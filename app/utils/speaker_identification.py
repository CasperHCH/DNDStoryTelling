"""
Advanced speaker identification and diarization for D&D sessions.
Identifies different speakers (players, DM) and attributes dialogue appropriately.
"""

import asyncio
import json
import logging
import numpy as np
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Speaker:
    """Represents an identified speaker in the session."""
    speaker_id: str
    role: str  # 'dm', 'player', 'unknown'
    name: Optional[str] = None
    voice_characteristics: Dict[str, float] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.voice_characteristics is None:
            self.voice_characteristics = {}


@dataclass
class SpeechSegment:
    """Represents a segment of speech from a specific speaker."""
    start_time: float
    end_time: float
    speaker_id: str
    text: str
    confidence: float
    audio_features: Dict[str, Any] = None

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class SpeakerIdentifier:
    """Identifies and tracks different speakers in D&D audio sessions."""

    def __init__(self,
                 min_speaker_duration: float = 2.0,
                 max_speakers: int = 8,  # Typical D&D group: DM + 3-6 players
                 similarity_threshold: float = 0.75):
        self.min_speaker_duration = min_speaker_duration
        self.max_speakers = max_speakers
        self.similarity_threshold = similarity_threshold

        # Speaker tracking
        self.speakers: Dict[str, Speaker] = {}
        self.speaker_counter = 0

        # Audio analysis (would need actual audio processing libraries)
        self.use_audio_features = False
        try:
            # Check if advanced audio libraries are available
            import librosa
            import speechbrain
            self.use_audio_features = True
            logger.info("Advanced audio analysis available")
        except ImportError:
            logger.info("Using basic speaker identification without audio features")

    async def identify_speakers(self, audio_path: str, transcription_segments: List[Dict]) -> List[SpeechSegment]:
        """
        Identify speakers in audio and create attributed speech segments.

        Args:
            audio_path: Path to the audio file
            transcription_segments: Segments from Whisper with timestamps

        Returns:
            List of speech segments with speaker identification
        """
        logger.info(f"Starting speaker identification for {len(transcription_segments)} segments")

        # Convert transcription segments to our format
        segments = self._convert_transcription_segments(transcription_segments)

        if self.use_audio_features:
            # Use advanced audio analysis for speaker identification
            segments = await self._identify_with_audio_features(audio_path, segments)
        else:
            # Use pattern-based identification (fallback)
            segments = await self._identify_with_patterns(segments)

        # Apply D&D-specific speaker role classification
        segments = await self._classify_dnd_roles(segments)

        # Merge short segments from same speaker
        segments = self._merge_consecutive_segments(segments)

        logger.info(f"Identified {len(self.speakers)} unique speakers")
        return segments

    def _convert_transcription_segments(self, transcription_segments: List[Dict]) -> List[SpeechSegment]:
        """Convert Whisper segments to SpeechSegment objects."""
        segments = []

        for segment in transcription_segments:
            # Handle different segment formats
            if isinstance(segment, dict):
                start = segment.get('start', 0)
                end = segment.get('end', start + 5)  # Default 5 second duration
                text = segment.get('text', '')
                confidence = segment.get('confidence', 0.8)
            else:
                # Handle simple text segments
                start = len(segments) * 30  # Estimate 30 seconds per segment
                end = start + 30
                text = str(segment)
                confidence = 0.7

            if text.strip():  # Only process non-empty segments
                speech_segment = SpeechSegment(
                    start_time=start,
                    end_time=end,
                    speaker_id="unknown",  # Will be identified later
                    text=text.strip(),
                    confidence=confidence
                )
                segments.append(speech_segment)

        return segments

    async def _identify_with_audio_features(self, audio_path: str, segments: List[SpeechSegment]) -> List[SpeechSegment]:
        """Advanced speaker identification using audio feature analysis."""
        try:
            import librosa

            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)

            for segment in segments:
                # Extract audio features for this segment
                start_sample = int(segment.start_time * sr)
                end_sample = int(segment.end_time * sr)

                if end_sample > len(y):
                    end_sample = len(y)

                audio_chunk = y[start_sample:end_sample]

                if len(audio_chunk) > 0:
                    # Extract voice features
                    features = self._extract_voice_features(audio_chunk, sr)
                    segment.audio_features = features

                    # Match to existing speakers or create new one
                    speaker_id = await self._match_speaker_by_features(features)
                    segment.speaker_id = speaker_id
                else:
                    segment.speaker_id = self._get_fallback_speaker_id()

        except Exception as e:
            logger.warning(f"Audio feature analysis failed, using pattern fallback: {e}")
            segments = await self._identify_with_patterns(segments)

        return segments

    def _extract_voice_features(self, audio_chunk: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract voice characteristics from audio chunk."""
        try:
            import librosa

            # Extract basic audio features
            features = {}

            # Fundamental frequency (pitch)
            pitches, magnitudes = librosa.piptrack(y=audio_chunk, sr=sr)
            pitch_mean = np.mean(pitches[magnitudes > np.percentile(magnitudes, 85)])
            features['pitch_mean'] = float(pitch_mean) if not np.isnan(pitch_mean) else 0.0

            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_chunk, sr=sr)
            features['spectral_centroid'] = float(np.mean(spectral_centroids))

            # MFCC features (voice characteristics)
            mfccs = librosa.feature.mfcc(y=audio_chunk, sr=sr, n_mfcc=13)
            for i, mfcc in enumerate(mfccs):
                features[f'mfcc_{i}'] = float(np.mean(mfcc))

            # Energy/volume
            features['energy'] = float(np.mean(librosa.feature.rms(y=audio_chunk)))

            return features

        except Exception as e:
            logger.warning(f"Feature extraction failed: {e}")
            return {'pitch_mean': 0.0, 'energy': 0.0}

    async def _match_speaker_by_features(self, features: Dict[str, float]) -> str:
        """Match audio features to existing speakers or create new speaker."""
        if not features or not self.speakers:
            return self._create_new_speaker(features)

        best_match_id = None
        best_similarity = 0.0

        # Compare with existing speakers
        for speaker_id, speaker in self.speakers.items():
            if speaker.voice_characteristics:
                similarity = self._calculate_feature_similarity(features, speaker.voice_characteristics)

                if similarity > best_similarity and similarity > self.similarity_threshold:
                    best_similarity = similarity
                    best_match_id = speaker_id

        if best_match_id:
            # Update speaker characteristics with new data
            self._update_speaker_features(best_match_id, features)
            return best_match_id
        else:
            # Create new speaker
            return self._create_new_speaker(features)

    def _calculate_feature_similarity(self, features1: Dict[str, float], features2: Dict[str, float]) -> float:
        """Calculate similarity between two feature sets."""
        try:
            # Simple cosine similarity for voice features
            common_keys = set(features1.keys()) & set(features2.keys())
            if not common_keys:
                return 0.0

            vec1 = np.array([features1[key] for key in common_keys])
            vec2 = np.array([features2[key] for key in common_keys])

            # Normalize vectors
            vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
            vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

            # Calculate cosine similarity
            similarity = np.dot(vec1_norm, vec2_norm)
            return float(max(0, similarity))  # Ensure non-negative

        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0

    def _create_new_speaker(self, features: Dict[str, float] = None) -> str:
        """Create a new speaker with given features."""
        self.speaker_counter += 1
        speaker_id = f"speaker_{self.speaker_counter}"

        speaker = Speaker(
            speaker_id=speaker_id,
            role='unknown',
            voice_characteristics=features or {},
            confidence=0.8 if features else 0.5
        )

        self.speakers[speaker_id] = speaker
        return speaker_id

    def _update_speaker_features(self, speaker_id: str, new_features: Dict[str, float]):
        """Update speaker characteristics with new feature data."""
        speaker = self.speakers[speaker_id]

        if not speaker.voice_characteristics:
            speaker.voice_characteristics = new_features.copy()
        else:
            # Average with existing features
            for key, value in new_features.items():
                if key in speaker.voice_characteristics:
                    # Weighted average (new data has less weight)
                    speaker.voice_characteristics[key] = (
                        0.7 * speaker.voice_characteristics[key] + 0.3 * value
                    )
                else:
                    speaker.voice_characteristics[key] = value

    async def _identify_with_patterns(self, segments: List[SpeechSegment]) -> List[SpeechSegment]:
        """Pattern-based speaker identification using text analysis."""
        logger.info("Using pattern-based speaker identification")

        # Patterns that help identify DM vs Players
        dm_patterns = [
            # DM narration patterns
            r'\byou (see|hear|feel|notice|find)\b',
            r'\b(roll|make) a \w+ (check|save|roll)\b',
            r'\bthe \w+ (attacks?|moves?|says?)\b',
            r'\b(initiative|turn order|round \d+)\b',
            r'\b(describe|tell me|what do you)\b',
            r'\byou take \d+ (damage|points)\b',

            # Environment descriptions
            r'\bthe room is\b',
            r'\bin the distance\b',
            r'\bsuddenly\b',
            r'\bas you enter\b'
        ]

        player_patterns = [
            # Player action patterns
            r'\bi (want to|will|am going to|try to)\b',
            r'\bcan i\b',
            r'\bi cast\b',
            r'\bi attack\b',
            r'\bmy character\b',
            r'\bi rolled a\b',
            r'\bwhat\'s my\b',

            # Character speech
            r'^["\'].*["\']$',  # Quoted speech
            r'\bmy \w+ says?\b'
        ]

        current_speaker_id = None
        speaker_consistency_buffer = []

        for segment in segments:
            # Analyze text patterns
            dm_score = self._calculate_pattern_score(segment.text, dm_patterns)
            player_score = self._calculate_pattern_score(segment.text, player_patterns)

            # Determine likely speaker type
            if dm_score > player_score and dm_score > 0.3:
                suggested_role = 'dm'
            elif player_score > 0.2:
                suggested_role = 'player'
            else:
                suggested_role = 'unknown'

            # Find or create appropriate speaker
            speaker_id = self._find_or_create_speaker_by_role(suggested_role, segment.text)
            segment.speaker_id = speaker_id

            # Track speaker consistency
            speaker_consistency_buffer.append(speaker_id)
            if len(speaker_consistency_buffer) > 5:
                speaker_consistency_buffer.pop(0)

            # If speaker changes too frequently, smooth it out
            if len(set(speaker_consistency_buffer)) > 3:
                # Use most common speaker from recent segments
                from collections import Counter
                most_common = Counter(speaker_consistency_buffer).most_common(1)[0][0]
                segment.speaker_id = most_common

        return segments

    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> float:
        """Calculate how well text matches given patterns."""
        import re

        text_lower = text.lower()
        matches = 0

        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches += 1

        return matches / len(patterns) if patterns else 0.0

    def _find_or_create_speaker_by_role(self, role: str, text: str) -> str:
        """Find existing speaker with role or create new one."""
        # Look for existing speaker with this role
        for speaker_id, speaker in self.speakers.items():
            if speaker.role == role:
                return speaker_id

        # Create new speaker with this role
        speaker_id = self._create_new_speaker()
        self.speakers[speaker_id].role = role

        # Try to infer name from text for players
        if role == 'player':
            name = self._infer_character_name(text)
            if name:
                self.speakers[speaker_id].name = name
        elif role == 'dm':
            self.speakers[speaker_id].name = "Dungeon Master"

        return speaker_id

    def _infer_character_name(self, text: str) -> Optional[str]:
        """Try to infer character name from player speech."""
        import re

        # Look for "I'm [Name]" or "My name is [Name]" patterns
        name_patterns = [
            r"i'?m (\w+)",
            r"my name is (\w+)",
            r"call me (\w+)",
            r"(\w+) says?",
            r"my character (\w+)"
        ]

        text_lower = text.lower()
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                name = match.group(1).capitalize()
                # Filter out common words that aren't names
                if name not in ['The', 'A', 'An', 'This', 'That', 'You', 'I', 'We', 'They']:
                    return name

        return None

    def _get_fallback_speaker_id(self) -> str:
        """Get a fallback speaker ID when identification fails."""
        if not self.speakers:
            return self._create_new_speaker()

        # Return the most recently used speaker
        return max(self.speakers.keys(), key=lambda x: self.speaker_counter)

    async def _classify_dnd_roles(self, segments: List[SpeechSegment]) -> List[SpeechSegment]:
        """Apply D&D-specific role classification to identified speakers."""

        # Analyze speech patterns to refine role identification
        for speaker_id, speaker in self.speakers.items():
            speaker_segments = [s for s in segments if s.speaker_id == speaker_id]

            if not speaker_segments:
                continue

            # Analyze combined text from this speaker
            all_text = " ".join(s.text for s in speaker_segments)

            # Calculate role confidence based on content
            dm_indicators = self._count_dm_indicators(all_text)
            player_indicators = self._count_player_indicators(all_text)

            # Update role based on stronger indicators
            if dm_indicators > player_indicators * 2:
                speaker.role = 'dm'
                speaker.confidence = min(0.95, 0.6 + dm_indicators * 0.05)
            elif player_indicators > dm_indicators:
                speaker.role = 'player'
                speaker.confidence = min(0.9, 0.5 + player_indicators * 0.05)
            else:
                speaker.role = 'unknown'
                speaker.confidence = 0.3

        return segments

    def _count_dm_indicators(self, text: str) -> int:
        """Count indicators that suggest DM speech."""
        dm_keywords = [
            'roll', 'initiative', 'damage', 'save', 'check', 'perception', 'investigation',
            'monster', 'creature', 'npc', 'villager', 'guard', 'shopkeeper',
            'room', 'door', 'corridor', 'chamber', 'dungeon', 'forest', 'town',
            'suddenly', 'you see', 'you hear', 'you notice', 'you find',
            'make a', 'roll a', 'give me', 'everyone roll'
        ]

        text_lower = text.lower()
        return sum(1 for keyword in dm_keywords if keyword in text_lower)

    def _count_player_indicators(self, text: str) -> int:
        """Count indicators that suggest player speech."""
        player_keywords = [
            'i cast', 'i attack', 'i move', 'i want to', 'can i', 'my character',
            'i rolled', 'my spell', 'my weapon', 'my turn', 'i use',
            'hello', 'thank you', 'excuse me', 'pardon me',  # Character dialogue
            'what do you', 'where are', 'how much', 'who is'  # Player questions
        ]

        text_lower = text.lower()
        return sum(1 for keyword in player_keywords if keyword in text_lower)

    def _merge_consecutive_segments(self, segments: List[SpeechSegment]) -> List[SpeechSegment]:
        """Merge consecutive segments from the same speaker."""
        if not segments:
            return segments

        merged = []
        current_segment = segments[0]

        for next_segment in segments[1:]:
            # Check if segments can be merged
            if (current_segment.speaker_id == next_segment.speaker_id and
                next_segment.start_time - current_segment.end_time < 3.0):  # Max 3 second gap

                # Merge segments
                current_segment = SpeechSegment(
                    start_time=current_segment.start_time,
                    end_time=next_segment.end_time,
                    speaker_id=current_segment.speaker_id,
                    text=current_segment.text + " " + next_segment.text,
                    confidence=(current_segment.confidence + next_segment.confidence) / 2,
                    audio_features=current_segment.audio_features
                )
            else:
                # Can't merge, add current and start new
                merged.append(current_segment)
                current_segment = next_segment

        # Add the last segment
        merged.append(current_segment)

        return merged

    def get_speaker_summary(self) -> Dict[str, Any]:
        """Get summary of identified speakers."""
        summary = {
            'total_speakers': len(self.speakers),
            'speakers': {},
            'session_info': {
                'dm_identified': any(s.role == 'dm' for s in self.speakers.values()),
                'player_count': sum(1 for s in self.speakers.values() if s.role == 'player'),
                'unknown_speakers': sum(1 for s in self.speakers.values() if s.role == 'unknown')
            }
        }

        for speaker_id, speaker in self.speakers.items():
            summary['speakers'][speaker_id] = {
                'role': speaker.role,
                'name': speaker.name,
                'confidence': speaker.confidence,
                'has_voice_features': bool(speaker.voice_characteristics)
            }

        return summary


class DNDTranscriptionProcessor:
    """Processes D&D session transcriptions with speaker identification."""

    def __init__(self):
        self.speaker_identifier = SpeakerIdentifier()

    async def process_dnd_session(self, audio_path: str, transcription_segments: List[Dict]) -> Dict[str, Any]:
        """Process a complete D&D session with speaker identification."""
        start_time = time.time()

        logger.info("Processing D&D session with speaker identification")

        # Identify speakers in the transcription
        speech_segments = await self.speaker_identifier.identify_speakers(audio_path, transcription_segments)

        # Format results for D&D context
        formatted_transcription = self._format_dnd_transcription(speech_segments)

        # Generate session summary
        session_summary = self._generate_session_summary(speech_segments)

        processing_time = time.time() - start_time

        return {
            'transcription': formatted_transcription,
            'speech_segments': [
                {
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'speaker_id': seg.speaker_id,
                    'speaker_role': self.speaker_identifier.speakers.get(seg.speaker_id, Speaker('unknown', 'unknown')).role,
                    'speaker_name': self.speaker_identifier.speakers.get(seg.speaker_id, Speaker('unknown', 'unknown')).name,
                    'text': seg.text,
                    'confidence': seg.confidence
                }
                for seg in speech_segments
            ],
            'speaker_summary': self.speaker_identifier.get_speaker_summary(),
            'session_summary': session_summary,
            'processing_time': processing_time
        }

    def _format_dnd_transcription(self, segments: List[SpeechSegment]) -> str:
        """Format speech segments as a readable D&D session transcript."""
        formatted_lines = []

        for segment in segments:
            speaker = self.speaker_identifier.speakers.get(segment.speaker_id)

            # Determine speaker label
            if speaker and speaker.name:
                speaker_label = speaker.name
            elif speaker and speaker.role == 'dm':
                speaker_label = "DM"
            elif speaker and speaker.role == 'player':
                speaker_label = f"Player {segment.speaker_id}"
            else:
                speaker_label = f"Speaker {segment.speaker_id}"

            # Format timestamp
            minutes = int(segment.start_time // 60)
            seconds = int(segment.start_time % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            # Format the line
            formatted_line = f"{timestamp} {speaker_label}: {segment.text}"
            formatted_lines.append(formatted_line)

        return "\n".join(formatted_lines)

    def _generate_session_summary(self, segments: List[SpeechSegment]) -> Dict[str, Any]:
        """Generate a summary of the D&D session."""
        total_duration = max(seg.end_time for seg in segments) if segments else 0

        # Calculate speaking time per role
        speaking_time = {'dm': 0, 'player': 0, 'unknown': 0}

        for segment in segments:
            speaker = self.speaker_identifier.speakers.get(segment.speaker_id)
            role = speaker.role if speaker else 'unknown'
            speaking_time[role] += segment.duration

        # Count dialogue vs narration
        dialogue_segments = []
        narration_segments = []

        for segment in segments:
            speaker = self.speaker_identifier.speakers.get(segment.speaker_id)
            if speaker and speaker.role == 'dm':
                narration_segments.append(segment)
            else:
                dialogue_segments.append(segment)

        return {
            'total_duration_minutes': total_duration / 60,
            'speaker_distribution': {
                'dm_time_percent': (speaking_time['dm'] / total_duration * 100) if total_duration > 0 else 0,
                'player_time_percent': (speaking_time['player'] / total_duration * 100) if total_duration > 0 else 0,
                'unknown_time_percent': (speaking_time['unknown'] / total_duration * 100) if total_duration > 0 else 0
            },
            'content_breakdown': {
                'dialogue_segments': len(dialogue_segments),
                'narration_segments': len(narration_segments),
                'total_segments': len(segments)
            },
            'estimated_participants': len([s for s in self.speaker_identifier.speakers.values() if s.role in ['dm', 'player']])
        }

    async def map_speakers_to_characters(self, speakers: Dict[str, Any], character_names: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Map identified speakers to D&D character names.

        Args:
            speakers: Dictionary of speaker information
            character_names: Optional list of known character names

        Returns:
            Mapping of speaker IDs to character names
        """
        speaker_mapping = {}

        for speaker_id, speaker_info in speakers.items():
            if isinstance(speaker_info, dict):
                role = speaker_info.get('role', 'unknown')
                name = speaker_info.get('name')
            else:
                # Handle Speaker object
                role = getattr(speaker_info, 'role', 'unknown')
                name = getattr(speaker_info, 'name', None)

            if role == 'dm':
                speaker_mapping[speaker_id] = name or "Dungeon Master"
            elif role == 'player':
                if name:
                    speaker_mapping[speaker_id] = name
                elif character_names:
                    # Try to assign available character names
                    assigned_names = set(speaker_mapping.values())
                    available_names = [n for n in character_names if n not in assigned_names]
                    if available_names:
                        speaker_mapping[speaker_id] = available_names[0]
                    else:
                        speaker_mapping[speaker_id] = f"Player {speaker_id}"
                else:
                    speaker_mapping[speaker_id] = f"Player {speaker_id}"
            else:
                speaker_mapping[speaker_id] = f"Unknown Speaker {speaker_id}"

        return speaker_mapping

    async def process_dnd_transcription(self, transcription: str, speaker_mapping: Optional[Dict[str, str]] = None) -> str:
        """
        Process a D&D transcription with speaker identification and formatting.

        Args:
            transcription: Raw transcription text
            speaker_mapping: Optional mapping of speaker IDs to names

        Returns:
            Formatted D&D transcription
        """
        if not transcription:
            return ""

        # If we have a simple string transcription, enhance it with basic D&D formatting
        if speaker_mapping:
            # Apply speaker mapping to improve readability
            formatted_transcription = transcription
            for speaker_id, character_name in speaker_mapping.items():
                # Replace generic speaker labels with character names
                formatted_transcription = formatted_transcription.replace(
                    f"Speaker {speaker_id}", character_name
                )
                formatted_transcription = formatted_transcription.replace(
                    f"speaker_{speaker_id}", character_name
                )
        else:
            formatted_transcription = transcription

        # Add basic D&D formatting
        lines = formatted_transcription.split('\n')
        enhanced_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Add formatting for common D&D elements
            if any(keyword in line.lower() for keyword in ['rolls', 'roll a', 'rolled']):
                line = f"🎲 {line}"
            elif any(keyword in line.lower() for keyword in ['damage', 'takes', 'hp']):
                line = f"⚔️ {line}"
            elif any(keyword in line.lower() for keyword in ['casts', 'spell', 'magic']):
                line = f"✨ {line}"

            enhanced_lines.append(line)

        return '\n'.join(enhanced_lines)


# Global instances for easy access from production integrations
speaker_identifier = SpeakerIdentifier()
transcription_processor = DNDTranscriptionProcessor()

# Alias for backward compatibility and clearer naming in production integration
dnd_processor = transcription_processor


# Global instance
dnd_transcription_processor = DNDTranscriptionProcessor()