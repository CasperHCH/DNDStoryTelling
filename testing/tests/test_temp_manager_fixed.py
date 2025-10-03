"""Comprehensive tests for temp file manager utilities."""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import os
import tempfile
from app.utils.temp_manager import TempFileManager


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
        assert manager is not None
        assert hasattr(manager, '_temp_dir')

    def test_create_temp_file_basic(self):
        """Test basic temporary file creation."""
        manager = TempFileManager()

        with manager.create_temp_file() as temp_path:
            assert temp_path is not None
            assert isinstance(temp_path, Path)
            # File should exist during context
            assert temp_path.exists()

    def test_create_temp_file_with_prefix_suffix(self):
        """Test temporary file creation with prefix and suffix."""
        manager = TempFileManager()

        with manager.create_temp_file(prefix="test_", suffix=".txt") as temp_path:
            assert temp_path is not None
            assert isinstance(temp_path, Path)
            assert temp_path.suffix == ".txt"
            assert "test_" in temp_path.name

    def test_create_temp_file_with_content(self):
        """Test temporary file creation with initial content."""
        manager = TempFileManager()
        test_content = "Hello, World!"

        with manager.create_temp_file(content=test_content) as temp_path:
            assert temp_path.exists()
            content = temp_path.read_text()
            assert content == test_content

    def test_create_temp_file_binary_mode(self):
        """Test temporary file creation in binary mode."""
        manager = TempFileManager()
        test_content = b"Binary content"

        with manager.create_temp_file(content=test_content, mode='wb') as temp_path:
            assert temp_path.exists()
            content = temp_path.read_bytes()
            assert content == test_content

    def test_temp_file_cleanup(self):
        """Test that temporary files are cleaned up after context."""
        manager = TempFileManager()
        temp_path = None

        with manager.create_temp_file() as path:
            temp_path = path
            assert temp_path.exists()

        # File should be cleaned up after context
        assert not temp_path.exists()

    def test_create_temp_directory_basic(self):
        """Test basic temporary directory creation."""
        manager = TempFileManager()

        temp_dir = manager.create_temp_directory()
        assert temp_dir is not None
        assert isinstance(temp_dir, Path)
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_create_temp_directory_with_prefix(self):
        """Test temporary directory creation with prefix."""
        manager = TempFileManager()

        temp_dir = manager.create_temp_directory(prefix="test_")
        assert temp_dir.exists()
        assert "test_" in temp_dir.name

    def test_cleanup_all_basic(self):
        """Test cleanup of all temporary files."""
        manager = TempFileManager()

        # Create some temp files
        temp_paths = []
        for i in range(3):
            with manager.create_temp_file() as temp_path:
                temp_paths.append(temp_path)

        # All should be cleaned up after context
        for path in temp_paths:
            assert not path.exists()

    def test_cleanup_on_exit(self):
        """Test that cleanup is registered for exit."""
        with patch('app.utils.temp_manager.atexit.register') as mock_register:
            manager = TempFileManager()
            mock_register.assert_called()

    def test_logger_usage(self):
        """Test that logging is used appropriately."""
        with patch('app.utils.temp_manager.logger') as mock_logger:
            manager = TempFileManager()
            # Logger should be used for initialization
            mock_logger.info.assert_called()

    def test_concurrent_access(self):
        """Test thread safety of the singleton."""
        import threading

        instances = []

        def create_instance():
            instances.append(TempFileManager())

        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance

    def test_temp_dir_persistence(self):
        """Test that temp directory persists across multiple operations."""
        manager = TempFileManager()

        # Create multiple temp files
        paths = []
        for i in range(3):
            with manager.create_temp_file() as temp_path:
                paths.append(temp_path.parent)

        # All should use the same temp directory
        base_dir = paths[0]
        for path in paths[1:]:
            assert path == base_dir

    def test_error_handling_in_cleanup(self):
        """Test error handling during cleanup operations."""
        manager = TempFileManager()

        # Mock os.remove to raise an exception
        with patch('app.utils.temp_manager.os.remove', side_effect=OSError("Test error")):
            with patch('app.utils.temp_manager.logger') as mock_logger:
                # This should not raise an exception
                try:
                    with manager.create_temp_file() as temp_path:
                        pass  # File will fail to clean up
                except OSError:
                    pass  # Expected

                # Logger should record the error
                mock_logger.error.assert_called()

    def test_pathlib_integration(self):
        """Test integration with pathlib.Path operations."""
        manager = TempFileManager()

        with manager.create_temp_file(suffix=".txt") as temp_path:
            # Should support pathlib operations
            assert temp_path.suffix == ".txt"
            assert temp_path.exists()
            assert temp_path.is_file()

            # Should support writing/reading
            temp_path.write_text("Test content")
            content = temp_path.read_text()
            assert content == "Test content"

    def test_temp_file_in_subdirectory(self):
        """Test creating temp files in subdirectories."""
        manager = TempFileManager()

        # Create subdirectory first
        subdir = manager.create_temp_directory(prefix="subdir_")

        # Create file in subdirectory using manual path construction
        with tempfile.NamedTemporaryFile(dir=str(subdir), delete=False, suffix=".txt") as f:
            temp_path = Path(f.name)

        try:
            assert temp_path.exists()
            assert temp_path.parent == subdir
        finally:
            # Manual cleanup since we used delete=False
            if temp_path.exists():
                temp_path.unlink()

    @patch('app.utils.temp_manager.tempfile.mkdtemp')
    def test_create_temp_directory_mocked(self, mock_mkdtemp):
        """Test temporary directory creation with mocked tempfile."""
        mock_mkdtemp.return_value = "/tmp/mocked_dir"

        manager = TempFileManager()
        result = manager.create_temp_directory(prefix="test_")

        assert str(result) == "/tmp/mocked_dir"
        mock_mkdtemp.assert_called_with(prefix="test_")

    def test_context_manager_exception_handling(self):
        """Test context manager behavior when exceptions occur."""
        manager = TempFileManager()
        temp_path = None

        try:
            with manager.create_temp_file() as path:
                temp_path = path
                assert temp_path.exists()
                # Raise an exception within the context
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # File should still be cleaned up despite the exception
        assert not temp_path.exists()

    def test_multiple_managers_same_instance(self):
        """Test that multiple TempFileManager calls return same instance."""
        manager1 = TempFileManager()
        manager2 = TempFileManager()
        manager3 = TempFileManager()

        assert manager1 is manager2
        assert manager2 is manager3
        assert manager1 is manager3

    def test_file_permissions(self):
        """Test that temporary files have appropriate permissions."""
        manager = TempFileManager()

        with manager.create_temp_file() as temp_path:
            # File should be readable and writable by owner
            stat_info = temp_path.stat()
            # Check that file exists and has some permissions
            assert stat_info.st_size >= 0

            # Try to write to the file to verify permissions
            temp_path.write_text("Permission test")
            content = temp_path.read_text()
            assert content == "Permission test"