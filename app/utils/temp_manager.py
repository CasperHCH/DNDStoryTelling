"""
Centralized temporary file management for the DNDStoryTelling application.

This module provides a unified way to create, manage, and clean up temporary files
across the entire application, preventing the creation of multiple temp directories
and ensuring proper cleanup.
"""

import atexit
import logging
import shutil
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class TempFileManager:
    """Centralized manager for temporary files and directories."""

    _instance: Optional["TempFileManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "TempFileManager":
        """Singleton pattern to ensure only one temp manager exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the temp file manager."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._temp_files: Dict[str, Dict[str, Any]] = {}
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

        # Create centralized temp directory
        self._temp_dir = self._create_temp_directory()

        # Register cleanup on exit
        atexit.register(self.cleanup_all)

        # Start background cleanup thread
        self._start_cleanup_thread()

        logger.info(f"TempFileManager initialized with directory: {self._temp_dir}")

    def _create_temp_directory(self) -> Path:
        """Create and return the centralized temporary directory."""
        settings = get_settings()
        base_dir = Path(settings.UPLOAD_DIR).parent
        temp_dir = base_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def _start_cleanup_thread(self):
        """Start the background cleanup thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker, daemon=True, name="TempFileCleanup"
            )
            self._cleanup_thread.start()

    def _cleanup_worker(self):
        """Background worker that periodically cleans up old temp files."""
        while not self._stop_cleanup.wait(timeout=300):  # Check every 5 minutes
            try:
                self.cleanup_old_files(max_age_seconds=3600)  # Clean files older than 1 hour
            except Exception as e:
                logger.error(f"Error in temp file cleanup worker: {e}")

    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "tmp",
        directory: Optional[str] = None,
        delete_on_exit: bool = True,
    ) -> Path:
        """
        Create a temporary file in the centralized temp directory.

        Args:
            suffix: File suffix (e.g., '.wav', '.txt')
            prefix: File prefix
            directory: Subdirectory within temp dir (optional)
            delete_on_exit: Whether to delete file on application exit

        Returns:
            Path to the created temporary file
        """
        if directory:
            target_dir = self._temp_dir / directory
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self._temp_dir

        # Create the temporary file
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=str(target_dir))

        # Close the file descriptor since we just need the path
        import os

        os.close(fd)

        temp_path_obj = Path(temp_path)

        # Track the file
        self._temp_files[str(temp_path_obj)] = {
            "created_at": time.time(),
            "delete_on_exit": delete_on_exit,
            "directory": directory,
        }

        logger.debug(f"Created temp file: {temp_path_obj}")
        return temp_path_obj

    @contextmanager
    def temp_file(self, suffix: str = "", prefix: str = "tmp", directory: Optional[str] = None):
        """
        Context manager for temporary files that are automatically cleaned up.

        Args:
            suffix: File suffix
            prefix: File prefix
            directory: Subdirectory within temp dir

        Yields:
            Path to the temporary file
        """
        temp_path = self.create_temp_file(
            suffix=suffix, prefix=prefix, directory=directory, delete_on_exit=False
        )

        try:
            yield temp_path
        finally:
            self.delete_temp_file(temp_path)

    def create_temp_directory(
        self, suffix: str = "", prefix: str = "tmp", parent_directory: Optional[str] = None
    ) -> Path:
        """
        Create a temporary directory in the centralized temp area.

        Args:
            suffix: Directory suffix
            prefix: Directory prefix
            parent_directory: Parent directory within temp dir

        Returns:
            Path to the created temporary directory
        """
        if parent_directory:
            target_dir = self._temp_dir / parent_directory
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self._temp_dir

        temp_dir = Path(tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(target_dir)))

        # Track the directory
        self._temp_files[str(temp_dir)] = {
            "created_at": time.time(),
            "delete_on_exit": True,
            "is_directory": True,
            "directory": parent_directory,
        }

        logger.debug(f"Created temp directory: {temp_dir}")
        return temp_dir

    @contextmanager
    def temp_directory(
        self, suffix: str = "", prefix: str = "tmp", parent_directory: Optional[str] = None
    ):
        """
        Context manager for temporary directories that are automatically cleaned up.

        Args:
            suffix: Directory suffix
            prefix: Directory prefix
            parent_directory: Parent directory within temp dir

        Yields:
            Path to the temporary directory
        """
        temp_dir = self.create_temp_directory(
            suffix=suffix, prefix=prefix, parent_directory=parent_directory
        )

        try:
            yield temp_dir
        finally:
            self.delete_temp_file(temp_dir)

    def delete_temp_file(self, file_path: Path):
        """
        Delete a specific temporary file or directory.

        Args:
            file_path: Path to the file or directory to delete
        """
        try:
            file_path = Path(file_path)
            str_path = str(file_path)

            if file_path.exists():
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                    logger.debug(f"Deleted temp directory: {file_path}")
                else:
                    file_path.unlink()
                    logger.debug(f"Deleted temp file: {file_path}")

            # Remove from tracking
            if str_path in self._temp_files:
                del self._temp_files[str_path]

        except Exception as e:
            logger.error(f"Error deleting temp file {file_path}: {e}")

    def cleanup_old_files(self, max_age_seconds: int = 3600):
        """
        Clean up temporary files older than the specified age.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
        """
        current_time = time.time()
        files_cleaned = 0

        # Clean tracked files
        files_to_remove = []
        for file_path, info in self._temp_files.items():
            file_age = current_time - info["created_at"]
            if file_age > max_age_seconds:
                files_to_remove.append(file_path)

        for file_path in files_to_remove:
            self.delete_temp_file(Path(file_path))
            files_cleaned += 1

        # Clean untracked files in temp directory
        try:
            for item in self._temp_dir.rglob("*"):
                if item.is_file():
                    file_age = current_time - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            item.unlink()
                            files_cleaned += 1
                            logger.debug(f"Cleaned untracked temp file: {item}")
                        except Exception as e:
                            logger.warning(f"Could not clean untracked file {item}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning untracked temp files: {e}")

        if files_cleaned > 0:
            logger.info(f"Cleaned up {files_cleaned} old temporary files")

    def cleanup_all(self):
        """Clean up all tracked temporary files and the temp directory."""
        logger.info("Cleaning up all temporary files...")

        # Stop cleanup thread
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)

        # Clean all tracked files
        files_to_remove = list(self._temp_files.keys())
        for file_path in files_to_remove:
            self.delete_temp_file(Path(file_path))

        # Remove the entire temp directory if it exists and is empty
        try:
            if self._temp_dir.exists():
                # Only remove if empty
                if not any(self._temp_dir.iterdir()):
                    self._temp_dir.rmdir()
                    logger.info(f"Removed empty temp directory: {self._temp_dir}")
                else:
                    logger.info(f"Temp directory not empty, leaving: {self._temp_dir}")
        except Exception as e:
            logger.error(f"Error removing temp directory: {e}")

    def get_temp_directory(self) -> Path:
        """Get the centralized temporary directory path."""
        return self._temp_dir

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about current temporary files."""
        current_time = time.time()
        stats = {
            "total_files": len(self._temp_files),
            "temp_directory": str(self._temp_dir),
            "files_by_age": {"<1min": 0, "1min-1hr": 0, ">1hr": 0},
            "files_by_type": {"files": 0, "directories": 0},
        }

        for file_path, info in self._temp_files.items():
            age = current_time - info["created_at"]

            # Age categorization
            if age < 60:
                stats["files_by_age"]["<1min"] += 1
            elif age < 3600:
                stats["files_by_age"]["1min-1hr"] += 1
            else:
                stats["files_by_age"][">1hr"] += 1

            # Type categorization
            if info.get("is_directory", False):
                stats["files_by_type"]["directories"] += 1
            else:
                stats["files_by_type"]["files"] += 1

        return stats


# Global instance
_temp_manager = TempFileManager()


# Convenience functions for easy access
def create_temp_file(
    suffix: str = "",
    prefix: str = "tmp",
    directory: Optional[str] = None,
    delete_on_exit: bool = True,
) -> Path:
    """Create a temporary file. See TempFileManager.create_temp_file for details."""
    return _temp_manager.create_temp_file(suffix, prefix, directory, delete_on_exit)


def temp_file(suffix: str = "", prefix: str = "tmp", directory: Optional[str] = None):
    """Context manager for temporary files. See TempFileManager.temp_file for details."""
    return _temp_manager.temp_file(suffix, prefix, directory)


def create_temp_directory(
    suffix: str = "", prefix: str = "tmp", parent_directory: Optional[str] = None
) -> Path:
    """Create a temporary directory. See TempFileManager.create_temp_directory for details."""
    return _temp_manager.create_temp_directory(suffix, prefix, parent_directory)


def temp_directory(suffix: str = "", prefix: str = "tmp", parent_directory: Optional[str] = None):
    """Context manager for temporary directories. See TempFileManager.temp_directory for details."""
    return _temp_manager.temp_directory(suffix, prefix, parent_directory)


def cleanup_old_temp_files(max_age_seconds: int = 3600):
    """Clean up old temporary files. See TempFileManager.cleanup_old_files for details."""
    return _temp_manager.cleanup_old_files(max_age_seconds)


def get_temp_stats() -> Dict[str, Any]:
    """Get temporary file statistics. See TempFileManager.get_stats for details."""
    return _temp_manager.get_stats()


def get_temp_directory() -> Path:
    """Get the centralized temporary directory path."""
    return _temp_manager.get_temp_directory()
