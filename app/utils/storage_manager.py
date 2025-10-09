"""
Advanced file lifecycle management and storage optimization.
Handles disk space monitoring, automatic cleanup, and storage quotas.
"""

import asyncio
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import psutil
import logging

from app.utils.monitoring import performance_metrics, alert_manager

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage lifecycle, cleanup, and disk space monitoring."""

    def __init__(self,
                 upload_dir: str = "uploads",
                 temp_dir: str = "temp",
                 max_disk_usage_percent: float = 85.0,
                 cleanup_age_hours: int = 24,
                 user_quota_gb: float = 5.0):
        self.upload_dir = Path(upload_dir)
        self.temp_dir = Path(temp_dir)
        self.max_disk_usage_percent = max_disk_usage_percent
        self.cleanup_age_hours = cleanup_age_hours
        self.user_quota_gb = user_quota_gb

        # Ensure directories exist
        self.upload_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)

        # Storage tracking
        self.user_storage_usage = {}
        self.cleanup_stats = {
            'last_cleanup': None,
            'files_cleaned': 0,
            'space_freed_mb': 0,
            'cleanup_errors': []
        }

    def get_disk_usage(self) -> Dict[str, float]:
        """Get current disk usage statistics."""
        try:
            usage = psutil.disk_usage(str(self.upload_dir))
            return {
                'total_gb': usage.total / (1024**3),
                'used_gb': usage.used / (1024**3),
                'free_gb': usage.free / (1024**3),
                'used_percent': (usage.used / usage.total) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'used_percent': 100}

    def is_disk_space_critical(self) -> bool:
        """Check if disk space is critically low."""
        usage = self.get_disk_usage()
        return usage['used_percent'] > self.max_disk_usage_percent

    async def check_user_quota(self, user_id: str) -> Dict[str, float]:
        """Check storage usage for a specific user."""
        user_dir = self.upload_dir / f"user_{user_id}"
        if not user_dir.exists():
            return {'used_gb': 0, 'quota_gb': self.user_quota_gb, 'remaining_gb': self.user_quota_gb}

        try:
            total_size = sum(f.stat().st_size for f in user_dir.rglob('*') if f.is_file())
            used_gb = total_size / (1024**3)

            self.user_storage_usage[user_id] = used_gb

            return {
                'used_gb': used_gb,
                'quota_gb': self.user_quota_gb,
                'remaining_gb': max(0, self.user_quota_gb - used_gb)
            }
        except Exception as e:
            logger.error(f"Failed to calculate user quota for {user_id}: {e}")
            return {'used_gb': 0, 'quota_gb': self.user_quota_gb, 'remaining_gb': 0}

    async def can_upload_file(self, user_id: str, file_size_bytes: int) -> Tuple[bool, str]:
        """Check if user can upload a file of given size."""
        # Check disk space
        if self.is_disk_space_critical():
            return False, "System disk space critically low. Please try again later."

        # Check user quota
        quota_info = await self.check_user_quota(user_id)
        file_size_gb = file_size_bytes / (1024**3)

        if file_size_gb > quota_info['remaining_gb']:
            return False, f"Upload would exceed your storage quota. Available: {quota_info['remaining_gb']:.2f}GB, Required: {file_size_gb:.2f}GB"

        return True, "Upload allowed"

    async def cleanup_old_files(self, force: bool = False) -> Dict[str, int]:
        """Clean up old files to free disk space."""
        if not force and not self.is_disk_space_critical():
            return {'files_cleaned': 0, 'space_freed_mb': 0}

        cleanup_stats = {'files_cleaned': 0, 'space_freed_mb': 0, 'errors': []}
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_age_hours)

        # Clean temp files first (most aggressive)
        await self._cleanup_directory(self.temp_dir, cutoff_time, cleanup_stats, hours=1)

        # Clean old upload files if still needed
        if self.is_disk_space_critical():
            await self._cleanup_directory(self.upload_dir, cutoff_time, cleanup_stats)

        # Clean orphaned processed files
        await self._cleanup_orphaned_files(cleanup_stats)

        # Update global stats
        self.cleanup_stats.update({
            'last_cleanup': datetime.now(),
            'files_cleaned': cleanup_stats['files_cleaned'],
            'space_freed_mb': cleanup_stats['space_freed_mb'],
            'cleanup_errors': cleanup_stats['errors']
        })

        if cleanup_stats['files_cleaned'] > 0:
            await alert_manager.trigger_alert(
                "storage_cleanup",
                "info",
                f"Cleaned up {cleanup_stats['files_cleaned']} files, freed {cleanup_stats['space_freed_mb']:.1f}MB",
                cleanup_stats
            )

        performance_metrics.record_function_call("storage_cleanup", cleanup_stats['files_cleaned'])
        return cleanup_stats

    async def _cleanup_directory(self, directory: Path, cutoff_time: datetime, stats: Dict, hours: int = None) -> None:
        """Clean up files in a specific directory."""
        if not directory.exists():
            return

        # Use different cutoff for different directories
        local_cutoff = cutoff_time
        if hours:
            local_cutoff = datetime.now() - timedelta(hours=hours)

        try:
            for file_path in directory.rglob('*'):
                if not file_path.is_file():
                    continue

                try:
                    # Get file modification time
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_time < local_cutoff:
                        # Check if file is not in use
                        if not self._is_file_in_use(file_path):
                            file_size = file_path.stat().st_size
                            file_path.unlink()

                            stats['files_cleaned'] += 1
                            stats['space_freed_mb'] += file_size / (1024**2)

                            logger.info(f"Cleaned up old file: {file_path}")

                except Exception as e:
                    error_msg = f"Failed to clean file {file_path}: {e}"
                    stats['errors'].append(error_msg)
                    logger.warning(error_msg)

        except Exception as e:
            error_msg = f"Failed to scan directory {directory}: {e}"
            stats['errors'].append(error_msg)
            logger.error(error_msg)

    async def _cleanup_orphaned_files(self, stats: Dict) -> None:
        """Clean up files that are no longer referenced in database."""
        try:
            # This would need database integration to check for orphaned files
            # For now, we'll clean files with specific patterns that indicate processing artifacts

            patterns_to_clean = [
                "temp_*",
                "*.tmp",
                "converted_*",
                "processed_*"
            ]

            for pattern in patterns_to_clean:
                for file_path in self.upload_dir.glob(pattern):
                    if file_path.is_file():
                        try:
                            # Check if file is old enough and not in use
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if (datetime.now() - file_time).total_seconds() > 3600:  # 1 hour old
                                if not self._is_file_in_use(file_path):
                                    file_size = file_path.stat().st_size
                                    file_path.unlink()

                                    stats['files_cleaned'] += 1
                                    stats['space_freed_mb'] += file_size / (1024**2)

                        except Exception as e:
                            stats['errors'].append(f"Failed to clean orphaned file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to clean orphaned files: {e}")

    def _is_file_in_use(self, file_path: Path) -> bool:
        """Check if a file is currently being used by another process."""
        try:
            # Try to open file for writing to check if it's locked
            with open(file_path, 'a'):
                return False
        except IOError:
            return True

    async def get_storage_report(self) -> Dict:
        """Generate comprehensive storage usage report."""
        disk_usage = self.get_disk_usage()

        # Calculate directory sizes
        upload_size = self._get_directory_size(self.upload_dir)
        temp_size = self._get_directory_size(self.temp_dir)

        # Get largest files
        largest_files = self._get_largest_files(self.upload_dir, limit=10)

        # Get user storage breakdown
        user_storage = {}
        for user_id in self.user_storage_usage:
            quota_info = await self.check_user_quota(user_id)
            user_storage[user_id] = quota_info

        return {
            'disk_usage': disk_usage,
            'directory_sizes': {
                'uploads_mb': upload_size / (1024**2),
                'temp_mb': temp_size / (1024**2)
            },
            'largest_files': largest_files,
            'user_storage': user_storage,
            'cleanup_stats': self.cleanup_stats,
            'storage_health': 'critical' if disk_usage['used_percent'] > self.max_disk_usage_percent else 'healthy',
            'recommendations': self._get_storage_recommendations(disk_usage)
        }

    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory."""
        try:
            return sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
        except Exception:
            return 0

    def _get_largest_files(self, directory: Path, limit: int = 10) -> List[Dict]:
        """Get the largest files in directory."""
        try:
            files_with_size = []
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    files_with_size.append({
                        'path': str(file_path.relative_to(directory)),
                        'size_mb': size / (1024**2),
                        'modified': modified.isoformat()
                    })

            # Sort by size and return top N
            files_with_size.sort(key=lambda x: x['size_mb'], reverse=True)
            return files_with_size[:limit]

        except Exception as e:
            logger.error(f"Failed to get largest files: {e}")
            return []

    def _get_storage_recommendations(self, disk_usage: Dict) -> List[str]:
        """Generate storage optimization recommendations."""
        recommendations = []

        if disk_usage['used_percent'] > 90:
            recommendations.append("Critical: Immediately clean up old files")
        elif disk_usage['used_percent'] > 80:
            recommendations.append("Warning: Consider cleaning up old files")

        if disk_usage['free_gb'] < 1:
            recommendations.append("Less than 1GB free space remaining")

        if len(self.cleanup_stats.get('cleanup_errors', [])) > 0:
            recommendations.append("Review cleanup errors in logs")

        return recommendations


class FileLifecycleManager:
    """Manages the complete lifecycle of uploaded files."""

    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.processing_files = set()  # Track files currently being processed

    async def register_file_upload(self, user_id: str, filename: str, file_size: int) -> str:
        """Register a new file upload and return unique file ID."""
        # Check if upload is allowed
        can_upload, message = await self.storage_manager.can_upload_file(user_id, file_size)
        if not can_upload:
            raise ValueError(message)

        # Generate unique file ID
        file_id = f"{user_id}_{int(time.time())}_{filename}"

        # Create user directory if needed
        user_dir = self.storage_manager.upload_dir / f"user_{user_id}"
        user_dir.mkdir(exist_ok=True)

        return file_id

    async def mark_processing_start(self, file_id: str):
        """Mark file as currently being processed."""
        self.processing_files.add(file_id)

    async def mark_processing_complete(self, file_id: str, success: bool):
        """Mark file processing as complete."""
        self.processing_files.discard(file_id)

        if success:
            performance_metrics.record_function_call("file_processing_success", 1)
        else:
            performance_metrics.record_function_call("file_processing_failure", 1)

    def is_file_processing(self, file_id: str) -> bool:
        """Check if file is currently being processed."""
        return file_id in self.processing_files


# Global storage management instances
storage_manager = StorageManager()
file_lifecycle_manager = FileLifecycleManager(storage_manager)


async def start_storage_monitoring():
    """Start background storage monitoring and cleanup."""
    logger.info("Starting storage monitoring")

    while True:
        try:
            # Check disk space every 5 minutes
            if storage_manager.is_disk_space_critical():
                await alert_manager.trigger_alert(
                    "disk_space_critical",
                    "critical",
                    f"Disk space critically low: {storage_manager.get_disk_usage()['used_percent']:.1f}% used",
                    storage_manager.get_disk_usage()
                )

                # Trigger cleanup
                await storage_manager.cleanup_old_files(force=True)

            # Regular cleanup check every hour
            await storage_manager.cleanup_old_files(force=False)

            await asyncio.sleep(300)  # Check every 5 minutes

        except Exception as e:
            logger.error(f"Error in storage monitoring: {e}")
            await asyncio.sleep(300)