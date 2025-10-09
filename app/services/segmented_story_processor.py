"""
Enhanced Story Processing Base Class
Ensures ALL story generators can handle extremely large transcriptions by:
1. Automatic segmentation of large texts
2. Context preservation across segments
3. Synthesis of all segments into coherent narrative
4. Memory of entire session for story continuity
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class SegmentedStoryProcessor(ABC):
    """
    Base class for story processors that need to handle very large transcriptions.
    Automatically segments large texts and processes them comprehensively.
    """

    def __init__(self, max_segment_tokens: int = 3000, overlap_tokens: int = 200):
        """
        Initialize the segmented processor.

        Args:
            max_segment_tokens: Maximum tokens per segment (safe for all AI models)
            overlap_tokens: Tokens to overlap between segments for context continuity
        """
        self.max_segment_tokens = max_segment_tokens
        self.overlap_tokens = overlap_tokens
        self.session_memory = {
            'characters': set(),
            'locations': set(),
            'plot_points': [],
            'key_events': [],
            'ongoing_narrative': ""
        }

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters for English)
        This is conservative to ensure we stay within limits.
        """
        return len(text) // 3  # Conservative estimate

    def segment_transcription(self, text: str) -> List[Dict[str, Any]]:
        """
        Intelligently segment large transcription while preserving context.

        Returns:
            List of segments with metadata for processing
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        total_tokens = self.estimate_tokens(text)

        logger.info(f"Processing transcription: {total_tokens} estimated tokens")

        if total_tokens <= self.max_segment_tokens:
            # Small enough to process as single segment
            return [{
                'content': text,
                'segment_id': 1,
                'is_final': True,
                'total_segments': 1,
                'start_position': 0,
                'end_position': len(text)
            }]

        # Large transcription - need to segment intelligently
        segments = []

        # First, try to split on natural boundaries (sessions, encounters, etc.)
        natural_boundaries = self._find_natural_boundaries(text)

        if natural_boundaries:
            segments = self._create_segments_from_boundaries(text, natural_boundaries)
        else:
            # Fallback to paragraph-based segmentation
            segments = self._create_paragraph_segments(text)

        # Add metadata to segments
        for i, segment in enumerate(segments):
            segment.update({
                'segment_id': i + 1,
                'total_segments': len(segments),
                'is_final': i == len(segments) - 1
            })

        logger.info(f"Created {len(segments)} segments for processing")
        return segments

    def _find_natural_boundaries(self, text: str) -> List[int]:
        """Find natural breaking points in D&D transcriptions."""
        boundaries = []

        # Look for session markers
        session_patterns = [
            r'\n\s*\*\*\s*Session\s+\d+',
            r'\n\s*\*\*\s*Part\s+\d+',
            r'\n\s*---+\s*\n',
            r'\n\s*#{2,}\s*',
            r'\n\s*\*\*\s*Round\s+\d+',
            r'\n\s*\*\*\s*(Combat|Initiative|Encounter)',
            r'\n\s*\*\*\s*(Scene|Chapter|Act)\s+\d+'
        ]

        for pattern in session_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                boundaries.append(match.start())

        # Sort and deduplicate boundaries
        boundaries = sorted(set(boundaries))

        # Filter out boundaries that are too close together
        filtered_boundaries = [0]  # Always start at beginning
        for boundary in boundaries:
            if boundary - filtered_boundaries[-1] > 1000:  # At least 1000 chars apart
                filtered_boundaries.append(boundary)

        return filtered_boundaries

    def _create_segments_from_boundaries(self, text: str, boundaries: List[int]) -> List[Dict[str, Any]]:
        """Create segments based on natural boundaries."""
        segments = []

        for i in range(len(boundaries)):
            start_pos = boundaries[i]
            end_pos = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)

            segment_text = text[start_pos:end_pos].strip()

            if segment_text:
                # Check if segment is too large
                if self.estimate_tokens(segment_text) > self.max_segment_tokens:
                    # Further subdivide large segments
                    sub_segments = self._create_paragraph_segments(segment_text)
                    segments.extend(sub_segments)
                else:
                    segments.append({
                        'content': segment_text,
                        'start_position': start_pos,
                        'end_position': end_pos
                    })

        return segments

    def _create_paragraph_segments(self, text: str) -> List[Dict[str, Any]]:
        """Create segments based on paragraph breaks."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        segments = []
        current_segment = ""
        start_pos = 0

        for para in paragraphs:
            # Check if adding this paragraph would exceed token limit
            potential_segment = current_segment + "\n\n" + para if current_segment else para

            if self.estimate_tokens(potential_segment) > self.max_segment_tokens and current_segment:
                # Save current segment and start new one
                segments.append({
                    'content': current_segment.strip(),
                    'start_position': start_pos,
                    'end_position': start_pos + len(current_segment)
                })
                start_pos += len(current_segment) + 2  # +2 for \n\n
                current_segment = para
            else:
                current_segment = potential_segment

        # Add final segment
        if current_segment:
            segments.append({
                'content': current_segment.strip(),
                'start_position': start_pos,
                'end_position': start_pos + len(current_segment)
            })

        return segments

    def extract_session_elements(self, text: str) -> Dict[str, Any]:
        """Extract key elements from transcription segment for context."""
        elements = {
            'characters': set(),
            'locations': set(),
            'actions': [],
            'dialogue': [],
            'plot_points': []
        }

        # Extract character names (look for speaker patterns)
        character_patterns = [
            r'\*\*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\*\*:',  # **CharacterName**:
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):',          # CharacterName:
            r'Player\s+\d+\s*\(([^)]+)\)',                 # Player 1 (CharacterName)
        ]

        for pattern in character_patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                if len(name) > 1 and len(name) < 30:  # Reasonable name length
                    elements['characters'].add(name)

        # Extract locations
        location_patterns = [
            r'(?:in|at|near|through|entering|leaving)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Forest|Cave|Tower|Temple|City|Village|Dungeon|Keep|Castle))?)',
            r'Location:\s*([A-Z][^.\n]+)',
        ]

        for pattern in location_patterns:
            for match in re.finditer(pattern, text):
                location = match.group(1).strip()
                if len(location) > 1 and len(location) < 50:
                    elements['locations'].add(location)

        # Extract key actions and plot points
        action_indicators = ['rolls', 'attacks', 'casts', 'moves', 'investigates', 'discovers', 'finds']
        for indicator in action_indicators:
            pattern = rf'[^.\n]*{indicator}[^.\n]*'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                elements['actions'].append(match.group(0).strip())

        return elements

    async def process_full_transcription(self, text: str, context: Any) -> str:
        """
        Main method to process entire transcription, regardless of size.
        This ensures the AI reads and understands the COMPLETE session.
        """
        if not text or not text.strip():
            return "No transcription content provided."

        logger.info("Starting comprehensive transcription processing...")

        # Reset session memory for new transcription
        self.session_memory = {
            'characters': set(),
            'locations': set(),
            'plot_points': [],
            'key_events': [],
            'ongoing_narrative': ""
        }

        # Segment the transcription
        segments = self.segment_transcription(text)

        if len(segments) == 1:
            # Small transcription - process directly
            logger.info("Processing single segment transcription")
            return await self._process_single_segment(segments[0], context)

        # Large transcription - process all segments and synthesize
        logger.info(f"Processing large transcription in {len(segments)} segments")

        segment_summaries = []
        running_context = self._prepare_initial_context(context)

        for i, segment in enumerate(segments):
            logger.info(f"Processing segment {i+1}/{len(segments)}")

            # Extract elements from this segment
            elements = self.extract_session_elements(segment['content'])
            self._update_session_memory(elements)

            # Process this segment with accumulated context
            segment_summary = await self._process_segment_with_context(
                segment, running_context, elements
            )

            segment_summaries.append({
                'summary': segment_summary,
                'segment_id': segment['segment_id'],
                'elements': elements
            })

            # Update running context for next segment
            running_context = self._update_running_context(running_context, segment_summary, elements)

        # Synthesize all segments into final coherent narrative
        final_story = await self._synthesize_complete_story(segment_summaries, context)

        logger.info("Completed comprehensive transcription processing")
        return final_story

    def _prepare_initial_context(self, context: Any) -> Dict[str, Any]:
        """Prepare initial context for segment processing."""
        if hasattr(context, 'model_dump'):
            return {
                'session_name': getattr(context, 'session_name', 'Unknown Session'),
                'setting': getattr(context, 'setting', 'D&D Fantasy'),
                'characters': getattr(context, 'characters', []),
                'previous_events': getattr(context, 'previous_events', []),
                'campaign_notes': getattr(context, 'campaign_notes', None)
            }
        else:
            return context or {}

    def _update_session_memory(self, elements: Dict[str, Any]):
        """Update session memory with new elements."""
        self.session_memory['characters'].update(elements['characters'])
        self.session_memory['locations'].update(elements['locations'])
        self.session_memory['key_events'].extend(elements['actions'][:3])  # Keep top 3

        # Trim memory to prevent excessive growth
        if len(self.session_memory['key_events']) > 20:
            self.session_memory['key_events'] = self.session_memory['key_events'][-20:]

    def _update_running_context(self, context: Dict[str, Any], summary: str, elements: Dict[str, Any]) -> Dict[str, Any]:
        """Update context for next segment based on current segment results."""
        updated_context = context.copy()

        # Add discovered characters
        if 'characters' not in updated_context:
            updated_context['characters'] = []
        updated_context['characters'].extend(list(elements['characters']))
        updated_context['characters'] = list(set(updated_context['characters']))  # Remove duplicates

        # Add to previous events (keep it concise)
        if 'previous_events' not in updated_context:
            updated_context['previous_events'] = []

        # Add a summary of this segment to previous events
        segment_summary = summary[:200] + "..." if len(summary) > 200 else summary
        updated_context['previous_events'].append(f"Previous segment: {segment_summary}")

        # Keep only last 5 previous events to prevent context bloat
        updated_context['previous_events'] = updated_context['previous_events'][-5:]

        return updated_context

    @abstractmethod
    async def _process_single_segment(self, segment: Dict[str, Any], context: Any) -> str:
        """Process a single segment (when transcription is small enough)."""
        pass

    @abstractmethod
    async def _process_segment_with_context(self, segment: Dict[str, Any], context: Dict[str, Any], elements: Dict[str, Any]) -> str:
        """Process a segment with accumulated context from previous segments."""
        pass

    @abstractmethod
    async def _synthesize_complete_story(self, segment_summaries: List[Dict[str, Any]], original_context: Any) -> str:
        """Synthesize all segment summaries into final coherent story."""
        pass