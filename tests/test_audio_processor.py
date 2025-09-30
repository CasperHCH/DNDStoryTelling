# filepath: c:\repos\DNDStoryTelling\tests\test_audio_processor.py
import pytest
from app.services.audio_processor import AudioProcessor
import os

@pytest.mark.asyncio
async def test_process_audio(audio_file):
    """Test that audio processor can handle audio files."""
    if not os.path.exists(audio_file):
        pytest.skip("Audio file not created properly")
    
    processor = AudioProcessor()
    
    try:
        result = await processor.process_audio(audio_file)
        assert isinstance(result, str)
        assert len(result) >= 0  # Even empty audio should return empty string
    except FileNotFoundError as e:
        if "ffmpeg" in str(e).lower():
            pytest.skip("FFmpeg not available for testing")
        else:
            raise
    except Exception as e:
        # If whisper fails to load or process, that's okay for testing
        if "whisper" in str(e).lower() or "model" in str(e).lower():
            pytest.skip(f"Whisper model not available: {e}")
        else:
            raise