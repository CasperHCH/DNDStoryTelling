"""Audio processing service for transcription and analysis."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import whisper
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from app.config import get_settings
from app.utils.temp_manager import temp_file, cleanup_old_temp_files, TempFileManager

logger = logging.getLogger(__name__)

class AudioProcessingError(Exception):
    """Custom exception for audio processing errors."""
    pass

class AudioProcessor:
    """Service for processing audio files with Whisper transcription."""

    def __init__(self, model_size: str = "base"):
        """Initialize the audio processor with specified model size."""
        self.model_size = model_size
        self._model: Optional[whisper.Whisper] = None
        self.supported_formats = get_settings().supported_audio_formats_list

    @property
    def model(self) -> whisper.Whisper:
        """Lazy load the Whisper model to save memory."""
        if self._model is None:
            try:
                logger.info(f"Loading Whisper model: {self.model_size}")
                self._model = whisper.load_model(self.model_size)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise AudioProcessingError(f"Failed to load Whisper model: {e}")
        return self._model

    def validate_audio_file(self, file_path: Path) -> None:
        """Validate audio file format and size."""
        if not file_path.exists():
            raise AudioProcessingError(f"Audio file not found: {file_path}")

        file_size = file_path.stat().st_size
        if file_size > get_settings().MAX_FILE_SIZE:
            raise AudioProcessingError(
                f"File too large: {file_size} bytes (max: {get_settings().MAX_FILE_SIZE} bytes)"
            )

        file_extension = file_path.suffix.lower().lstrip('.')
        if file_extension not in self.supported_formats:
            raise AudioProcessingError(
                f"Unsupported audio format: {file_extension}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )

    async def process_audio(
        self,
        file_path: str | Path,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Process audio file and return transcription with metadata.

        Args:
            file_path: Path to audio file
            language: Optional language hint for Whisper
            task: Either 'transcribe' or 'translate'

        Returns:
            Dictionary containing transcription and metadata
        """
        file_path = Path(file_path)

        try:
            # Validate input file
            self.validate_audio_file(file_path)

            # Convert to standard format for processing
            normalized_path = await self._normalize_audio_format(file_path)

            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_audio,
                normalized_path,
                language,
                task
            )

            # Clean up temporary file if created
            if normalized_path != file_path:
                normalized_path.unlink(missing_ok=True)

            return {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "duration": self._get_audio_duration(file_path),
                "file_size": file_path.stat().st_size,
                "processing_successful": True
            }

        except Exception as e:
            logger.error(f"Audio processing failed for {file_path}: {e}")
            raise AudioProcessingError(f"Audio processing failed: {e}")

    async def _normalize_audio_format(self, file_path: Path) -> Path:
        """Convert audio to WAV format if needed."""
        if file_path.suffix.lower() == '.wav':
            return file_path

        try:
            logger.debug(f"Converting {file_path} to WAV format")
            audio = AudioSegment.from_file(str(file_path))

            # Create temporary WAV file using centralized manager
            temp_manager = TempFileManager()
            temp_path = temp_manager.create_temp_file(suffix=".wav", directory="audio")

            # Export to WAV with optimized settings
            audio.export(
                str(temp_path),
                format="wav",
                parameters=["-ar", "16000", "-ac", "1"]  # 16kHz mono for efficiency
            )

            logger.debug(f"Audio converted successfully: {temp_path}")
            # Note: temp file will be cleaned up automatically by the background cleanup
            return temp_path

        except CouldntDecodeError as e:
            raise AudioProcessingError(f"Could not decode audio file: {e}")
        except Exception as e:
            raise AudioProcessingError(f"Audio conversion failed: {e}")

    def _transcribe_audio(
        self,
        file_path: Path,
        language: Optional[str],
        task: str
    ) -> Dict[str, Any]:
        """Perform the actual transcription using Whisper."""
        try:
            logger.info(f"Starting transcription of {file_path}")

            result = self.model.transcribe(
                str(file_path),
                language=language,
                task=task,
                verbose=False,
                word_timestamps=True
            )

            logger.info(f"Transcription completed for {file_path}")
            return result

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise AudioProcessingError(f"Transcription failed: {e}")

    def _get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds."""
        try:
            audio = AudioSegment.from_file(str(file_path))
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            return 0.0

    def get_supported_formats(self) -> List[str]:
        """Return list of supported audio formats."""
        return self.supported_formats.copy()

    async def cleanup_temp_files(self) -> None:
        """Clean up old temporary files using centralized manager."""
        try:
            cleanup_old_temp_files(max_age_seconds=3600)  # 1 hour
            logger.info("Temporary audio files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")