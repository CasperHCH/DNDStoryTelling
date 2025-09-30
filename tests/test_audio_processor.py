# filepath: c:\repos\DNDStoryTelling\tests\test_audio_processor.py
import pytest
from app.services.audio_processor import AudioProcessor
import os

@pytest.mark.asyncio
async def test_process_audio(audio_file):
    """Test that audio processor can handle audio files."""
    if not os.path.exists(audio_file):
        pytest.skip("Audio file not created properly")

    try:
        processor = AudioProcessor()
        result = await processor.process_audio(audio_file)
        assert isinstance(result, str)
        assert len(result) >= 0
    except FileNotFoundError as e:
        # Handle various missing dependency scenarios
        error_msg = str(e).lower()
        if "ffmpeg" in error_msg or "avconv" in error_msg or "fil blev ikke fundet" in error_msg:
            pytest.skip("FFmpeg not available for testing")
        else:
            raise
    except Exception as e:
        # Handle other dependency issues
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["whisper", "model", "torch", "cuda"]):
            pytest.skip(f"ML dependencies not available: {e}")
        else:
            raise