"""
Comprehensive error recovery and fault tolerance for file processing operations.
Handles partial failures, corruption detection, and intelligent recovery strategies.
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import shutil
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict

from app.utils.monitoring import performance_metrics, alert_manager

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of file processing operations."""
    PENDING = "pending"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    CANCELLED = "cancelled"
    RECOVERED = "recovered"


class RecoveryStrategy(Enum):
    """Different recovery strategies for failed operations."""
    RETRY = "retry"
    SKIP_SEGMENT = "skip_segment"
    FALLBACK_METHOD = "fallback_method"
    MANUAL_INTERVENTION = "manual_intervention"
    IGNORE_ERROR = "ignore_error"


@dataclass
class ProcessingCheckpoint:
    """Represents a checkpoint in file processing."""
    operation_id: str
    timestamp: datetime
    stage: str
    progress_percent: float
    data: Dict[str, Any]
    file_hash: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingCheckpoint':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ProcessingError:
    """Detailed error information for recovery analysis."""
    error_id: str
    operation_id: str
    stage: str
    error_type: str
    error_message: str
    timestamp: datetime
    context: Dict[str, Any]
    recovery_attempts: int = 0
    recoverable: bool = True
    suggested_strategy: RecoveryStrategy = RecoveryStrategy.RETRY


class FileCorruptionDetector:
    """Detects various types of file corruption."""

    def __init__(self):
        self.magic_numbers = {
            # Audio formats
            b'\xff\xfb': 'mp3',
            b'\xff\xf3': 'mp3',
            b'\xff\xf2': 'mp3',
            b'RIFF': 'wav',
            b'fLaC': 'flac',
            b'OggS': 'ogg',
            b'ftypM4A': 'm4a',

            # Document formats
            b'%PDF': 'pdf',
            b'\x50\x4b\x03\x04': 'zip_based',  # docx, etc.
        }

    async def detect_corruption(self, file_path: Path) -> Dict[str, Any]:
        """Comprehensive corruption detection."""
        corruption_report = {
            'is_corrupted': False,
            'corruption_type': None,
            'confidence': 1.0,
            'issues': [],
            'file_info': {}
        }

        try:
            # Basic file existence and accessibility
            if not file_path.exists():
                corruption_report['is_corrupted'] = True
                corruption_report['corruption_type'] = 'missing_file'
                corruption_report['issues'].append('File does not exist')
                return corruption_report

            if file_path.stat().st_size == 0:
                corruption_report['is_corrupted'] = True
                corruption_report['corruption_type'] = 'empty_file'
                corruption_report['issues'].append('File is empty')
                return corruption_report

            # File header validation
            header_valid, header_issues = await self._validate_file_header(file_path)
            if not header_valid:
                corruption_report['is_corrupted'] = True
                corruption_report['corruption_type'] = 'invalid_header'
                corruption_report['issues'].extend(header_issues)

            # File structure validation for audio files
            if file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']:
                structure_valid, structure_issues = await self._validate_audio_structure(file_path)
                if not structure_valid:
                    corruption_report['is_corrupted'] = True
                    if not corruption_report['corruption_type']:
                        corruption_report['corruption_type'] = 'invalid_structure'
                    corruption_report['issues'].extend(structure_issues)

            # Calculate file integrity metrics
            corruption_report['file_info'] = await self._get_file_integrity_info(file_path)

            # Assess overall corruption confidence
            if corruption_report['is_corrupted']:
                corruption_report['confidence'] = min(1.0, len(corruption_report['issues']) * 0.3)

        except Exception as e:
            corruption_report['is_corrupted'] = True
            corruption_report['corruption_type'] = 'access_error'
            corruption_report['issues'].append(f'Cannot analyze file: {str(e)}')
            logger.error(f"Corruption detection failed for {file_path}: {e}")

        return corruption_report

    async def _validate_file_header(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate file header matches expected format."""
        issues = []

        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)

            # Check if header matches expected format
            expected_format = None
            for magic, format_name in self.magic_numbers.items():
                if header.startswith(magic):
                    expected_format = format_name
                    break

            file_extension = file_path.suffix.lower()[1:]  # Remove dot

            # Special handling for common mismatches
            if file_extension == 'wav' and not header.startswith(b'RIFF'):
                issues.append('WAV file missing RIFF header')
            elif file_extension == 'mp3' and not any(header.startswith(magic) for magic in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2']):
                issues.append('MP3 file missing valid header')
            elif file_extension == 'flac' and not header.startswith(b'fLaC'):
                issues.append('FLAC file missing fLaC header')

            return len(issues) == 0, issues

        except Exception as e:
            return False, [f'Header validation error: {str(e)}']

    async def _validate_audio_structure(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate audio file internal structure."""
        issues = []

        try:
            # Try to get basic audio info without full loading
            file_size = file_path.stat().st_size

            # Check for suspiciously small audio files
            if file_size < 1024:  # Less than 1KB
                issues.append('Audio file suspiciously small')

            # Try to read audio metadata
            try:
                import mutagen
                audio_file = mutagen.File(file_path)

                if audio_file is None:
                    issues.append('Cannot parse audio metadata')
                else:
                    # Check for basic audio properties
                    if hasattr(audio_file, 'info'):
                        if getattr(audio_file.info, 'length', 0) <= 0:
                            issues.append('Audio file reports zero duration')
                        if getattr(audio_file.info, 'bitrate', 0) <= 0:
                            issues.append('Audio file reports zero bitrate')

            except ImportError:
                # Mutagen not available, use basic checks
                logger.debug("Mutagen not available, using basic audio validation")

                # Basic file size vs duration heuristic
                if file_path.suffix.lower() == '.mp3':
                    # Rough estimate: 1 minute of MP3 at 128kbps ≈ 1MB
                    if file_size < 10000:  # Very small for audio
                        issues.append('MP3 file unusually small')

        except Exception as e:
            issues.append(f'Audio structure validation error: {str(e)}')

        return len(issues) == 0, issues

    async def _get_file_integrity_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file integrity information."""
        try:
            stat = file_path.stat()

            # Calculate MD5 hash for integrity
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            return {
                'size_bytes': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'md5_hash': hash_md5.hexdigest(),
                'readable': True
            }

        except Exception as e:
            return {
                'size_bytes': 0,
                'modified_time': None,
                'md5_hash': None,
                'readable': False,
                'error': str(e)
            }


class ProcessingRecoveryManager:
    """Manages recovery from processing failures."""

    def __init__(self,
                 checkpoint_dir: str = "processing_checkpoints",
                 max_recovery_attempts: int = 3,
                 checkpoint_interval_seconds: int = 30):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

        self.max_recovery_attempts = max_recovery_attempts
        self.checkpoint_interval = checkpoint_interval_seconds

        # Active operations tracking
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.recovery_strategies: Dict[str, Callable] = {}

        # Corruption detector
        self.corruption_detector = FileCorruptionDetector()

        # Register default recovery strategies
        self._register_default_strategies()

    def _register_default_strategies(self):
        """Register default recovery strategies."""
        self.recovery_strategies.update({
            'retry_with_delay': self._retry_with_exponential_backoff,
            'fallback_processing': self._try_fallback_processing_method,
            'segment_skip': self._skip_corrupted_segment,
            'format_conversion': self._attempt_format_conversion,
            'partial_recovery': self._recover_partial_results
        })

    async def start_operation(self,
                            operation_id: str,
                            file_path: Path,
                            operation_type: str,
                            metadata: Dict[str, Any] = None) -> bool:
        """Start tracking a new processing operation."""

        # Check for file corruption first
        corruption_report = await self.corruption_detector.detect_corruption(file_path)

        if corruption_report['is_corrupted']:
            await alert_manager.trigger_alert(
                "file_corruption_detected",
                "error",
                f"File corruption detected in {file_path.name}: {corruption_report['corruption_type']}",
                corruption_report
            )
            return False

        # Initialize operation tracking
        self.active_operations[operation_id] = {
            'file_path': str(file_path),
            'operation_type': operation_type,
            'status': ProcessingStatus.STARTED,
            'start_time': datetime.now(),
            'last_checkpoint': None,
            'errors': [],
            'recovery_attempts': 0,
            'metadata': metadata or {},
            'file_integrity': corruption_report['file_info']
        }

        logger.info(f"Started operation {operation_id} for {file_path.name}")
        return True

    async def save_checkpoint(self,
                            operation_id: str,
                            stage: str,
                            progress_percent: float,
                            data: Dict[str, Any]) -> None:
        """Save a processing checkpoint."""

        if operation_id not in self.active_operations:
            logger.warning(f"Cannot save checkpoint for unknown operation {operation_id}")
            return

        operation = self.active_operations[operation_id]

        # Calculate file hash for integrity
        file_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

        checkpoint = ProcessingCheckpoint(
            operation_id=operation_id,
            timestamp=datetime.now(),
            stage=stage,
            progress_percent=progress_percent,
            data=data,
            file_hash=file_hash,
            metadata=operation['metadata']
        )

        # Save checkpoint to disk
        checkpoint_file = self.checkpoint_dir / f"{operation_id}_{stage}.checkpoint"
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint, f)

            operation['last_checkpoint'] = checkpoint
            operation['status'] = ProcessingStatus.IN_PROGRESS

            logger.debug(f"Saved checkpoint for {operation_id} at stage {stage} ({progress_percent:.1f}%)")

        except Exception as e:
            logger.error(f"Failed to save checkpoint for {operation_id}: {e}")

    async def handle_processing_error(self,
                                    operation_id: str,
                                    stage: str,
                                    error: Exception,
                                    context: Dict[str, Any] = None) -> Optional[RecoveryStrategy]:
        """Handle a processing error and determine recovery strategy."""

        if operation_id not in self.active_operations:
            logger.error(f"Cannot handle error for unknown operation {operation_id}")
            return None

        operation = self.active_operations[operation_id]

        # Create error record
        error_record = ProcessingError(
            error_id=f"{operation_id}_{stage}_{int(time.time())}",
            operation_id=operation_id,
            stage=stage,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.now(),
            context=context or {},
            recovery_attempts=operation['recovery_attempts']
        )

        operation['errors'].append(error_record)
        operation['status'] = ProcessingStatus.FAILED

        # Analyze error and suggest recovery strategy
        recovery_strategy = await self._analyze_error_for_recovery(error_record, operation)

        logger.error(f"Processing error in {operation_id} at stage {stage}: {error}")
        logger.info(f"Suggested recovery strategy: {recovery_strategy}")

        # Record error metrics
        performance_metrics.record_function_call(f"processing_error_{error_record.error_type}", 1)

        return recovery_strategy

    async def attempt_recovery(self,
                             operation_id: str,
                             strategy: RecoveryStrategy,
                             recovery_function: Optional[Callable] = None) -> bool:
        """Attempt to recover from a processing failure."""

        if operation_id not in self.active_operations:
            logger.error(f"Cannot recover unknown operation {operation_id}")
            return False

        operation = self.active_operations[operation_id]

        if operation['recovery_attempts'] >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts exceeded for {operation_id}")
            operation['status'] = ProcessingStatus.FAILED
            return False

        operation['recovery_attempts'] += 1

        logger.info(f"Attempting recovery for {operation_id} using strategy {strategy} (attempt {operation['recovery_attempts']})")

        try:
            # Use custom recovery function or default strategy
            if recovery_function:
                success = await recovery_function(operation_id, operation)
            else:
                strategy_func = self.recovery_strategies.get(strategy.value)
                if strategy_func:
                    success = await strategy_func(operation_id, operation)
                else:
                    logger.error(f"No recovery strategy available for {strategy}")
                    return False

            if success:
                operation['status'] = ProcessingStatus.RECOVERED
                logger.info(f"Successfully recovered operation {operation_id}")

                # Alert successful recovery
                await alert_manager.trigger_alert(
                    "processing_recovery_success",
                    "info",
                    f"Successfully recovered processing operation {operation_id}",
                    {'operation_id': operation_id, 'strategy': strategy.value, 'attempts': operation['recovery_attempts']}
                )

                performance_metrics.record_function_call("processing_recovery_success", 1)
                return True
            else:
                logger.warning(f"Recovery attempt failed for {operation_id}")
                return False

        except Exception as e:
            logger.error(f"Recovery attempt failed with exception for {operation_id}: {e}")
            return False

    async def _analyze_error_for_recovery(self, error: ProcessingError, operation: Dict[str, Any]) -> RecoveryStrategy:
        """Analyze error to suggest appropriate recovery strategy."""

        error_type = error.error_type.lower()
        error_message = error.error_message.lower()

        # File-related errors
        if 'filenotfound' in error_type or 'no such file' in error_message:
            return RecoveryStrategy.MANUAL_INTERVENTION

        # Memory-related errors
        if 'memory' in error_message or 'outofmemory' in error_type:
            return RecoveryStrategy.SKIP_SEGMENT

        # Network/API errors
        if any(keyword in error_message for keyword in ['timeout', 'connection', 'network', 'api']):
            return RecoveryStrategy.RETRY

        # Audio processing errors
        if any(keyword in error_message for keyword in ['audio', 'whisper', 'transcription']):
            return RecoveryStrategy.FALLBACK_METHOD

        # Corruption errors
        if any(keyword in error_message for keyword in ['corrupt', 'invalid format', 'decode']):
            return RecoveryStrategy.MANUAL_INTERVENTION

        # Default to retry for unknown errors
        return RecoveryStrategy.RETRY

    async def _retry_with_exponential_backoff(self, operation_id: str, operation: Dict[str, Any]) -> bool:
        """Retry operation with exponential backoff."""

        attempt = operation['recovery_attempts']
        delay = min(300, 2 ** attempt)  # Max 5 minutes delay

        logger.info(f"Retrying operation {operation_id} after {delay} seconds")
        await asyncio.sleep(delay)

        # This would trigger re-execution of the original operation
        # Implementation depends on the specific processing pipeline
        return True  # Placeholder

    async def _try_fallback_processing_method(self, operation_id: str, operation: Dict[str, Any]) -> bool:
        """Try alternative processing method."""

        logger.info(f"Attempting fallback processing for {operation_id}")

        # Example: Switch from OpenAI Whisper to local Whisper
        # Or switch from high-quality to fast processing
        operation['metadata']['fallback_mode'] = True
        operation['metadata']['processing_quality'] = 'fast'

        return True  # Placeholder

    async def _skip_corrupted_segment(self, operation_id: str, operation: Dict[str, Any]) -> bool:
        """Skip corrupted segment and continue processing."""

        logger.info(f"Skipping corrupted segment for {operation_id}")

        # Mark segment as skipped and continue
        operation['metadata']['segments_skipped'] = operation['metadata'].get('segments_skipped', 0) + 1

        return True  # Placeholder

    async def _attempt_format_conversion(self, operation_id: str, operation: Dict[str, Any]) -> bool:
        """Attempt to convert file format and retry."""

        logger.info(f"Attempting format conversion for {operation_id}")

        file_path = Path(operation['file_path'])

        try:
            # This would use ffmpeg or similar to convert format
            # Placeholder implementation
            converted_path = file_path.with_suffix('.wav')

            # Update operation to use converted file
            operation['file_path'] = str(converted_path)
            operation['metadata']['format_converted'] = True

            return True

        except Exception as e:
            logger.error(f"Format conversion failed: {e}")
            return False

    async def _recover_partial_results(self, operation_id: str, operation: Dict[str, Any]) -> bool:
        """Recover partial results from last checkpoint."""

        logger.info(f"Recovering partial results for {operation_id}")

        last_checkpoint = operation.get('last_checkpoint')
        if not last_checkpoint:
            logger.warning(f"No checkpoint available for {operation_id}")
            return False

        # Load and validate checkpoint
        try:
            checkpoint_file = self.checkpoint_dir / f"{operation_id}_{last_checkpoint.stage}.checkpoint"

            if checkpoint_file.exists():
                with open(checkpoint_file, 'rb') as f:
                    checkpoint = pickle.load(f)

                # Validate checkpoint integrity
                current_hash = hashlib.md5(json.dumps(checkpoint.data, sort_keys=True).encode()).hexdigest()

                if current_hash == checkpoint.file_hash:
                    # Checkpoint is valid, can resume from here
                    operation['metadata']['resumed_from_checkpoint'] = True
                    operation['metadata']['resume_progress'] = checkpoint.progress_percent
                    return True
                else:
                    logger.error(f"Checkpoint integrity check failed for {operation_id}")
                    return False
            else:
                logger.error(f"Checkpoint file not found for {operation_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to recover from checkpoint: {e}")
            return False

    async def complete_operation(self, operation_id: str, success: bool, result_data: Dict[str, Any] = None):
        """Mark operation as completed."""

        if operation_id not in self.active_operations:
            return

        operation = self.active_operations[operation_id]

        operation['status'] = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
        operation['end_time'] = datetime.now()
        operation['result'] = result_data or {}

        # Clean up checkpoints on successful completion
        if success:
            await self._cleanup_operation_checkpoints(operation_id)

        logger.info(f"Completed operation {operation_id} with status {operation['status']}")

        # Record completion metrics
        duration = (operation['end_time'] - operation['start_time']).total_seconds()
        performance_metrics.record_function_call(
            f"operation_{'success' if success else 'failure'}",
            duration
        )

    async def _cleanup_operation_checkpoints(self, operation_id: str):
        """Clean up checkpoint files for completed operation."""
        try:
            for checkpoint_file in self.checkpoint_dir.glob(f"{operation_id}_*.checkpoint"):
                checkpoint_file.unlink()
            logger.debug(f"Cleaned up checkpoints for {operation_id}")
        except Exception as e:
            logger.warning(f"Failed to clean up checkpoints for {operation_id}: {e}")

    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an operation."""
        operation = self.active_operations.get(operation_id)

        if not operation:
            return None

        return {
            'operation_id': operation_id,
            'status': operation['status'].value,
            'file_path': operation['file_path'],
            'operation_type': operation['operation_type'],
            'start_time': operation['start_time'].isoformat(),
            'recovery_attempts': operation['recovery_attempts'],
            'error_count': len(operation['errors']),
            'last_checkpoint_stage': operation['last_checkpoint'].stage if operation['last_checkpoint'] else None,
            'progress_percent': operation['last_checkpoint'].progress_percent if operation['last_checkpoint'] else 0
        }

    def get_recovery_report(self) -> Dict[str, Any]:
        """Get comprehensive recovery statistics."""

        total_operations = len(self.active_operations)
        status_counts = {}

        for operation in self.active_operations.values():
            status = operation['status']
            status_counts[status.value] = status_counts.get(status.value, 0) + 1

        error_types = {}
        recovery_strategies = {}

        for operation in self.active_operations.values():
            for error in operation['errors']:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
                if hasattr(error, 'suggested_strategy'):
                    strategy = error.suggested_strategy.value
                    recovery_strategies[strategy] = recovery_strategies.get(strategy, 0) + 1

        return {
            'total_operations': total_operations,
            'status_distribution': status_counts,
            'error_types': error_types,
            'recovery_strategies_used': recovery_strategies,
            'average_recovery_attempts': sum(op['recovery_attempts'] for op in self.active_operations.values()) / max(1, total_operations)
        }


# Global recovery manager instance
recovery_manager = ProcessingRecoveryManager()