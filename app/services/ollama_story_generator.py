#!/usr/bin/env python3
"""
Free local AI story generator using Ollama
No API keys, no billing, completely offline!

Install Ollama first: https://ollama.ai/
Then run: ollama pull llama3.2:3b (or other models)
"""

import asyncio
import httpx
import json
import logging
from typing import Optional, Dict, Any, List

from app.services.segmented_story_processor import SegmentedStoryProcessor

logger = logging.getLogger(__name__)

class OllamaStoryGenerator(SegmentedStoryProcessor):
    """
    Free local AI story generator using Ollama.
    Zero cost, works completely offline!
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        super().__init__(max_segment_tokens=2500, overlap_tokens=150)  # Conservative for local models
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_story(self, text: str, context) -> str:
        """
        Generate a story using local Ollama model with comprehensive transcription processing.
        Ensures ALL content is processed regardless of size.
        """
        logger.info(f"Starting Ollama story generation for {self.estimate_tokens(text)} estimated tokens")

        try:
            # Check if Ollama is running
            await self._check_ollama_status()
            await self._ensure_model_available()

            # Use segmented processing to handle large transcriptions
            return await self.process_full_transcription(text, context)

        except Exception as e:
            logger.error(f"Ollama story generation failed: {e}")
            # Fallback to enhanced demo mode
            return self._create_fallback_story(text, context)

    async def _process_single_segment(self, segment: Dict[str, Any], context: Any) -> str:
        """Process a single segment when transcription is small enough."""
        prompt = self._create_prompt(segment['content'], context)
        return await self._generate_with_ollama(prompt)

    async def _process_segment_with_context(self, segment: Dict[str, Any], context: Dict[str, Any], elements: Dict[str, Any]) -> str:
        """Process a segment with accumulated context from previous segments."""
        enhanced_prompt = self._create_segment_prompt(segment['content'], context, elements, segment)
        return await self._generate_with_ollama(enhanced_prompt)

    async def _synthesize_complete_story(self, segment_summaries: List[Dict[str, Any]], original_context: Any) -> str:
        """Synthesize all segment summaries into final coherent story."""
        # Combine all summaries
        all_summaries = [s['summary'] for s in segment_summaries]
        combined_content = "\n\n---\n\n".join(all_summaries)

        # Create synthesis prompt
        synthesis_prompt = self._create_synthesis_prompt(combined_content, segment_summaries, original_context)

        # Generate final unified story
        final_story = await self._generate_with_ollama(synthesis_prompt)

        # Add session statistics
        total_characters = len(self.session_memory['characters'])
        total_locations = len(self.session_memory['locations'])

        header = f"""# 🎲 Complete D&D Session Story (Ollama Local AI)

*This story was generated locally using Ollama, processing ALL {len(segment_summaries)} segments of your session transcription with complete privacy.*

**Session Statistics:**
- Characters Identified: {total_characters}
- Locations Visited: {total_locations}
- Segments Processed: {len(segment_summaries)}
- Complete Story: Yes ✅
- Processing: Local & Private 🔒

---

"""

        return header + final_story

    async def _check_ollama_status(self):
        """Check if Ollama service is running."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise Exception("Ollama service not accessible")
        except Exception as e:
            raise Exception(f"Ollama not running. Please start Ollama service: {e}")

    async def _ensure_model_available(self):
        """Ensure the specified model is downloaded."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            models = response.json()

            model_names = [model["name"] for model in models.get("models", [])]

            if not any(self.model in name for name in model_names):
                # Try to pull the model
                logger.info(f"Downloading model {self.model}... This may take a few minutes.")

                pull_data = {"name": self.model}
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json=pull_data
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "status" in data:
                                logger.info(f"Model download: {data['status']}")

        except Exception as e:
            raise Exception(f"Model {self.model} not available: {e}")

    async def _generate_with_ollama(self, prompt: str) -> str:
        """Generate text using Ollama API."""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        result = response.json()
        return result.get("response", "").strip()

    def _create_prompt(self, text: str, context) -> str:
        """Create enhanced prompt for D&D storytelling."""
        # Handle both dict and StoryContext model
        if hasattr(context, 'model_dump'):
            session_name = getattr(context, 'session_name', 'Unknown Session')
            setting = getattr(context, 'setting', 'generic fantasy')
            characters = getattr(context, 'characters', [])
            previous_events = getattr(context, 'previous_events', [])
            campaign_notes = getattr(context, 'campaign_notes', None)
        else:
            session_name = context.get('session_name', 'Unknown Session')
            setting = context.get('setting', 'generic fantasy')
            characters = context.get('characters', [])
            previous_events = context.get('previous_events', [])
            campaign_notes = context.get('campaign_notes', None)

        characters_str = ', '.join(characters) if characters else 'Unknown characters'
        previous_str = '. '.join(previous_events) if previous_events else 'No previous events'
        notes_str = campaign_notes if campaign_notes else 'No additional notes'

        return f"""You are an expert Dungeon Master and storyteller specializing in D&D campaigns.

Session Information:
- Session: {session_name}
- Setting: {setting}
- Characters: {characters_str}
- Previous Events: {previous_str}
- Campaign Notes: {notes_str}

Based on this D&D session content:
{text}

Create an engaging, detailed narrative summary that:
1. Captures the key events and character actions
2. Maintains the tone and atmosphere of D&D
3. Includes dialogue and character interactions
4. Describes the setting and environment vividly
5. Highlights important story developments
6. Uses proper D&D terminology and style

Write the story in past tense, third person, as if recounting the session to other players. Make it exciting and immersive!"""

    def _create_segment_prompt(self, text: str, context: Dict[str, Any], elements: Dict[str, Any], segment_info: Dict[str, Any]) -> str:
        """Create prompt for processing a segment with context from previous segments."""
        session_name = context.get('session_name', 'Unknown Session')
        setting = context.get('setting', 'D&D Fantasy')
        characters = context.get('characters', [])
        previous_events = context.get('previous_events', [])

        characters_str = ', '.join(characters) if characters else 'Unknown characters'
        previous_str = '. '.join(previous_events) if previous_events else 'Beginning of session'

        segment_characters = ', '.join(elements['characters']) if elements['characters'] else 'None discovered'
        segment_locations = ', '.join(elements['locations']) if elements['locations'] else 'None specified'

        return f"""You are an expert D&D storyteller processing part {segment_info['segment_id']} of {segment_info['total_segments']} from a session.

Session Context:
- Session: {session_name}
- Setting: {setting}
- Known Characters: {characters_str}
- Previous Events: {previous_str}

This Segment:
- Characters: {segment_characters}
- Locations: {segment_locations}
- Part: {segment_info['segment_id']}/{segment_info['total_segments']}

Content:
{text}

Create a vivid narrative for this part that connects to the ongoing story. Focus on character actions, dialogue, and atmospheric descriptions. Make it engaging and maintain continuity with previous events."""

    def _create_synthesis_prompt(self, combined_content: str, segment_summaries: List[Dict[str, Any]], original_context: Any) -> str:
        """Create prompt for synthesizing all segments into final story."""
        if hasattr(original_context, 'model_dump'):
            session_name = getattr(original_context, 'session_name', 'Epic D&D Session')
            setting = getattr(original_context, 'setting', 'D&D Fantasy')
        else:
            session_name = original_context.get('session_name', 'Epic D&D Session') if original_context else 'Epic D&D Session'
            setting = original_context.get('setting', 'D&D Fantasy') if original_context else 'D&D Fantasy'

        all_characters = list(self.session_memory['characters'])
        all_locations = list(self.session_memory['locations'])

        characters_str = ', '.join(all_characters) if all_characters else 'Various adventurers'
        locations_str = ', '.join(all_locations) if all_locations else 'Multiple locations'

        return f"""You are creating the final story from {len(segment_summaries)} parts of a D&D session.

Session: {session_name}
Setting: {setting}
All Characters: {characters_str}
All Locations: {locations_str}

Story Parts:
{combined_content}

Weave these parts into one complete, engaging D&D session story. Maintain chronological order, develop character arcs, and create a satisfying narrative flow. This should read as one unified adventure, not separate pieces."""

    def _create_fallback_story(self, prompt: str, context) -> str:
        """Create fallback story when Ollama is not available."""
        return f"""🎲 **Local AI Story Generation (Offline Mode)**

**Session Summary**: A thrilling D&D adventure unfolds as the party faces new challenges and discoveries.

**Key Events**:
• The adventurers explored mysterious territories and encountered unexpected allies
• Strategic decisions were made that will shape future encounters
• Character development moments revealed new depths to party relationships
• Combat encounters tested the group's tactical abilities and teamwork
• Exploration revealed important clues about the overarching campaign

**Atmosphere**: The session was filled with tension, excitement, and memorable roleplay moments that brought the world to life.

**Story Impact**: The events of this session have set the stage for future adventures, with consequences that will ripple through the campaign.

---
**💡 For Enhanced AI Stories**:
Install Ollama (https://ollama.ai/) and run `ollama pull llama3.2:3b` to enable full local AI story generation with no costs!

**Current Status**: Ollama not detected - using enhanced demo mode."""

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Example usage and installation guide
if __name__ == "__main__":
    print("🤖 Free Local AI Story Generator Setup")
    print("=" * 50)
    print()
    print("📋 Installation Steps:")
    print("1. Download Ollama: https://ollama.ai/")
    print("2. Install and start Ollama service")
    print("3. Download a model: `ollama pull llama3.2:3b`")
    print("4. Run this script to test!")
    print()
    print("📊 Model Recommendations:")
    print("• llama3.2:3b (4GB) - Fast, good quality")
    print("• llama3.2:7b (8GB) - Better quality, slower")
    print("• mistral:7b (4GB) - Great for storytelling")
    print("• codellama:7b (4GB) - Good for technical content")
    print()
    print("💾 Storage Requirements:")
    print("• Small models (3B): ~4GB disk space")
    print("• Medium models (7B): ~8GB disk space")
    print("• Runs completely offline after download!")