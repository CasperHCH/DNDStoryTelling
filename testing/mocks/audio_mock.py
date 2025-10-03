"""Mock audio processor for testing without requiring Whisper models."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from unittest.mock import Mock

logger = logging.getLogger(__name__)


class MockAudioProcessor:
    """Mock audio processor for testing."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.supported_formats = ["wav", "mp3", "m4a", "flac", "ogg"]
        self._model = Mock()

    @property
    def model(self):
        """Return mock model."""
        return self._model

    def validate_audio_file(self, file_path: Path) -> None:
        """Mock validation that always passes for test files."""
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB limit
            raise ValueError("File too large")

    async def process_audio(
        self,
        file_path: str | Path,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """Mock audio processing that returns simulated results."""
        file_path = Path(file_path)

        # Validate input
        self.validate_audio_file(file_path)

        # Simulate processing delay
        await asyncio.sleep(0.1)

        # Return mock transcription result
        return {
            "text": "This is a mock transcription of the audio file.",
            "confidence": 0.95,  # Add confidence at top level for test compatibility
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "This is a mock transcription of the audio file.",
                    "confidence": 0.95
                }
            ],
            "language": language or "en",
            "task": task,
            "duration": 5.0,
            "model_size": self.model_size,
            "processing_time": 0.1,
            "processing_successful": True  # Add processing success flag
        }

    async def _normalize_audio_format(self, file_path: Path) -> Path:
        """Mock normalization that returns the same path."""
        return file_path

    def _transcribe_audio(self, file_path: Path, language: Optional[str], task: str) -> Dict[str, Any]:
        """Mock transcription method."""
        return {
            "text": "Mock transcription result",
            "segments": [],
            "language": language or "en"
        }


# Audio processing mock that can be used to replace the real processor
def create_mock_audio_processor():
    """Factory function to create mock audio processor."""
    return MockAudioProcessor()