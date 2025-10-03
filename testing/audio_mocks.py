"""
Mock audio processor for testing environments without FFmpeg.
This module provides a mock implementation that prevents FFmpeg-related import errors.
"""

import os
from unittest.mock import MagicMock
from typing import Dict, Any, List, Optional

class MockAudioSegment:
    """Mock AudioSegment for testing without FFmpeg."""

    def __init__(self, data=None, *args, **kwargs):
        self.data = data or b"mock_audio_data"
        self.frame_rate = 44100
        self.channels = 2
        self.sample_width = 2
        self.duration_seconds = 10.0

    @classmethod
    def from_file(cls, file, format=None, **kwargs):
        """Mock from_file method."""
        return cls()

    @classmethod
    def from_wav(cls, file):
        """Mock from_wav method."""
        return cls()

    @classmethod
    def from_mp3(cls, file):
        """Mock from_mp3 method."""
        return cls()

    def export(self, out_f, format="wav", **kwargs):
        """Mock export method."""
        if hasattr(out_f, 'write'):
            out_f.write(self.data)
        return out_f

    def __len__(self):
        return 10000  # Mock 10 second duration in milliseconds

    def __getitem__(self, key):
        return MockAudioSegment()

    def __add__(self, other):
        return MockAudioSegment()

    def set_frame_rate(self, frame_rate):
        return MockAudioSegment()

    def set_channels(self, channels):
        return MockAudioSegment()

def mock_pydub():
    """Mock pydub imports for testing."""
    import sys
    from unittest.mock import MagicMock

    # Create mock modules
    mock_pydub = MagicMock()
    mock_pydub.AudioSegment = MockAudioSegment
    mock_pydub.silence = MagicMock()
    mock_pydub.effects = MagicMock()
    mock_pydub.playback = MagicMock()

    # Add to sys.modules
    sys.modules['pydub'] = mock_pydub
    sys.modules['pydub.audio_segment'] = MagicMock()
    sys.modules['pydub.silence'] = MagicMock()
    sys.modules['pydub.effects'] = MagicMock()
    sys.modules['pydub.playback'] = MagicMock()

def mock_librosa():
    """Mock librosa imports for testing."""
    import sys
    from unittest.mock import MagicMock

    mock_librosa = MagicMock()
    mock_librosa.load.return_value = ([0.1, 0.2, 0.3], 22050)  # (audio_data, sample_rate)
    mock_librosa.stft.return_value = [[0.1 + 0.2j, 0.3 + 0.4j]]
    mock_librosa.feature = MagicMock()
    mock_librosa.feature.mfcc.return_value = [[0.1, 0.2, 0.3]]

    sys.modules['librosa'] = mock_librosa
    sys.modules['librosa.feature'] = mock_librosa.feature

def mock_soundfile():
    """Mock soundfile imports for testing."""
    import sys
    from unittest.mock import MagicMock

    mock_soundfile = MagicMock()
    mock_soundfile.read.return_value = ([0.1, 0.2, 0.3], 44100)
    mock_soundfile.write = MagicMock()

    sys.modules['soundfile'] = mock_soundfile

def mock_ffmpeg():
    """Mock ffmpeg-python imports for testing."""
    import sys
    from unittest.mock import MagicMock

    mock_ffmpeg = MagicMock()
    mock_ffmpeg.input.return_value = mock_ffmpeg
    mock_ffmpeg.output.return_value = mock_ffmpeg
    mock_ffmpeg.run.return_value = None

    sys.modules['ffmpeg'] = mock_ffmpeg

def setup_audio_mocks():
    """Set up all audio-related mocks for testing."""
    # Only mock if we're in a test environment or CI
    if os.getenv('ENVIRONMENT') == 'test' or os.getenv('CI') == 'true':
        try:
            import pydub
        except (ImportError, RuntimeError):
            # FFmpeg not available, use mocks
            mock_pydub()
            mock_librosa()
            mock_soundfile()
            mock_ffmpeg()
            return True
    return False

# Auto-setup mocks when module is imported
if __name__ != "__main__":
    setup_audio_mocks()