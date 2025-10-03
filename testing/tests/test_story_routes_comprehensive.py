"""Comprehensive tests for story routes."""

import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import io
from app.main import app
from app.routes.story import router


class TestStoryRoutes:
    """Test cases for story upload and processing endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_upload_story_endpoint_exists(self):
        """Test that the upload story endpoint exists."""
        # Test with empty request first to see the response
        response = self.client.post("/upload-story")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.process_audio')
    @patch('app.routes.story.generate_story')
    def test_upload_story_success(self, mock_generate, mock_process, mock_validate):
        """Test successful story upload and processing."""
        # Setup mocks
        mock_validate.return_value = None  # Validation passes
        mock_process.return_value = "Transcribed text from audio"
        mock_generate.return_value = "Generated story content"
        
        # Create test file
        test_file_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "story" in data
        assert "transcription" in data
        assert data["story"] == "Generated story content"
        assert data["transcription"] == "Transcribed text from audio"
    
    @patch('app.routes.story.validate_file_upload')
    def test_upload_story_validation_error(self, mock_validate):
        """Test story upload with validation error."""
        from app.utils.security import SecurityError
        mock_validate.side_effect = SecurityError("Invalid file type")
        
        test_file_content = b"invalid content"
        files = {"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.process_audio')
    def test_upload_story_processing_error(self, mock_process, mock_validate):
        """Test story upload with audio processing error."""
        mock_validate.return_value = None
        mock_process.side_effect = Exception("Audio processing failed")
        
        test_file_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.process_audio')
    @patch('app.routes.story.generate_story')
    def test_upload_story_generation_error(self, mock_generate, mock_process, mock_validate):
        """Test story upload with story generation error."""
        mock_validate.return_value = None
        mock_process.return_value = "Transcribed text"
        mock_generate.side_effect = Exception("Story generation failed")
        
        test_file_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    def test_upload_story_missing_file(self):
        """Test story upload without file."""
        response = self.client.post("/upload-story")
        
        # Should return 422 for missing required field
        assert response.status_code == 422
    
    def test_upload_story_empty_file(self):
        """Test story upload with empty file."""
        files = {"file": ("", io.BytesIO(b""), "application/octet-stream")}
        
        response = self.client.post("/upload-story", files=files)
        
        # Should handle empty file gracefully
        assert response.status_code in [400, 422, 500]
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.TempFileManager')
    def test_upload_story_temp_file_handling(self, mock_temp_manager, mock_validate):
        """Test temporary file handling during upload."""
        mock_validate.return_value = None
        
        # Mock temp file manager
        mock_manager = MagicMock()
        mock_temp_manager.return_value = mock_manager
        mock_temp_path = Mock()
        mock_temp_path.write_bytes = Mock()
        mock_manager.create_temp_file.return_value.__enter__ = Mock(return_value=mock_temp_path)
        mock_manager.create_temp_file.return_value.__exit__ = Mock(return_value=None)
        
        with patch('app.routes.story.process_audio', side_effect=Exception("Test error")):
            test_file_content = b"fake audio content"
            files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
            
            response = self.client.post("/upload-story", files=files)
            
            # Should use temp file manager
            mock_temp_manager.assert_called_once()
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.process_audio')
    @patch('app.routes.story.generate_story')
    def test_upload_story_large_file(self, mock_generate, mock_process, mock_validate):
        """Test story upload with large file."""
        mock_validate.return_value = None
        mock_process.return_value = "Transcribed large file"
        mock_generate.return_value = "Generated story from large file"
        
        # Create large test file (1MB)
        large_content = b"x" * (1024 * 1024)
        files = {"file": ("large.mp3", io.BytesIO(large_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "story" in data
        assert "transcription" in data
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.process_audio')
    @patch('app.routes.story.generate_story')
    def test_upload_story_different_formats(self, mock_generate, mock_process, mock_validate):
        """Test story upload with different audio formats."""
        mock_validate.return_value = None
        mock_process.return_value = "Transcribed audio"
        mock_generate.return_value = "Generated story"
        
        formats = [
            ("test.mp3", "audio/mpeg"),
            ("test.wav", "audio/wav"),
            ("test.m4a", "audio/m4a"),
            ("test.ogg", "audio/ogg")
        ]
        
        for filename, content_type in formats:
            test_content = b"fake audio content"
            files = {"file": (filename, io.BytesIO(test_content), content_type)}
            
            response = self.client.post("/upload-story", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert "story" in data
    
    @patch('app.routes.story.logger')
    @patch('app.routes.story.validate_file_upload')
    def test_upload_story_logging(self, mock_validate, mock_logger):
        """Test that upload story logs appropriately."""
        mock_validate.side_effect = Exception("Test error")
        
        test_file_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        # Should log errors
        mock_logger.error.assert_called()
    
    def test_upload_story_response_format(self):
        """Test upload story response format consistency."""
        with patch('app.routes.story.validate_file_upload') as mock_validate:
            with patch('app.routes.story.process_audio') as mock_process:
                with patch('app.routes.story.generate_story') as mock_generate:
                    mock_validate.return_value = None
                    mock_process.return_value = "Test transcription"
                    mock_generate.return_value = "Test story"
                    
                    test_file_content = b"fake audio content"
                    files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
                    
                    response = self.client.post("/upload-story", files=files)
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Check response structure
                    assert isinstance(data, dict)
                    assert "story" in data
                    assert "transcription" in data
                    assert isinstance(data["story"], str)
                    assert isinstance(data["transcription"], str)
    
    def test_upload_story_content_type_header(self):
        """Test that responses have appropriate content type."""
        with patch('app.routes.story.validate_file_upload') as mock_validate:
            with patch('app.routes.story.process_audio') as mock_process:
                with patch('app.routes.story.generate_story') as mock_generate:
                    mock_validate.return_value = None
                    mock_process.return_value = "Test transcription"
                    mock_generate.return_value = "Test story"
                    
                    test_file_content = b"fake audio content"
                    files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
                    
                    response = self.client.post("/upload-story", files=files)
                    
                    assert "content-type" in response.headers
                    assert "application/json" in response.headers["content-type"]
    
    @patch('app.routes.story.validate_file_upload')
    @patch('app.routes.story.process_audio')
    @patch('app.routes.story.generate_story')
    def test_upload_story_unicode_handling(self, mock_generate, mock_process, mock_validate):
        """Test story upload handles unicode content properly."""
        mock_validate.return_value = None
        mock_process.return_value = "Transcription with unicode: café, naïve, résumé"
        mock_generate.return_value = "Story with unicode: The café was naïve about résumé quality"
        
        test_file_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(test_file_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle unicode properly
        assert "café" in data["transcription"]
        assert "naïve" in data["transcription"]
        assert "résumé" in data["transcription"]
    
    def test_upload_story_concurrent_requests(self):
        """Test handling of concurrent upload requests."""
        import concurrent.futures
        import threading
        
        def make_upload_request():
            with patch('app.routes.story.validate_file_upload') as mock_validate:
                with patch('app.routes.story.process_audio') as mock_process:
                    with patch('app.routes.story.generate_story') as mock_generate:
                        mock_validate.return_value = None
                        mock_process.return_value = f"Transcription {threading.current_thread().ident}"
                        mock_generate.return_value = f"Story {threading.current_thread().ident}"
                        
                        test_content = b"fake audio content"
                        files = {"file": ("test.mp3", io.BytesIO(test_content), "audio/mpeg")}
                        
                        return self.client.post("/upload-story", files=files)
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_upload_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete
        for response in responses:
            assert response.status_code == 200
    
    @patch('app.routes.story.validate_file_upload')
    def test_upload_story_file_size_validation(self, mock_validate):
        """Test file size validation during upload."""
        from app.utils.security import SecurityError
        mock_validate.side_effect = SecurityError("File too large")
        
        # Large file content
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB
        files = {"file": ("huge.mp3", io.BytesIO(large_content), "audio/mpeg")}
        
        response = self.client.post("/upload-story", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_upload_story_filename_sanitization(self):
        """Test that filenames are properly sanitized."""
        with patch('app.routes.story.validate_file_upload') as mock_validate:
            with patch('app.routes.story.process_audio') as mock_process:
                with patch('app.routes.story.generate_story') as mock_generate:
                    mock_validate.return_value = None
                    mock_process.return_value = "Transcription"
                    mock_generate.return_value = "Story"
                    
                    # Potentially dangerous filename
                    dangerous_filename = "../../../etc/passwd.mp3"
                    test_content = b"fake audio content"
                    files = {"file": (dangerous_filename, io.BytesIO(test_content), "audio/mpeg")}
                    
                    response = self.client.post("/upload-story", files=files)
                    
                    # Should handle safely (validation should catch this)
                    assert response.status_code in [200, 400]  # Either processed safely or rejected
    
    def test_upload_story_memory_efficiency(self):
        """Test that upload handles memory efficiently for large files."""
        with patch('app.routes.story.validate_file_upload') as mock_validate:
            with patch('app.routes.story.process_audio') as mock_process:
                with patch('app.routes.story.generate_story') as mock_generate:
                    mock_validate.return_value = None
                    mock_process.return_value = "Transcription"
                    mock_generate.return_value = "Story"
                    
                    # Simulate streaming upload
                    test_content = b"audio_data" * 10000  # Reasonably large
                    files = {"file": ("stream_test.mp3", io.BytesIO(test_content), "audio/mpeg")}
                    
                    response = self.client.post("/upload-story", files=files)
                    
                    assert response.status_code == 200
                    # Should complete without memory issues