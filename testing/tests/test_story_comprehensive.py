"""Comprehensive tests for story upload endpoint and related functionality."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from io import BytesIO

# Mock pydub to avoid ffmpeg issues during testing
import sys
sys.modules['pydub'] = MagicMock()
sys.modules['pydub.audio_segment'] = MagicMock()


class TestStoryUpload:
    """Test cases for the story upload endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user with OpenAI API key."""
        user = MagicMock()
        user.openai_api_key = "test_openai_key"
        user.id = 1
        return user

    @pytest.fixture
    def mock_user_no_key(self):
        """Create a mock user without OpenAI API key."""
        user = MagicMock()
        user.openai_api_key = None
        user.id = 1
        return user

    @pytest.fixture
    def sample_text_file(self):
        """Create a sample text file for testing."""
        content = b"This is test content for story generation."
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(content),
            size=len(content),
            headers={"content-type": "text/plain"}
        )
        return file

    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample audio file for testing."""
        content = b"fake_audio_content"
        file = UploadFile(
            filename="test.mp3",
            file=BytesIO(content),
            size=len(content),
            headers={"content-type": "audio/mpeg"}
        )
        return file

    @pytest.fixture
    def large_file(self):
        """Create a large file that exceeds size limit."""
        content = b"x" * (51 * 1024 * 1024)  # 51MB
        file = UploadFile(
            filename="large.txt",
            file=BytesIO(content),
            size=len(content),
            headers={"content-type": "text/plain"}
        )
        return file

    @pytest.mark.asyncio
    @patch('app.routes.story.StoryGenerator')
    @patch('app.routes.story.AudioProcessor')
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_text_file_success(self, mock_db, mock_auth, mock_audio_proc_class, mock_story_gen_class, mock_user, sample_text_file):
        """Test successful text file upload and story generation."""
        from app.routes.story import upload_file
        
        # Setup mocks
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        mock_story_gen = AsyncMock()
        mock_story_gen.generate_story = AsyncMock(return_value="Generated story content")
        mock_story_gen_class.return_value = mock_story_gen
        
        mock_audio_proc = AsyncMock()
        mock_audio_proc_class.return_value = mock_audio_proc
        
        context = {"tone": "heroic", "setting": "fantasy"}
        
        # Execute
        result = await upload_file(
            file=sample_text_file,
            context=context,
            db=mock_db.return_value,
            current_user=mock_user
        )
        
        # Verify
        assert result == {"story": "Generated story content"}
        mock_story_gen.generate_story.assert_called_once_with("This is test content for story generation.", context)

    @pytest.mark.asyncio
    @patch('app.routes.story.StoryGenerator')
    @patch('app.routes.story.AudioProcessor')
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_audio_file_success(self, mock_db, mock_auth, mock_audio_proc_class, mock_story_gen_class, mock_user, sample_audio_file):
        """Test successful audio file upload and story generation."""
        from app.routes.story import upload_file
        
        # Setup mocks
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        mock_story_gen = AsyncMock()
        mock_story_gen.generate_story = AsyncMock(return_value="Story from audio")
        mock_story_gen_class.return_value = mock_story_gen
        
        mock_audio_proc = AsyncMock()
        mock_audio_proc.process_audio = AsyncMock(return_value="Transcribed text from audio")
        mock_audio_proc_class.return_value = mock_audio_proc
        
        context = {"tone": "dramatic"}
        
        # Execute
        result = await upload_file(
            file=sample_audio_file,
            context=context,
            db=mock_db.return_value,
            current_user=mock_user
        )
        
        # Verify
        assert result == {"story": "Story from audio"}
        mock_audio_proc.process_audio.assert_called_once()
        mock_story_gen.generate_story.assert_called_once_with("Transcribed text from audio", context)

    @pytest.mark.asyncio
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_no_openai_key(self, mock_db, mock_auth, mock_user_no_key, sample_text_file):
        """Test upload fails when user has no OpenAI API key."""
        from app.routes.story import upload_file
        
        mock_auth.return_value = mock_user_no_key
        mock_db.return_value = MagicMock()
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                file=sample_text_file,
                context={},
                db=mock_db.return_value,
                current_user=mock_user_no_key
            )
        
        assert exc_info.value.status_code == 400
        assert "OpenAI API key not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_no_filename(self, mock_db, mock_auth, mock_user):
        """Test upload fails when no filename provided."""
        from app.routes.story import upload_file
        
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        # Create file with no filename
        file = UploadFile(
            filename=None,
            file=BytesIO(b"content"),
            size=7
        )
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                file=file,
                context={},
                db=mock_db.return_value,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400
        assert "No file provided" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_file_too_large(self, mock_db, mock_auth, mock_user, large_file):
        """Test upload fails when file is too large."""
        from app.routes.story import upload_file
        
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                file=large_file,
                context={},
                db=mock_db.return_value,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.routes.story.StoryGenerator')
    @patch('app.routes.story.AudioProcessor')
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_invalid_text_encoding(self, mock_db, mock_auth, mock_audio_proc_class, mock_story_gen_class, mock_user):
        """Test upload fails with invalid text file encoding."""
        from app.routes.story import upload_file
        
        # Setup mocks
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        mock_story_gen_class.return_value = AsyncMock()
        mock_audio_proc_class.return_value = AsyncMock()
        
        # Create file with invalid encoding
        invalid_content = b'\xff\xfe\x00\x00invalid_utf8'
        file = UploadFile(
            filename="invalid.txt",
            file=BytesIO(invalid_content),
            size=len(invalid_content),
            headers={"content-type": "text/plain"}
        )
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                file=file,
                context={},
                db=mock_db.return_value,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid text file encoding" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.routes.story.StoryGenerator')
    @patch('app.routes.story.AudioProcessor')
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_story_generation_fails(self, mock_db, mock_auth, mock_audio_proc_class, mock_story_gen_class, mock_user, sample_text_file):
        """Test upload handles story generation failure."""
        from app.routes.story import upload_file
        
        # Setup mocks
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        mock_story_gen = AsyncMock()
        mock_story_gen.generate_story = AsyncMock(side_effect=Exception("Story generation failed"))
        mock_story_gen_class.return_value = mock_story_gen
        
        mock_audio_proc_class.return_value = AsyncMock()
        
        context = {"tone": "heroic"}
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                file=sample_text_file,
                context=context,
                db=mock_db.return_value,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.routes.story.StoryGenerator')
    @patch('app.routes.story.AudioProcessor')
    @patch('app.routes.story.get_current_user')
    @patch('app.routes.story.get_db')
    async def test_upload_audio_processing_fails(self, mock_db, mock_auth, mock_audio_proc_class, mock_story_gen_class, mock_user, sample_audio_file):
        """Test upload handles audio processing failure."""
        from app.routes.story import upload_file
        
        # Setup mocks
        mock_auth.return_value = mock_user
        mock_db.return_value = MagicMock()
        
        mock_story_gen_class.return_value = AsyncMock()
        
        mock_audio_proc = AsyncMock()
        mock_audio_proc.process_audio = AsyncMock(side_effect=Exception("Audio processing failed"))
        mock_audio_proc_class.return_value = mock_audio_proc
        
        context = {"tone": "dramatic"}
        
        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                file=sample_audio_file,
                context=context,
                db=mock_db.return_value,
                current_user=mock_user
            )
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail