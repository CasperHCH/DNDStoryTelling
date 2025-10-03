import os

from openai import AsyncOpenAI


class StoryGenerationError(Exception):
    """Exception raised when story generation fails."""
    pass


class StoryGenerator:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_story(self, text: str, context: dict) -> str:
        prompt = self._create_prompt(text, context)
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative writer specializing in D&D campaign narratives.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def _create_prompt(self, text: str, context: dict) -> str:
        return f"""
        Based on this D&D session transcript:
        {text}

        Create a narrative with these specifications:
        Tone: {context.get('tone', 'neutral')}
        Mood: {context.get('mood', 'standard')}
        World: {context.get('world', 'generic fantasy')}
        Previous Context: {context.get('previous_context', 'none')}
        """

    def _preprocess_transcription(self, transcription: str) -> str:
        """Preprocess transcription text for better story generation."""
        if not transcription or not transcription.strip():
            return ""

        # Clean up common transcription artifacts
        cleaned = transcription.strip()

        # Remove excessive whitespace
        cleaned = ' '.join(cleaned.split())

        # Basic punctuation cleanup
        cleaned = cleaned.replace(' ,', ',')
        cleaned = cleaned.replace(' .', '.')
        cleaned = cleaned.replace(' ?', '?')
        cleaned = cleaned.replace(' !', '!')

        return cleaned

    def validate_context(self, context: dict) -> dict:
        """Validate and normalize context parameters."""
        valid_context = {}

        # Validate tone
        valid_tones = ['neutral', 'dark', 'heroic', 'comedic', 'mysterious', 'epic']
        tone = context.get('tone', 'neutral')
        valid_context['tone'] = tone if tone in valid_tones else 'neutral'

        # Validate mood
        valid_moods = ['standard', 'tense', 'relaxed', 'dramatic', 'lighthearted']
        mood = context.get('mood', 'standard')
        valid_context['mood'] = mood if mood in valid_moods else 'standard'

        # Validate world setting
        world = context.get('world', 'generic fantasy')
        valid_context['world'] = str(world) if world else 'generic fantasy'

        # Validate previous context
        prev_context = context.get('previous_context', 'none')
        valid_context['previous_context'] = str(prev_context) if prev_context else 'none'

        return valid_context
