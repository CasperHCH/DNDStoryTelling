# filepath: c:\repos\DNDStoryTelling\tests\test_audio_processor.py
import pytest
from app.services.audio_processor import AudioProcessor
import tempfile
from pydub import AudioSegment
import os

@pytest.fixture
def audio_file():
    # Create a simple audio file for testing
    audio = AudioSegment.silent(duration=1000)  # 1 second of silence
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        audio.export(temp_file.name, format="wav")
        yield temp_file.name
    os.unlink(temp_file.name)

@pytest.mark.asyncio
async def test_process_audio(audio_file):
    processor = AudioProcessor()
    result = await processor.process_audio(audio_file)
    assert isinstance(result, str)
    assert len(result) >= 0  # Even empty audio should return empty string