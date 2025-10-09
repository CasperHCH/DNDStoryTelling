"""
Production Systems Integration Module.
Provides unified interface for all production-ready features and coordinates system operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Import all our production systems
from app.utils.storage_manager import storage_manager, file_lifecycle_manager
from app.utils.speaker_identification import speaker_identifier, dnd_processor
from app.utils.error_recovery import recovery_manager, ProcessingStatus, RecoveryStrategy
from app.utils.ai_cost_tracker import usage_tracker, AIService, UsageType
from app.utils.audio_quality import audio_analyzer, audio_preprocessor
from app.utils.monitoring import performance_metrics, alert_manager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfiguration:
    """Configuration for audio processing operations."""

    # Quality settings
    min_quality_score: float = 0.6
    auto_preprocessing: bool = True
    optimize_for_transcription: bool = True

    # Cost controls
    max_cost_per_file: float = 5.00
    check_quotas_before_processing: bool = True

    # Storage settings
    cleanup_temp_files: bool = True
    preserve_original: bool = True

    # Error handling
    max_recovery_attempts: int = 3
    enable_checkpoints: bool = True

    # Speaker identification
    enable_speaker_identification: bool = True
    dnd_character_mapping: bool = True


@dataclass
class ProcessingResult:
    """Comprehensive processing result."""

    operation_id: str
    success: bool
    file_path: Path
    processed_file_path: Optional[Path]

    # Quality metrics
    original_quality: Optional[Dict[str, Any]]
    final_quality: Optional[Dict[str, Any]]

    # Processing details
    transcription_result: Optional[Dict[str, Any]]
    speaker_analysis: Optional[Dict[str, Any]]
    story_result: Optional[Dict[str, Any]]

    # System metrics
    processing_time_seconds: float
    total_cost: float
    storage_used_mb: float

    # Error information
    errors: List[str]
    warnings: List[str]
    recovery_actions: List[str]


class DNDProductionProcessor:
    """Main production processor coordinating all systems."""

    def __init__(self, config: Optional[ProcessingConfiguration] = None):
        self.config = config or ProcessingConfiguration()

        # Initialize system health tracking
        self.system_health = {
            'storage_manager': True,
            'speaker_identifier': True,
            'error_recovery': True,
            'ai_cost_tracker': True,
            'audio_analyzer': True
        }

        logger.info("Production processor initialized with full system integration")

    async def process_dnd_session(self,
                                file_path: Path,
                                user_id: str,
                                session_metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """Process a complete D&D session with full production pipeline."""

        operation_id = f"dnd_session_{user_id}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()

        logger.info(f"Starting D&D session processing: {operation_id}")

        # Initialize result tracking
        result = ProcessingResult(
            operation_id=operation_id,
            success=False,
            file_path=file_path,
            processed_file_path=None,
            original_quality=None,
            final_quality=None,
            transcription_result=None,
            speaker_analysis=None,
            story_result=None,
            processing_time_seconds=0,
            total_cost=0,
            storage_used_mb=0,
            errors=[],
            warnings=[],
            recovery_actions=[]
        )

        try:
            # Step 1: Pre-processing validation
            logger.info(f"Step 1: Pre-processing validation for {operation_id}")

            validation_success = await self._pre_processing_validation(
                file_path, user_id, operation_id, result
            )

            if not validation_success:
                return result

            # Step 2: Audio quality analysis and preprocessing
            logger.info(f"Step 2: Audio quality analysis for {operation_id}")

            processed_file, quality_metrics = await self._handle_audio_quality(
                file_path, operation_id, result
            )

            # Step 3: Speaker identification and analysis
            logger.info(f"Step 3: Speaker identification for {operation_id}")

            speaker_results = await self._handle_speaker_identification(
                processed_file, operation_id, result, session_metadata
            )

            # Step 4: Transcription with cost tracking
            logger.info(f"Step 4: Transcription processing for {operation_id}")

            transcription_results = await self._handle_transcription(
                processed_file, speaker_results, operation_id, result
            )

            # Step 5: Story generation
            logger.info(f"Step 5: Story generation for {operation_id}")

            story_results = await self._handle_story_generation(
                transcription_results, speaker_results, operation_id, result
            )

            # Step 6: Post-processing and cleanup
            logger.info(f"Step 6: Post-processing cleanup for {operation_id}")

            await self._post_processing_cleanup(
                processed_file, operation_id, result
            )

            # Mark as successful
            result.success = True
            await recovery_manager.complete_operation(operation_id, True, {
                'transcription': transcription_results,
                'speakers': speaker_results,
                'story': story_results
            })

        except Exception as e:
            logger.error(f"Processing failed for {operation_id}: {e}")
            result.errors.append(str(e))

            # Attempt error recovery
            await self._handle_processing_error(operation_id, e, result)

        finally:
            # Calculate final metrics
            end_time = datetime.now()
            result.processing_time_seconds = (end_time - start_time).total_seconds()

            # Get storage usage
            result.storage_used_mb = await self._calculate_storage_usage(operation_id)

            logger.info(f"Processing completed for {operation_id}: {'SUCCESS' if result.success else 'FAILED'}")

            # Record comprehensive metrics
            await self._record_final_metrics(result)

        return result

    async def _pre_processing_validation(self,
                                       file_path: Path,
                                       user_id: str,
                                       operation_id: str,
                                       result: ProcessingResult) -> bool:
        """Comprehensive pre-processing validation."""

        try:
            # Check file existence and accessibility
            if not file_path.exists():
                result.errors.append("File does not exist")
                return False

            if file_path.stat().st_size == 0:
                result.errors.append("File is empty")
                return False

            # Storage validation
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            if not storage_manager.check_upload_allowed(user_id, file_size_mb):
                result.errors.append("Storage quota exceeded")
                return False

            # Start operation tracking
            if not await recovery_manager.start_operation(
                operation_id, file_path, "dnd_session_processing",
                {"user_id": user_id, "file_size_mb": file_size_mb}
            ):
                result.errors.append("Failed to initialize error recovery")
                return False

            # Check cost quotas if enabled
            if self.config.check_quotas_before_processing:
                # Estimate processing costs
                estimated_audio_minutes = await self._estimate_audio_duration(file_path)

                # Check Whisper quota
                whisper_cost, whisper_allowed = await usage_tracker.estimate_cost(
                    AIService.OPENAI_WHISPER,
                    UsageType.AUDIO_MINUTES,
                    estimated_audio_minutes
                )

                if not whisper_allowed:
                    result.errors.append("Transcription would exceed cost quotas")
                    return False

                # Estimate GPT usage for story generation (rough estimate)
                estimated_tokens = estimated_audio_minutes * 1000  # Rough estimate
                gpt_cost, gpt_allowed = await usage_tracker.estimate_cost(
                    AIService.OPENAI_GPT,
                    UsageType.INPUT_TOKENS,
                    estimated_tokens
                )

                if not gpt_allowed or (whisper_cost + gpt_cost) > self.config.max_cost_per_file:
                    result.errors.append(f"Processing would exceed cost limits: ${whisper_cost + gpt_cost:.2f}")
                    return False

                logger.info(f"Estimated processing cost: ${whisper_cost + gpt_cost:.2f}")

            # Register file with lifecycle manager
            await file_lifecycle_manager.register_upload(user_id, file_path, {
                'operation_id': operation_id,
                'processing_type': 'dnd_session'
            })

            return True

        except Exception as e:
            result.errors.append(f"Pre-processing validation failed: {str(e)}")
            return False

    async def _handle_audio_quality(self,
                                  file_path: Path,
                                  operation_id: str,
                                  result: ProcessingResult) -> Tuple[Path, Dict[str, Any]]:
        """Handle audio quality analysis and preprocessing."""

        try:
            # Analyze original quality
            original_metrics = await audio_analyzer.analyze_audio_quality(file_path)
            result.original_quality = original_metrics.to_dict()

            # Save checkpoint
            await recovery_manager.save_checkpoint(
                operation_id, "audio_analysis", 25.0,
                {"original_quality": result.original_quality}
            )

            # Check if preprocessing is needed
            if (original_metrics.quality_score < self.config.min_quality_score and
                self.config.auto_preprocessing):

                logger.info(f"Audio quality below threshold ({original_metrics.quality_score:.2f}), applying preprocessing")

                if self.config.optimize_for_transcription:
                    processed_file, final_metrics = await audio_preprocessor.optimize_for_transcription(file_path)
                else:
                    # Suggest and apply general improvements
                    actions = await audio_preprocessor.suggest_preprocessing_actions(original_metrics)
                    processed_file, success = await audio_preprocessor.apply_preprocessing(file_path, actions)

                    if success:
                        final_metrics = await audio_analyzer.analyze_audio_quality(processed_file)
                    else:
                        processed_file = file_path
                        final_metrics = original_metrics
                        result.warnings.append("Audio preprocessing failed, using original file")

                result.processed_file_path = processed_file
                result.final_quality = final_metrics.to_dict()

                logger.info(f"Audio preprocessing complete. Quality improved from {original_metrics.quality_score:.2f} to {final_metrics.quality_score:.2f}")

            else:
                processed_file = file_path
                result.final_quality = result.original_quality
                logger.info("Audio quality acceptable, no preprocessing needed")

            # Save preprocessing checkpoint
            await recovery_manager.save_checkpoint(
                operation_id, "audio_preprocessing", 35.0,
                {"processed_file": str(processed_file), "final_quality": result.final_quality}
            )

            return processed_file, result.final_quality

        except Exception as e:
            logger.error(f"Audio quality handling failed: {e}")
            result.warnings.append(f"Audio quality processing failed: {str(e)}")
            return file_path, {}

    async def _handle_speaker_identification(self,
                                           file_path: Path,
                                           operation_id: str,
                                           result: ProcessingResult,
                                           session_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle speaker identification and D&D character mapping."""

        try:
            if not self.config.enable_speaker_identification:
                return {}

            logger.info("Performing speaker identification analysis")

            # Basic speaker identification
            speakers = await speaker_identifier.identify_speakers(str(file_path))

            # D&D-specific processing if enabled
            if self.config.dnd_character_mapping and session_metadata:
                character_names = session_metadata.get('characters', [])
                if character_names:
                    # Map speakers to D&D characters
                    speaker_mapping = await dnd_processor.map_speakers_to_characters(
                        speakers, character_names
                    )
                    speakers = speaker_mapping

            # Process with D&D enhancements
            enhanced_transcription = await dnd_processor.process_dnd_transcription(
                speakers, session_metadata or {}
            )

            speaker_results = {
                'speakers': [speaker.to_dict() for speaker in speakers],
                'enhanced_transcription': enhanced_transcription,
                'character_count': len(speakers),
                'total_speech_time': sum(speaker.total_duration for speaker in speakers)
            }

            result.speaker_analysis = speaker_results

            # Save checkpoint
            await recovery_manager.save_checkpoint(
                operation_id, "speaker_identification", 50.0,
                {"speaker_results": speaker_results}
            )

            logger.info(f"Speaker identification complete. Found {len(speakers)} speakers")

            return speaker_results

        except Exception as e:
            logger.error(f"Speaker identification failed: {e}")
            result.warnings.append(f"Speaker identification failed: {str(e)}")
            return {}

    async def _handle_transcription(self,
                                  file_path: Path,
                                  speaker_results: Dict[str, Any],
                                  operation_id: str,
                                  result: ProcessingResult) -> Dict[str, Any]:
        """Handle audio transcription with cost tracking."""

        try:
            logger.info("Starting audio transcription")

            # Get audio duration for cost calculation
            audio_duration = await self._estimate_audio_duration(file_path)

            # Record usage before API call
            transcription_cost = await usage_tracker.record_usage(
                AIService.OPENAI_WHISPER,
                UsageType.AUDIO_MINUTES,
                audio_duration,
                model_name="whisper-1",
                operation_id=operation_id,
                metadata={"file_path": str(file_path)}
            )

            result.total_cost += float(transcription_cost)

            # TODO: Replace with actual Whisper API call
            # This is a placeholder for the actual transcription logic
            transcription_result = {
                'text': 'Placeholder transcription text...',
                'segments': [],
                'language': 'en',
                'duration': audio_duration,
                'confidence': 0.95
            }

            # Enhance with speaker information
            if speaker_results and 'speakers' in speaker_results:
                # TODO: Merge speaker timeline with transcription segments
                transcription_result['speaker_segments'] = speaker_results['enhanced_transcription']

            result.transcription_result = transcription_result

            # Save checkpoint
            await recovery_manager.save_checkpoint(
                operation_id, "transcription", 70.0,
                {"transcription_result": transcription_result, "cost": float(transcription_cost)}
            )

            logger.info(f"Transcription complete. Cost: ${transcription_cost:.4f}")

            return transcription_result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            result.errors.append(f"Transcription failed: {str(e)}")

            # Attempt recovery
            recovery_strategy = await recovery_manager.handle_processing_error(
                operation_id, "transcription", e, {"file_path": str(file_path)}
            )

            if recovery_strategy:
                result.recovery_actions.append(f"Suggested recovery: {recovery_strategy.value}")

            return {}

    async def _handle_story_generation(self,
                                     transcription_results: Dict[str, Any],
                                     speaker_results: Dict[str, Any],
                                     operation_id: str,
                                     result: ProcessingResult) -> Dict[str, Any]:
        """Handle story generation from transcription."""

        try:
            if not transcription_results:
                result.warnings.append("No transcription available for story generation")
                return {}

            logger.info("Starting story generation")

            # Prepare input for story generation
            story_input = {
                'transcription': transcription_results.get('text', ''),
                'speakers': speaker_results.get('speakers', []),
                'session_duration': transcription_results.get('duration', 0),
                'character_interactions': speaker_results.get('enhanced_transcription', {})
            }

            # Estimate token usage for cost tracking
            estimated_input_tokens = len(story_input['transcription']) // 4  # Rough estimate
            estimated_output_tokens = estimated_input_tokens // 2  # Assume compression

            # Record input token usage
            input_cost = await usage_tracker.record_usage(
                AIService.OPENAI_GPT,
                UsageType.INPUT_TOKENS,
                estimated_input_tokens,
                model_name="gpt-4",
                operation_id=operation_id,
                metadata={"stage": "story_generation_input"}
            )

            # TODO: Replace with actual GPT API call for story generation
            # This is a placeholder for the actual story generation logic
            story_result = {
                'narrative': 'Generated D&D story narrative...',
                'key_events': [],
                'character_developments': {},
                'session_summary': 'Brief session summary...',
                'generated_at': datetime.now().isoformat()
            }

            # Record output token usage
            output_cost = await usage_tracker.record_usage(
                AIService.OPENAI_GPT,
                UsageType.OUTPUT_TOKENS,
                estimated_output_tokens,
                model_name="gpt-4",
                operation_id=operation_id,
                metadata={"stage": "story_generation_output"}
            )

            result.total_cost += float(input_cost + output_cost)
            result.story_result = story_result

            # Save checkpoint
            await recovery_manager.save_checkpoint(
                operation_id, "story_generation", 90.0,
                {"story_result": story_result, "total_cost": result.total_cost}
            )

            logger.info(f"Story generation complete. Total cost: ${input_cost + output_cost:.4f}")

            return story_result

        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            result.errors.append(f"Story generation failed: {str(e)}")

            # Attempt recovery
            recovery_strategy = await recovery_manager.handle_processing_error(
                operation_id, "story_generation", e, {"transcription_length": len(transcription_results.get('text', ''))}
            )

            if recovery_strategy:
                result.recovery_actions.append(f"Suggested recovery: {recovery_strategy.value}")

            return {}

    async def _post_processing_cleanup(self,
                                     processed_file: Path,
                                     operation_id: str,
                                     result: ProcessingResult):
        """Handle post-processing cleanup and file management."""

        try:
            # Clean up temporary files if configured
            if self.config.cleanup_temp_files and processed_file != result.file_path:
                # Keep processed file for now, clean up later via storage manager
                pass

            # Update file lifecycle status
            await file_lifecycle_manager.update_processing_status(
                str(result.file_path),
                "completed" if result.success else "failed",
                {
                    'operation_id': operation_id,
                    'processing_time': result.processing_time_seconds,
                    'total_cost': result.total_cost
                }
            )

            # Trigger storage cleanup if needed
            await storage_manager.cleanup_old_files()

            # Clean up audio preprocessing temp files
            audio_preprocessor.cleanup_temp_files()

            # Save final checkpoint
            await recovery_manager.save_checkpoint(
                operation_id, "post_processing", 100.0,
                {"cleanup_completed": True, "final_result": "success" if result.success else "failed"}
            )

            logger.info("Post-processing cleanup completed")

        except Exception as e:
            logger.warning(f"Post-processing cleanup had issues: {e}")
            result.warnings.append(f"Cleanup issues: {str(e)}")

    async def _handle_processing_error(self,
                                     operation_id: str,
                                     error: Exception,
                                     result: ProcessingResult):
        """Handle processing errors with recovery attempts."""

        try:
            # Determine recovery strategy
            recovery_strategy = await recovery_manager.handle_processing_error(
                operation_id, "processing", error, {"result": result.to_dict()}
            )

            if recovery_strategy and recovery_strategy != RecoveryStrategy.MANUAL_INTERVENTION:
                # Attempt recovery
                recovery_success = await recovery_manager.attempt_recovery(
                    operation_id, recovery_strategy
                )

                if recovery_success:
                    result.recovery_actions.append(f"Successfully recovered using {recovery_strategy.value}")
                    logger.info(f"Recovery successful for {operation_id}")
                else:
                    result.recovery_actions.append(f"Recovery attempt failed: {recovery_strategy.value}")
                    logger.error(f"Recovery failed for {operation_id}")

            # Mark operation as failed
            await recovery_manager.complete_operation(operation_id, False, {
                'error': str(error),
                'recovery_attempted': len(result.recovery_actions) > 0
            })

        except Exception as recovery_error:
            logger.error(f"Error recovery handling failed: {recovery_error}")

    async def _estimate_audio_duration(self, file_path: Path) -> float:
        """Estimate audio duration in minutes."""

        try:
            # Use ffprobe to get exact duration
            import subprocess
            import json

            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                duration_seconds = float(probe_data['format']['duration'])
                return duration_seconds / 60.0  # Convert to minutes
            else:
                # Fallback estimate based on file size
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                # Rough estimate: 1MB ≈ 1 minute for compressed audio
                return file_size_mb

        except Exception as e:
            logger.warning(f"Could not estimate audio duration: {e}")
            # Very rough fallback
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            return file_size_mb

    async def _calculate_storage_usage(self, operation_id: str) -> float:
        """Calculate total storage usage for operation."""

        try:
            # Get storage report
            storage_report = await storage_manager.get_storage_report()

            # This is a simplified calculation - in practice you'd track
            # files associated with this specific operation
            return storage_report.get('recent_uploads_mb', 0)

        except Exception as e:
            logger.warning(f"Could not calculate storage usage: {e}")
            return 0.0

    async def _record_final_metrics(self, result: ProcessingResult):
        """Record comprehensive metrics for monitoring."""

        try:
            # Performance metrics
            performance_metrics.record_function_call(
                "dnd_session_processing_complete",
                result.processing_time_seconds
            )

            performance_metrics.record_function_call(
                f"processing_result_{'success' if result.success else 'failure'}",
                1
            )

            if result.total_cost > 0:
                performance_metrics.record_function_call("processing_cost", result.total_cost)

            # Quality metrics
            if result.original_quality:
                performance_metrics.record_function_call(
                    "original_audio_quality",
                    result.original_quality.get('quality_score', 0)
                )

            if result.final_quality:
                performance_metrics.record_function_call(
                    "final_audio_quality",
                    result.final_quality.get('quality_score', 0)
                )

            # Alert on failures or high costs
            if not result.success:
                await alert_manager.trigger_alert(
                    "processing_failure",
                    "error",
                    f"D&D session processing failed: {result.operation_id}",
                    {"errors": result.errors, "warnings": result.warnings}
                )

            if result.total_cost > 10.0:  # Alert on high costs
                await alert_manager.trigger_alert(
                    "high_processing_cost",
                    "warning",
                    f"High processing cost: ${result.total_cost:.2f} for {result.operation_id}",
                    {"cost": result.total_cost, "operation_id": result.operation_id}
                )

        except Exception as e:
            logger.error(f"Failed to record final metrics: {e}")

    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""

        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'systems': {}
        }

        try:
            # Storage system health
            storage_report = await storage_manager.get_storage_report()
            health_report['systems']['storage'] = {
                'status': 'healthy' if storage_report['available_space_gb'] > 1 else 'warning',
                'available_space_gb': storage_report['available_space_gb'],
                'usage_percent': storage_report['usage_percent']
            }

            # Error recovery system health
            recovery_report = recovery_manager.get_recovery_report()
            health_report['systems']['error_recovery'] = {
                'status': 'healthy' if recovery_report['total_operations'] < 100 else 'warning',
                'active_operations': recovery_report['total_operations'],
                'average_recovery_attempts': recovery_report['average_recovery_attempts']
            }

            # AI usage system health
            usage_summary = usage_tracker.get_usage_summary(24)
            quota_status = usage_tracker.get_quota_status()

            quota_warnings = sum(1 for status in quota_status.values() if status['status'] == 'warning')

            health_report['systems']['ai_usage'] = {
                'status': 'healthy' if quota_warnings == 0 else 'warning',
                'daily_cost': usage_summary['total_cost'],
                'quota_warnings': quota_warnings
            }

            # Overall status determination
            system_statuses = [system['status'] for system in health_report['systems'].values()]
            if 'error' in system_statuses:
                health_report['overall_status'] = 'error'
            elif 'warning' in system_statuses:
                health_report['overall_status'] = 'warning'

        except Exception as e:
            logger.error(f"System health check failed: {e}")
            health_report['overall_status'] = 'error'
            health_report['error'] = str(e)

        return health_report

    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Run system optimization tasks."""

        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': [],
            'recommendations': []
        }

        try:
            # Clean up old files
            cleanup_result = await storage_manager.cleanup_old_files()
            if cleanup_result.get('files_deleted', 0) > 0:
                optimization_report['actions_taken'].append(
                    f"Cleaned up {cleanup_result['files_deleted']} old files, "
                    f"freed {cleanup_result['space_freed_gb']:.2f}GB"
                )

            # Clean up old usage records
            usage_tracker.cleanup_old_records()
            optimization_report['actions_taken'].append("Cleaned up old usage tracking records")

            # Clean up audio preprocessing temp files
            audio_preprocessor.cleanup_temp_files()
            optimization_report['actions_taken'].append("Cleaned up audio preprocessing temp files")

            # Check for system recommendations
            storage_report = await storage_manager.get_storage_report()

            if storage_report['usage_percent'] > 80:
                optimization_report['recommendations'].append(
                    "Storage usage high, consider increasing cleanup frequency"
                )

            quota_status = usage_tracker.get_quota_status()
            high_usage_quotas = [
                quota_id for quota_id, status in quota_status.items()
                if status['cost_percent'] > 70
            ]

            if high_usage_quotas:
                optimization_report['recommendations'].append(
                    f"High AI usage detected in quotas: {', '.join(high_usage_quotas)}"
                )

        except Exception as e:
            logger.error(f"System optimization failed: {e}")
            optimization_report['error'] = str(e)

        return optimization_report


# Global production processor instance
production_processor = DNDProductionProcessor()


# Convenience functions for common operations
async def process_dnd_audio_file(file_path: str,
                               user_id: str,
                               session_metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
    """Convenience function to process a D&D audio file with full production pipeline."""
    return await production_processor.process_dnd_session(
        Path(file_path), user_id, session_metadata
    )


async def get_production_system_status() -> Dict[str, Any]:
    """Get comprehensive production system status."""
    return await production_processor.get_system_health()


async def optimize_production_systems() -> Dict[str, Any]:
    """Run production system optimization."""
    return await production_processor.optimize_system_performance()