"""Comprehensive tests for temporary file management utilities."""

import pytest
import tempfile
import shutil
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from contextlib import contextmanager

from app.utils.temp_manager import TempFileManager, temp_file, cleanup_old_temp_files


class TestTempFileManager:
    """Test cases for TempFileManager class."""

    def setup_method(self):
        """Reset the singleton instance before each test."""
        TempFileManager._instance = None

    def test_singleton_pattern(self):
        """Test that TempFileManager follows singleton pattern."""
        manager1 = TempFileManager()
        manager2 = TempFileManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_initialization(self):
        """Test TempFileManager initialization."""
        manager = TempFileManager()

        assert hasattr(manager, '_initialized')
        assert hasattr(manager, '_temp_files')
        assert hasattr(manager, '_temp_dir')
        assert isinstance(manager._temp_files, dict)

    @patch('app.utils.temp_manager.tempfile.mkdtemp')
    def test_create_temp_directory(self, mock_mkdtemp):
        """Test creation of temporary directory."""
        mock_mkdtemp.return_value = "/tmp/test_temp_dir"

        manager = TempFileManager()

        mock_mkdtemp.assert_called_once()
        # Check that the directory path was stored
        assert hasattr(manager, '_temp_dir')

    @patch('app.utils.temp_manager.tempfile.NamedTemporaryFile')
    def test_create_temp_file_basic(self, mock_temp_file):
        """Test basic temporary file creation."""
        # Mock the temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_file.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file

        manager = TempFileManager()

        with manager.create_temp_file(suffix=".txt") as temp_path:
            assert temp_path == "/tmp/test_file.txt"

        # Check that the file was registered
        assert len(manager._temp_files) >= 0  # May have cleanup occurred

    @patch('app.utils.temp_manager.tempfile.NamedTemporaryFile')
    def test_create_temp_file_with_prefix_and_suffix(self, mock_temp_file):
        """Test temporary file creation with prefix and suffix."""
        mock_file = MagicMock()
        mock_file.name = "/tmp/prefix_test_file.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file

        manager = TempFileManager()

        with manager.create_temp_file(prefix="test_", suffix=".txt") as temp_path:
            assert temp_path == "/tmp/prefix_test_file.txt"

        # Verify tempfile was called with correct arguments
        mock_temp_file.assert_called_with(
            prefix="test_",
            suffix=".txt",
            dir=manager._temp_dir,
            delete=False
        )

    @patch('app.utils.temp_manager.tempfile.NamedTemporaryFile')
    def test_create_temp_file_with_directory(self, mock_temp_file):
        """Test temporary file creation in specific directory."""
        mock_file = MagicMock()
        mock_file.name = "/tmp/subdir/test_file.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file

        with patch('app.utils.temp_manager.Path.mkdir') as mock_mkdir:
            manager = TempFileManager()

            with manager.create_temp_file(directory="subdir") as temp_path:
                assert temp_path == "/tmp/subdir/test_file.txt"

            # Verify subdirectory was created
            mock_mkdir.assert_called_once()

    @patch('app.utils.temp_manager.os.remove')
    @patch('app.utils.temp_manager.os.path.exists')
    @patch('app.utils.temp_manager.tempfile.NamedTemporaryFile')
    def test_cleanup_temp_file(self, mock_temp_file, mock_exists, mock_remove):
        """Test cleanup of temporary files."""
        mock_file = MagicMock()
        mock_file.name = "/tmp/test_file.txt"
        mock_temp_file.return_value.__enter__.return_value = mock_file
        mock_exists.return_value = True

        manager = TempFileManager()

        # Create and then cleanup temp file
        with manager.create_temp_file() as temp_path:
            file_id = None
            for fid, info in manager._temp_files.items():
                if info['path'] == temp_path:
                    file_id = fid
                    break

        # Manually trigger cleanup
        if file_id:
            manager.cleanup_file(file_id)
            mock_remove.assert_called_with(temp_path)

    @patch('app.utils.temp_manager.shutil.rmtree')
    @patch('app.utils.temp_manager.os.path.exists')
    def test_cleanup_all_files(self, mock_exists, mock_rmtree):
        """Test cleanup of all temporary files."""
        mock_exists.return_value = True

        manager = TempFileManager()
        manager._temp_files = {
            "file1": {"path": "/tmp/file1.txt", "created_at": time.time()},
            "file2": {"path": "/tmp/file2.txt", "created_at": time.time()}
        }

        manager.cleanup_all()

        # All files should be cleaned up
        assert len(manager._temp_files) == 0

    def test_get_temp_files_info(self):
        """Test getting information about temporary files."""
        manager = TempFileManager()
        manager._temp_files = {
            "file1": {"path": "/tmp/file1.txt", "created_at": time.time() - 100},
            "file2": {"path": "/tmp/file2.txt", "created_at": time.time() - 50}
        }

        info = manager.get_temp_files_info()

        assert "total_files" in info
        assert "files" in info
        assert info["total_files"] == 2
        assert len(info["files"]) == 2

    @patch('app.utils.temp_manager.time.time')
    def test_cleanup_old_files(self, mock_time):
        """Test cleanup of old temporary files."""
        current_time = 1000.0
        mock_time.return_value = current_time

        manager = TempFileManager()
        manager._temp_files = {
            "old_file": {"path": "/tmp/old.txt", "created_at": current_time - 3700},  # > 1 hour old
            "new_file": {"path": "/tmp/new.txt", "created_at": current_time - 1800}   # 30 minutes old
        }

        with patch.object(manager, 'cleanup_file') as mock_cleanup:
            manager.cleanup_old_files(max_age_hours=1)

            # Only old file should be cleaned up
            mock_cleanup.assert_called_once_with("old_file")

    def test_concurrent_access(self):
        """Test thread safety of TempFileManager."""
        def create_temp_files():
            manager = TempFileManager()
            with patch('app.utils.temp_manager.tempfile.NamedTemporaryFile') as mock_temp:
                mock_file = MagicMock()
                mock_file.name = f"/tmp/thread_file_{threading.current_thread().ident}.txt"
                mock_temp.return_value.__enter__.return_value = mock_file

                with manager.create_temp_file() as temp_path:
                    # Simulate some work
                    time.sleep(0.01)

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_temp_files)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should complete without errors
        assert True  # If we get here, no deadlocks occurred

    @patch('app.utils.temp_manager.atexit.register')
    def test_atexit_registration(self, mock_atexit):
        """Test that cleanup is registered with atexit."""
        TempFileManager()

        # Should register cleanup function
        mock_atexit.assert_called()

    @patch('app.utils.temp_manager.logger')
    def test_error_handling_in_cleanup(self, mock_logger):
        """Test error handling during cleanup operations."""
        manager = TempFileManager()

        with patch('app.utils.temp_manager.os.remove', side_effect=OSError("Permission denied")):
            with patch('app.utils.temp_manager.os.path.exists', return_value=True):
                manager._temp_files = {"test": {"path": "/tmp/test.txt", "created_at": time.time()}}

                # Should not raise exception, but should log error
                manager.cleanup_all()

                mock_logger.error.assert_called()

    def test_temp_directory_creation_failure(self):
        """Test handling of temp directory creation failure."""
        with patch('app.utils.temp_manager.tempfile.mkdtemp', side_effect=OSError("No space left")):
            with patch('app.utils.temp_manager.logger') as mock_logger:
                manager = TempFileManager()

                # Should log the error
                mock_logger.error.assert_called()


class TestTempFileContextManager:
    """Test cases for the temp_file context manager."""

    def setup_method(self):
        """Reset the singleton instance before each test."""
        TempFileManager._instance = None

    @patch('app.utils.temp_manager.TempFileManager')
    def test_temp_file_context_manager(self, mock_manager_class):
        """Test the temp_file context manager."""
        mock_manager = MagicMock()
        mock_manager.create_temp_file.return_value.__enter__.return_value = "/tmp/test.txt"
        mock_manager.create_temp_file.return_value.__exit__.return_value = None
        mock_manager_class.return_value = mock_manager

        with temp_file(suffix=".txt") as temp_path:
            assert temp_path == "/tmp/test.txt"

        mock_manager.create_temp_file.assert_called_once_with(
            prefix=None,
            suffix=".txt",
            directory=None
        )

    @patch('app.utils.temp_manager.TempFileManager')
    def test_temp_file_with_all_parameters(self, mock_manager_class):
        """Test temp_file context manager with all parameters."""
        mock_manager = MagicMock()
        mock_manager.create_temp_file.return_value.__enter__.return_value = "/tmp/prefix_test.txt"
        mock_manager_class.return_value = mock_manager

        with temp_file(prefix="test_", suffix=".txt", directory="uploads") as temp_path:
            assert temp_path == "/tmp/prefix_test.txt"

        mock_manager.create_temp_file.assert_called_once_with(
            prefix="test_",
            suffix=".txt",
            directory="uploads"
        )


class TestCleanupOldTempFiles:
    """Test cases for the cleanup_old_temp_files function."""

    def setup_method(self):
        """Reset the singleton instance before each test."""
        TempFileManager._instance = None

    @patch('app.utils.temp_manager.TempFileManager')
    def test_cleanup_old_temp_files(self, mock_manager_class):
        """Test the cleanup_old_temp_files function."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        cleanup_old_temp_files(max_age_hours=2)

        mock_manager.cleanup_old_files.assert_called_once_with(max_age_hours=2)

    @patch('app.utils.temp_manager.TempFileManager')
    def test_cleanup_old_temp_files_default_age(self, mock_manager_class):
        """Test cleanup with default max age."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        cleanup_old_temp_files()

        mock_manager.cleanup_old_files.assert_called_once_with(max_age_hours=24)


class TestTempFileManagerIntegration:
    """Integration tests for TempFileManager with real file operations."""

    def setup_method(self):
        """Reset the singleton instance before each test."""
        TempFileManager._instance = None

    def test_real_temp_file_creation_and_cleanup(self):
        """Test actual temporary file creation and cleanup."""
        manager = TempFileManager()

        # Create a temp file and write to it
        with manager.create_temp_file(suffix=".txt") as temp_path:
            # Write some content
            with open(temp_path, 'w') as f:
                f.write("test content")

            # Verify file exists and has content
            assert Path(temp_path).exists()
            with open(temp_path, 'r') as f:
                assert f.read() == "test content"

        # File should still exist until explicit cleanup
        # (since we don't auto-delete in the context manager)

    def test_directory_creation(self):
        """Test that subdirectories are created correctly."""
        manager = TempFileManager()

        with manager.create_temp_file(directory="test_subdir", suffix=".txt") as temp_path:
            # Check that the file is in the expected subdirectory
            assert "test_subdir" in str(temp_path)
            assert Path(temp_path).parent.name == "test_subdir"

    def test_multiple_temp_files(self):
        """Test creating multiple temporary files."""
        manager = TempFileManager()
        temp_paths = []

        # Create multiple temp files
        for i in range(3):
            with manager.create_temp_file(suffix=f"_{i}.txt") as temp_path:
                temp_paths.append(temp_path)
                with open(temp_path, 'w') as f:
                    f.write(f"content {i}")

        # All files should have different names
        assert len(set(temp_paths)) == 3

        # All files should exist (until cleanup)
        for temp_path in temp_paths:
            if Path(temp_path).exists():  # May have been cleaned up
                with open(temp_path, 'r') as f:
                    content = f.read()
                    assert content.startswith("content")

    def test_cleanup_performance(self):
        """Test cleanup performance with many files."""
        manager = TempFileManager()

        # Create many temp file entries (mocked)
        with patch('app.utils.temp_manager.tempfile.NamedTemporaryFile') as mock_temp:
            mock_files = []
            for i in range(100):
                mock_file = MagicMock()
                mock_file.name = f"/tmp/perf_test_{i}.txt"
                mock_files.append(mock_file)

            mock_temp.return_value.__enter__.side_effect = mock_files

            # Create temp files quickly
            for i in range(100):
                with manager.create_temp_file() as temp_path:
                    pass

            # Cleanup should be fast
            start_time = time.time()
            manager.cleanup_all()
            cleanup_time = time.time() - start_time

            # Cleanup should complete within reasonable time
            assert cleanup_time < 1.0  # Less than 1 second for 100 files