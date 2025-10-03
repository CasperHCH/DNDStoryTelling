"""
Test configuration for handling missing dependencies in CI/CD environments.
"""

import os
import pytest

def pytest_configure():
    """Configure pytest with appropriate markers and settings."""
    # Add custom markers
    pytest.mark.audio = pytest.mark.skipif(
        not _check_audio_available(),
        reason="Audio processing dependencies not available"
    )

    pytest.mark.requires_ffmpeg = pytest.mark.skipif(
        not _check_ffmpeg_available(),
        reason="FFmpeg not available"
    )

def _check_audio_available():
    """Check if audio processing dependencies are available."""
    try:
        from pydub import AudioSegment
        return True
    except (ImportError, RuntimeError):
        return False

def _check_ffmpeg_available():
    """Check if FFmpeg is available."""
    import shutil
    return shutil.which("ffmpeg") is not None

# Environment-specific configuration
if os.getenv('CI') == 'true' or os.getenv('ENVIRONMENT') == 'test':
    # In CI or test environment, configure for minimal dependencies
    os.environ.setdefault('SKIP_AUDIO_TESTS', 'true')
    os.environ.setdefault('MOCK_AUDIO_PROCESSING', 'true')