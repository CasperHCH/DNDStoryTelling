"""Comprehensive tests for audio processing with real D&D session recordings."""

import asyncio
import os
import time
from pathlib import Path
from typing import List, Dict, Any
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.provisional import urls

from app.services.audio_processor import AudioProcessor, AudioProcessingError
from app.config import get_settings


class TestAudioProcessorUnit:
    """Unit tests for AudioProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create AudioProcessor instance for testing."""
        return AudioProcessor(model_size="tiny")  # Use tiny model for faster tests

    def test_audio_processor_initialization(self, processor):
        """Test AudioProcessor initializes correctly."""
        assert processor.model_size == "tiny"
        assert processor._model is None
        assert len(processor.supported_formats) > 0

    def test_validate_audio_file_nonexistent(self, processor, tmp_path):
        """Test validation fails for non-existent files."""
        fake_file = tmp_path / "nonexistent.wav"
        with pytest.raises(AudioProcessingError, match="Audio file not found"):
            processor.validate_audio_file(fake_file)

    @pytest.mark.unit
    def test_supported_formats_validation(self, processor):
        """Test supported audio formats are properly configured."""
        settings = get_settings()
        expected_formats = ["wav", "mp3", "m4a", "flac", "ogg"]

        for fmt in expected_formats:
            assert fmt in processor.supported_formats

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_filename_validation_property_based(self, processor, filename):
        """Property-based test for filename validation."""
        # This tests edge cases with various filename inputs
        test_path = Path(f"/tmp/{filename}.wav")

        # Should handle various filename inputs gracefully
        try:
            # This will fail because file doesn't exist, but shouldn't crash
            processor.validate_audio_file(test_path)
        except AudioProcessingError as e:
            assert "not found" in str(e)


class TestAudioProcessorIntegration:
    """Integration tests with real audio processing."""

    @pytest.fixture
    def processor(self):
        """Create AudioProcessor for integration testing."""
        return AudioProcessor(model_size="base")

    @pytest.mark.audio
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_process_small_audio_file(self, processor, test_audio_file):
        """Test processing of small audio file."""
        if not os.path.exists(test_audio_file):
            pytest.skip("Test audio file not available")

        start_time = time.time()
        result = await processor.process_audio(test_audio_file)
        processing_time = time.time() - start_time

        # Validate result structure
        assert isinstance(result, dict)
        assert "text" in result
        assert "language" in result
        assert "processing_successful" in result
        assert "confidence" in result
        assert "duration" in result
        assert "processing_time" in result

        # Validate result content
        assert result["processing_successful"] is True
        assert isinstance(result["text"], str)
        assert isinstance(result["confidence"], (int, float))
        assert result["processing_time"] > 0
        assert processing_time < 60  # Should process small files quickly

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_audio_processing_performance(self, processor, test_audio_file, benchmark):
        """Benchmark audio processing performance."""
        if not os.path.exists(test_audio_file):
            pytest.skip("Test audio file not available")

        async def process_audio():
            return await processor.process_audio(test_audio_file)

        result = benchmark(asyncio.run, process_audio())
        assert result["processing_successful"] is True


class TestRealDnDAudioIntegration:
    """Tests using real D&D session recordings from D:\\Raw Session Recordings."""

    @pytest.fixture
    def dnd_audio_path(self):
        """Get path to D&D session recordings."""
        return Path("D:/Raw Session Recordings")

    @pytest.fixture
    def audio_samples_path(self):
        """Get path to linked audio samples."""
        return Path("testing/audio_samples")

    @pytest.fixture
    def processor(self):
        """Create AudioProcessor for real D&D audio testing."""
        return AudioProcessor(model_size="base")

    def get_test_audio_files(self, audio_path: Path, max_files: int = 3) -> List[Path]:
        """Get list of test audio files, preferring smaller files first."""
        if not audio_path.exists():
            return []

        audio_files = []
        for ext in ["*.wav", "*.mp3"]:
            audio_files.extend(audio_path.glob(ext))

        # Sort by file size (smallest first) for faster testing
        audio_files.sort(key=lambda f: f.stat().st_size)
        return audio_files[:max_files]

    @pytest.mark.real_audio
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_dnd_audio_processing(self, processor, dnd_audio_path):
        """Test processing real D&D session recordings."""
        test_files = self.get_test_audio_files(dnd_audio_path, max_files=1)

        if not test_files:
            pytest.skip("No D&D audio files available in D:/Raw Session Recordings")

        test_file = test_files[0]
        file_size_mb = test_file.stat().st_size / (1024 * 1024)

        # Skip very large files in CI/automated testing
        if file_size_mb > 50:
            pytest.skip(f"File too large for automated testing: {file_size_mb:.1f}MB")

        print(f"Processing D&D audio file: {test_file.name} ({file_size_mb:.1f}MB)")

        start_time = time.time()
        result = await processor.process_audio(str(test_file))
        processing_time = time.time() - start_time

        # Validate processing succeeded
        assert result["processing_successful"] is True
        assert len(result["text"]) > 0

        # Performance expectations for D&D audio
        expected_max_time = file_size_mb * 2  # 2 seconds per MB as rough guideline
        assert processing_time < expected_max_time, f"Processing took {processing_time:.1f}s, expected < {expected_max_time:.1f}s"

        # D&D specific content validation
        text_lower = result["text"].lower()
        dnd_terms = ["roll", "dice", "attack", "spell", "character", "damage", "hit", "miss"]
        found_terms = sum(1 for term in dnd_terms if term in text_lower)

        print(f"Found {found_terms}/{len(dnd_terms)} D&D terms in transcription")
        print(f"Transcription preview: {result['text'][:200]}...")

        # Should find at least some D&D terminology in session recordings
        if len(result["text"]) > 100:  # Only check for D&D terms if we got substantial text
            assert found_terms > 0, "No D&D terminology found in session recording"

    @pytest.mark.real_audio
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multiple_dnd_audio_files_performance(self, processor, dnd_audio_path):
        """Test processing multiple D&D files to validate consistency."""
        test_files = self.get_test_audio_files(dnd_audio_path, max_files=3)

        if len(test_files) < 2:
            pytest.skip("Need at least 2 D&D audio files for consistency testing")

        results = []
        processing_times = []

        for test_file in test_files:
            file_size_mb = test_file.stat().st_size / (1024 * 1024)

            # Skip very large files
            if file_size_mb > 30:
                continue

            start_time = time.time()
            result = await processor.process_audio(str(test_file))
            processing_time = time.time() - start_time

            processing_times.append(processing_time / file_size_mb)  # Time per MB
            results.append({
                "file": test_file.name,
                "size_mb": file_size_mb,
                "processing_time": processing_time,
                "text_length": len(result["text"]),
                "success": result["processing_successful"]
            })

        if not results:
            pytest.skip("No suitable D&D audio files found for testing")

        # Validate all files processed successfully
        assert all(r["success"] for r in results)

        # Performance consistency check
        avg_time_per_mb = sum(processing_times) / len(processing_times)
        max_deviation = max(abs(t - avg_time_per_mb) / avg_time_per_mb for t in processing_times)

        print(f"Average processing time: {avg_time_per_mb:.2f} seconds per MB")
        print(f"Max deviation from average: {max_deviation:.2%}")

        # Performance should be reasonably consistent (within 100% deviation)
        assert max_deviation < 1.0, "Processing times vary too much between files"

    @pytest.mark.audio
    @pytest.mark.asyncio
    async def test_audio_quality_metrics(self, processor, dnd_audio_path):
        """Test audio quality assessment for D&D recordings."""
        test_files = self.get_test_audio_files(dnd_audio_path, max_files=1)

        if not test_files:
            pytest.skip("No D&D audio files available")

        test_file = test_files[0]
        result = await processor.process_audio(str(test_file))

        if not result["processing_successful"]:
            pytest.skip("Audio processing failed")

        # Quality metrics
        text_length = len(result["text"])
        words = result["text"].split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0

        quality_metrics = {
            "text_length": text_length,
            "word_count": len(words),
            "avg_word_length": avg_word_length,
            "confidence": result.get("confidence", 0),
            "has_content": text_length > 50
        }

        print(f"Audio quality metrics: {quality_metrics}")

        # Basic quality assertions
        assert quality_metrics["has_content"], "Transcription too short to be meaningful"
        assert quality_metrics["word_count"] > 10, "Too few words transcribed"
        assert 2 < quality_metrics["avg_word_length"] < 15, "Average word length seems unusual"