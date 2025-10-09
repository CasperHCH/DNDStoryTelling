"""
Comprehensive audio quality validation and preprocessing for D&D sessions.
Ensures optimal audio quality for transcription and story generation.
"""

import asyncio
import json
import logging
import math
import os
import subprocess
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import numpy as np
from app.utils.monitoring import performance_metrics, alert_manager

logger = logging.getLogger(__name__)


class AudioQuality(Enum):
    """Audio quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class AudioIssue(Enum):
    """Types of audio issues that can be detected."""
    LOW_VOLUME = "low_volume"
    HIGH_NOISE = "high_noise"
    CLIPPING = "clipping"
    SILENCE_PERIODS = "silence_periods"
    ECHO_REVERB = "echo_reverb"
    COMPRESSION_ARTIFACTS = "compression_artifacts"
    FREQUENCY_ISSUES = "frequency_issues"
    SAMPLE_RATE_ISSUES = "sample_rate_issues"
    MONO_RECORDING = "mono_recording"
    BIT_DEPTH_LOW = "bit_depth_low"


@dataclass
class AudioMetrics:
    """Comprehensive audio quality metrics."""

    # Basic properties
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int
    file_size_mb: float

    # Volume metrics
    rms_level: float
    peak_level: float
    dynamic_range: float

    # Noise metrics
    noise_floor: float
    snr_estimate: float

    # Quality indicators
    clipping_percentage: float
    silence_percentage: float

    # Frequency analysis
    frequency_response: Dict[str, float]
    spectral_centroid: float

    # Overall assessment
    quality_score: float
    quality_level: AudioQuality
    detected_issues: List[AudioIssue]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['quality_level'] = self.quality_level.value
        result['detected_issues'] = [issue.value for issue in self.detected_issues]
        return result


@dataclass
class PreprocessingAction:
    """Audio preprocessing action."""
    action_type: str
    description: str
    parameters: Dict[str, Any]
    estimated_improvement: float
    required: bool = False


class AudioQualityAnalyzer:
    """Analyzes audio quality and identifies issues."""

    def __init__(self):
        self.min_sample_rate = 16000  # Minimum for good transcription
        self.optimal_sample_rate = 44100
        self.min_bit_depth = 16
        self.min_duration = 1.0  # seconds
        self.max_silence_percentage = 30.0
        self.min_snr = 10.0  # dB
        self.max_clipping_percentage = 1.0

        # Quality thresholds
        self.quality_thresholds = {
            AudioQuality.EXCELLENT: 0.9,
            AudioQuality.GOOD: 0.75,
            AudioQuality.FAIR: 0.6,
            AudioQuality.POOR: 0.4,
            AudioQuality.UNACCEPTABLE: 0.0
        }

    async def analyze_audio_quality(self, file_path: Path) -> AudioMetrics:
        """Perform comprehensive audio quality analysis."""

        logger.info(f"Analyzing audio quality for {file_path.name}")

        try:
            # Get basic audio information
            basic_info = await self._get_basic_audio_info(file_path)

            # Load audio data for analysis
            audio_data, sample_rate = await self._load_audio_safely(file_path)

            if audio_data is None:
                return self._create_failed_metrics(file_path, "Failed to load audio")

            # Perform detailed analysis
            volume_metrics = self._analyze_volume(audio_data)
            noise_metrics = self._analyze_noise(audio_data, sample_rate)
            quality_issues = self._detect_quality_issues(audio_data, sample_rate, basic_info)
            frequency_metrics = self._analyze_frequency_response(audio_data, sample_rate)

            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                volume_metrics, noise_metrics, quality_issues, basic_info
            )

            # Determine quality level
            quality_level = self._determine_quality_level(quality_score)

            # Create comprehensive metrics
            metrics = AudioMetrics(
                duration_seconds=basic_info['duration'],
                sample_rate=basic_info['sample_rate'],
                channels=basic_info['channels'],
                bit_depth=basic_info['bit_depth'],
                file_size_mb=basic_info['file_size_mb'],
                rms_level=volume_metrics['rms_level'],
                peak_level=volume_metrics['peak_level'],
                dynamic_range=volume_metrics['dynamic_range'],
                noise_floor=noise_metrics['noise_floor'],
                snr_estimate=noise_metrics['snr_estimate'],
                clipping_percentage=quality_issues['clipping_percentage'],
                silence_percentage=quality_issues['silence_percentage'],
                frequency_response=frequency_metrics['frequency_response'],
                spectral_centroid=frequency_metrics['spectral_centroid'],
                quality_score=quality_score,
                quality_level=quality_level,
                detected_issues=quality_issues['detected_issues']
            )

            logger.info(f"Audio quality analysis complete: {quality_level.value} (score: {quality_score:.2f})")

            # Record metrics
            performance_metrics.record_function_call("audio_quality_analysis", 1)
            performance_metrics.record_function_call(f"audio_quality_{quality_level.value}", 1)

            return metrics

        except Exception as e:
            logger.error(f"Audio quality analysis failed for {file_path}: {e}")
            return self._create_failed_metrics(file_path, str(e))

    async def _get_basic_audio_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic audio file information using ffprobe."""

        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
                str(file_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")

            probe_data = json.loads(result.stdout)

            # Extract audio stream info
            audio_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break

            if not audio_stream:
                raise ValueError("No audio stream found")

            # Get file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            return {
                'duration': float(audio_stream.get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 1)),
                'bit_depth': int(audio_stream.get('bits_per_sample', 16)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else None,
                'file_size_mb': file_size_mb
            }

        except Exception as e:
            logger.error(f"Failed to get basic audio info: {e}")
            return {
                'duration': 0,
                'sample_rate': 0,
                'channels': 1,
                'bit_depth': 16,
                'codec': 'unknown',
                'bitrate': None,
                'file_size_mb': 0
            }

    async def _load_audio_safely(self, file_path: Path) -> Tuple[Optional[np.ndarray], int]:
        """Safely load audio data for analysis."""

        try:
            # Try librosa first (best for audio analysis)
            try:
                import librosa
                audio_data, sample_rate = librosa.load(str(file_path), sr=None, mono=False)

                # Ensure we have a 1D array for mono or take first channel for stereo
                if len(audio_data.shape) > 1:
                    audio_data = audio_data[0]  # Take first channel

                return audio_data, sample_rate

            except ImportError:
                logger.debug("librosa not available, using scipy")

                # Fallback to scipy
                try:
                    from scipy.io import wavfile
                    sample_rate, audio_data = wavfile.read(str(file_path))

                    # Normalize to [-1, 1] range
                    if audio_data.dtype == np.int16:
                        audio_data = audio_data.astype(np.float32) / 32768.0
                    elif audio_data.dtype == np.int32:
                        audio_data = audio_data.astype(np.float32) / 2147483648.0

                    # Handle stereo
                    if len(audio_data.shape) > 1:
                        audio_data = audio_data[:, 0]  # Take first channel

                    return audio_data, sample_rate

                except ImportError:
                    logger.warning("Neither librosa nor scipy available for audio loading")

                    # Last resort: use ffmpeg to convert to WAV and read raw
                    return await self._load_audio_with_ffmpeg(file_path)

        except Exception as e:
            logger.error(f"Failed to load audio data: {e}")
            return None, 0

    async def _load_audio_with_ffmpeg(self, file_path: Path) -> Tuple[Optional[np.ndarray], int]:
        """Load audio using ffmpeg as a last resort."""

        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

            # Convert to WAV using ffmpeg
            cmd = [
                'ffmpeg', '-i', str(file_path), '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1',
                '-y', temp_path
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=60)

            if result.returncode != 0:
                return None, 0

            # Read the converted WAV file
            try:
                import wave
                with wave.open(temp_path, 'rb') as wav_file:
                    frames = wav_file.readframes(-1)
                    sample_rate = wav_file.getframerate()

                    # Convert to numpy array
                    audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

                    return audio_data, sample_rate

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"FFmpeg audio loading failed: {e}")
            return None, 0

    def _analyze_volume(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Analyze volume characteristics."""

        # RMS (Root Mean Square) level
        rms_level = np.sqrt(np.mean(audio_data ** 2))

        # Peak level
        peak_level = np.max(np.abs(audio_data))

        # Dynamic range (difference between loudest and average)
        if rms_level > 0:
            dynamic_range = 20 * np.log10(peak_level / rms_level)
        else:
            dynamic_range = 0

        return {
            'rms_level': float(rms_level),
            'peak_level': float(peak_level),
            'dynamic_range': float(dynamic_range)
        }

    def _analyze_noise(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze noise characteristics."""

        # Estimate noise floor from quietest segments
        windowed_rms = self._calculate_windowed_rms(audio_data, sample_rate, window_seconds=0.1)
        noise_floor = np.percentile(windowed_rms, 10)  # 10th percentile as noise floor

        # Signal-to-Noise Ratio estimate
        signal_level = np.percentile(windowed_rms, 90)  # 90th percentile as signal level

        if noise_floor > 0:
            snr_estimate = 20 * np.log10(signal_level / noise_floor)
        else:
            snr_estimate = float('inf')

        return {
            'noise_floor': float(noise_floor),
            'snr_estimate': float(snr_estimate) if snr_estimate != float('inf') else 100.0
        }

    def _calculate_windowed_rms(self, audio_data: np.ndarray, sample_rate: int, window_seconds: float = 0.1) -> np.ndarray:
        """Calculate RMS in sliding windows."""

        window_samples = int(sample_rate * window_seconds)
        hop_samples = window_samples // 2

        rms_values = []

        for i in range(0, len(audio_data) - window_samples, hop_samples):
            window = audio_data[i:i + window_samples]
            rms = np.sqrt(np.mean(window ** 2))
            rms_values.append(rms)

        return np.array(rms_values)

    def _detect_quality_issues(self, audio_data: np.ndarray, sample_rate: int, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect various audio quality issues."""

        detected_issues = []

        # Clipping detection
        clipping_threshold = 0.99
        clipped_samples = np.sum(np.abs(audio_data) >= clipping_threshold)
        clipping_percentage = (clipped_samples / len(audio_data)) * 100

        if clipping_percentage > self.max_clipping_percentage:
            detected_issues.append(AudioIssue.CLIPPING)

        # Silence detection
        silence_threshold = 0.01
        silent_samples = np.sum(np.abs(audio_data) < silence_threshold)
        silence_percentage = (silent_samples / len(audio_data)) * 100

        if silence_percentage > self.max_silence_percentage:
            detected_issues.append(AudioIssue.SILENCE_PERIODS)

        # Low volume detection
        rms_level = np.sqrt(np.mean(audio_data ** 2))
        if rms_level < 0.1:  # Very quiet
            detected_issues.append(AudioIssue.LOW_VOLUME)

        # Sample rate issues
        if basic_info['sample_rate'] < self.min_sample_rate:
            detected_issues.append(AudioIssue.SAMPLE_RATE_ISSUES)

        # Bit depth issues
        if basic_info['bit_depth'] < self.min_bit_depth:
            detected_issues.append(AudioIssue.BIT_DEPTH_LOW)

        # Mono recording (for D&D sessions, stereo is often better)
        if basic_info['channels'] < 2:
            detected_issues.append(AudioIssue.MONO_RECORDING)

        return {
            'clipping_percentage': float(clipping_percentage),
            'silence_percentage': float(silence_percentage),
            'detected_issues': detected_issues
        }

    def _analyze_frequency_response(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Analyze frequency characteristics."""

        try:
            # FFT analysis
            fft = np.fft.rfft(audio_data)
            magnitude = np.abs(fft)
            frequencies = np.fft.rfftfreq(len(audio_data), 1/sample_rate)

            # Frequency band analysis
            frequency_bands = {
                'sub_bass': (20, 60),
                'bass': (60, 250),
                'low_mid': (250, 500),
                'mid': (500, 2000),
                'high_mid': (2000, 4000),
                'presence': (4000, 6000),
                'brilliance': (6000, 20000)
            }

            frequency_response = {}

            for band_name, (low_freq, high_freq) in frequency_bands.items():
                # Find indices for this frequency range
                low_idx = np.searchsorted(frequencies, low_freq)
                high_idx = np.searchsorted(frequencies, high_freq)

                if high_idx > low_idx:
                    # Average magnitude in this band
                    band_magnitude = np.mean(magnitude[low_idx:high_idx])
                    frequency_response[band_name] = float(band_magnitude)
                else:
                    frequency_response[band_name] = 0.0

            # Spectral centroid (brightness measure)
            if np.sum(magnitude) > 0:
                spectral_centroid = np.sum(frequencies * magnitude) / np.sum(magnitude)
            else:
                spectral_centroid = 0.0

            return {
                'frequency_response': frequency_response,
                'spectral_centroid': float(spectral_centroid)
            }

        except Exception as e:
            logger.warning(f"Frequency analysis failed: {e}")
            return {
                'frequency_response': {},
                'spectral_centroid': 0.0
            }

    def _calculate_quality_score(self, volume_metrics: Dict, noise_metrics: Dict, quality_issues: Dict, basic_info: Dict) -> float:
        """Calculate overall quality score (0-1)."""

        score = 1.0

        # Volume scoring
        rms_level = volume_metrics['rms_level']
        if rms_level < 0.1:  # Too quiet
            score -= 0.3
        elif rms_level > 0.8:  # Too loud (potential clipping)
            score -= 0.2

        # Dynamic range scoring
        dynamic_range = volume_metrics['dynamic_range']
        if dynamic_range < 10:  # Compressed/limited
            score -= 0.2
        elif dynamic_range > 40:  # Excellent dynamic range
            score += 0.1

        # Noise scoring
        snr = noise_metrics['snr_estimate']
        if snr < 10:  # High noise
            score -= 0.4
        elif snr < 20:  # Moderate noise
            score -= 0.2
        elif snr > 40:  # Excellent SNR
            score += 0.1

        # Clipping penalty
        clipping_percentage = quality_issues['clipping_percentage']
        score -= min(0.5, clipping_percentage / 100.0 * 5)  # Heavy penalty for clipping

        # Silence penalty
        silence_percentage = quality_issues['silence_percentage']
        if silence_percentage > 50:
            score -= 0.3
        elif silence_percentage > 30:
            score -= 0.1

        # Sample rate bonus/penalty
        sample_rate = basic_info['sample_rate']
        if sample_rate >= 44100:
            score += 0.1
        elif sample_rate < 16000:
            score -= 0.3

        # Bit depth penalty
        bit_depth = basic_info['bit_depth']
        if bit_depth < 16:
            score -= 0.2

        # Channel bonus (stereo is better for D&D)
        if basic_info['channels'] >= 2:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _determine_quality_level(self, quality_score: float) -> AudioQuality:
        """Determine quality level from score."""

        for quality_level, threshold in self.quality_thresholds.items():
            if quality_score >= threshold:
                return quality_level

        return AudioQuality.UNACCEPTABLE

    def _create_failed_metrics(self, file_path: Path, error_message: str) -> AudioMetrics:
        """Create metrics object for failed analysis."""

        return AudioMetrics(
            duration_seconds=0,
            sample_rate=0,
            channels=1,
            bit_depth=16,
            file_size_mb=0,
            rms_level=0,
            peak_level=0,
            dynamic_range=0,
            noise_floor=0,
            snr_estimate=0,
            clipping_percentage=100,
            silence_percentage=100,
            frequency_response={},
            spectral_centroid=0,
            quality_score=0,
            quality_level=AudioQuality.UNACCEPTABLE,
            detected_issues=[AudioIssue.COMPRESSION_ARTIFACTS]  # Generic issue
        )


class AudioPreprocessor:
    """Provides audio preprocessing and enhancement."""

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "audio_preprocessing"
        self.temp_dir.mkdir(exist_ok=True)

    async def suggest_preprocessing_actions(self, metrics: AudioMetrics) -> List[PreprocessingAction]:
        """Suggest preprocessing actions based on quality analysis."""

        actions = []

        # Normalize audio if volume issues detected
        if AudioIssue.LOW_VOLUME in metrics.detected_issues:
            actions.append(PreprocessingAction(
                action_type="normalize",
                description="Normalize audio volume to optimal level",
                parameters={"target_rms": -20, "peak_limit": -3},
                estimated_improvement=0.3,
                required=True
            ))

        # Noise reduction if high noise detected
        if metrics.snr_estimate < 20:
            actions.append(PreprocessingAction(
                action_type="noise_reduction",
                description="Apply noise reduction to improve clarity",
                parameters={"strength": min(0.5, (20 - metrics.snr_estimate) / 20)},
                estimated_improvement=0.2
            ))

        # Sample rate conversion if needed
        if metrics.sample_rate < 16000:
            actions.append(PreprocessingAction(
                action_type="resample",
                description="Increase sample rate for better transcription",
                parameters={"target_sample_rate": 16000},
                estimated_improvement=0.4,
                required=True
            ))

        # Convert to mono if stereo with no benefit (saves processing)
        if metrics.channels > 1 and AudioIssue.MONO_RECORDING not in metrics.detected_issues:
            # Check if stereo actually provides benefit
            actions.append(PreprocessingAction(
                action_type="stereo_to_mono",
                description="Convert to mono for more efficient processing",
                parameters={"method": "mix"},
                estimated_improvement=0.1
            ))

        # Clipping repair
        if metrics.clipping_percentage > 1.0:
            actions.append(PreprocessingAction(
                action_type="declip",
                description="Attempt to repair clipped audio",
                parameters={"method": "cubic_spline"},
                estimated_improvement=0.15
            ))

        # High-pass filter for low-frequency noise
        if AudioIssue.HIGH_NOISE in metrics.detected_issues:
            actions.append(PreprocessingAction(
                action_type="high_pass_filter",
                description="Remove low-frequency noise and rumble",
                parameters={"cutoff_frequency": 80},
                estimated_improvement=0.1
            ))

        # Compression for dynamic range issues
        if metrics.dynamic_range > 50:  # Too much dynamic range
            actions.append(PreprocessingAction(
                action_type="compressor",
                description="Apply gentle compression to reduce dynamic range",
                parameters={"ratio": 3.0, "threshold": -20, "attack": 10, "release": 100},
                estimated_improvement=0.2
            ))

        return actions

    async def apply_preprocessing(self, input_path: Path, actions: List[PreprocessingAction]) -> Tuple[Path, bool]:
        """Apply preprocessing actions to audio file."""

        if not actions:
            return input_path, True

        try:
            # Create output filename
            output_path = self.temp_dir / f"processed_{input_path.stem}_{int(datetime.now().timestamp())}{input_path.suffix}"

            # Build ffmpeg command
            ffmpeg_cmd = ['ffmpeg', '-i', str(input_path)]

            # Audio filters
            filters = []

            for action in actions:
                if action.action_type == "normalize":
                    filters.append(f"loudnorm=I=-16:TP=-1.5:LRA=11")

                elif action.action_type == "noise_reduction":
                    # Basic noise gate
                    filters.append(f"agate=threshold=0.003:ratio=10:attack=3:release=100")

                elif action.action_type == "resample":
                    target_rate = action.parameters.get("target_sample_rate", 16000)
                    ffmpeg_cmd.extend(['-ar', str(target_rate)])

                elif action.action_type == "stereo_to_mono":
                    ffmpeg_cmd.extend(['-ac', '1'])

                elif action.action_type == "declip":
                    filters.append("adeclick")

                elif action.action_type == "high_pass_filter":
                    cutoff = action.parameters.get("cutoff_frequency", 80)
                    filters.append(f"highpass=f={cutoff}")

                elif action.action_type == "compressor":
                    ratio = action.parameters.get("ratio", 3.0)
                    threshold = action.parameters.get("threshold", -20)
                    attack = action.parameters.get("attack", 10)
                    release = action.parameters.get("release", 100)
                    filters.append(f"acompressor=ratio={ratio}:threshold={threshold}dB:attack={attack}:release={release}")

            # Add filters to command
            if filters:
                ffmpeg_cmd.extend(['-af', ','.join(filters)])

            # Add output path and overwrite flag
            ffmpeg_cmd.extend(['-y', str(output_path)])

            logger.info(f"Applying audio preprocessing with {len(actions)} actions")

            # Execute ffmpeg
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.error(f"FFmpeg preprocessing failed: {result.stderr}")
                return input_path, False

            # Verify output file was created and is valid
            if not output_path.exists() or output_path.stat().st_size == 0:
                logger.error("Preprocessing produced empty or missing output file")
                return input_path, False

            logger.info(f"Audio preprocessing completed successfully: {output_path}")

            # Record success metrics
            performance_metrics.record_function_call("audio_preprocessing_success", 1)

            return output_path, True

        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            return input_path, False

    async def optimize_for_transcription(self, input_path: Path) -> Tuple[Path, AudioMetrics]:
        """Optimize audio specifically for transcription quality."""

        # First, analyze current quality
        analyzer = AudioQualityAnalyzer()
        current_metrics = await analyzer.analyze_audio_quality(input_path)

        # Get optimization actions
        actions = await self.suggest_preprocessing_actions(current_metrics)

        # Filter to transcription-critical actions
        transcription_critical = [
            action for action in actions
            if action.action_type in ["normalize", "resample", "noise_reduction", "stereo_to_mono"]
        ]

        if not transcription_critical:
            logger.info("No transcription optimization needed")
            return input_path, current_metrics

        # Apply preprocessing
        optimized_path, success = await self.apply_preprocessing(input_path, transcription_critical)

        if success and optimized_path != input_path:
            # Re-analyze to confirm improvement
            new_metrics = await analyzer.analyze_audio_quality(optimized_path)

            logger.info(f"Transcription optimization complete. Quality: {current_metrics.quality_level.value} -> {new_metrics.quality_level.value}")

            return optimized_path, new_metrics
        else:
            return input_path, current_metrics

    def cleanup_temp_files(self, keep_hours: int = 24):
        """Clean up temporary preprocessing files."""

        try:
            cutoff_time = datetime.now().timestamp() - (keep_hours * 3600)

            for temp_file in self.temp_dir.glob("processed_*"):
                if temp_file.stat().st_mtime < cutoff_time:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file.name}")

        except Exception as e:
            logger.warning(f"Temp file cleanup failed: {e}")


# Global instances
audio_analyzer = AudioQualityAnalyzer()
audio_preprocessor = AudioPreprocessor()