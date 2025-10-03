"""Test configuration to avoid PyTorch warnings and enable proper async testing."""

import os
import warnings
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, Mock

# Suppress PyTorch warnings during testing
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*weights_only.*")

# Set environment variables for testing
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = "test-key-12345"

# Import the mock after setting environment
from testing.mocks.audio_mock import MockAudioProcessor


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_audio_processor():
    """Provide a mock audio processor for testing."""
    return MockAudioProcessor()


@pytest.fixture(autouse=True)
def mock_whisper_globally():
    """Mock Whisper globally to avoid loading actual models."""
    with patch('app.services.audio_processor.whisper') as mock_whisper:
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Mock transcription result",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Mock transcription result",
                    "confidence": 0.95
                }
            ],
            "language": "en"
        }
        mock_whisper.load_model.return_value = mock_model
        yield mock_whisper


@pytest.fixture
def sample_audio_file(tmp_path):
    """Create a sample audio file for testing."""
    audio_file = tmp_path / "test_audio.wav"
    # Create a minimal WAV file (just header + minimal data)
    wav_header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00'
    audio_file.write_bytes(wav_header)
    return audio_file