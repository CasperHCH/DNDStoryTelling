import os

from openai import AsyncOpenAI


class StoryGenerationError(Exception):
    """Exception raised when story generation fails."""
    pass


class StoryGenerator:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_story(self, text: str, context) -> str:
        prompt = self._create_prompt(text, context)

        # Try models in order of preference (newest to older)
        models_to_try = ["gpt-4o", "gpt-4", "gpt-4-turbo"]

        for model in models_to_try:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a creative writer specializing in D&D campaign narratives.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                error_msg = str(e).lower()
                if "model" in error_msg and "not found" in error_msg:
                    continue  # Try next model
                elif "quota" in error_msg or "insufficient_quota" in error_msg or "429" in str(e):
                    # Quota exceeded - provide clear error message
                    raise Exception(f"OpenAI quota exceeded (Error 429). Please check your plan and billing details at https://platform.openai.com/account/billing")
                elif "401" in str(e) or "authentication" in error_msg:
                    # Authentication error
                    raise Exception("OpenAI API key authentication failed. Please check your API key.")
                else:
                    raise e  # Re-raise other errors

        # If all models fail, raise the last error
        raise Exception(f"None of the available models ({', '.join(models_to_try)}) are accessible with your API key. Please check your OpenAI account and subscription.")

    def _create_prompt(self, text: str, context) -> str:
        # Handle both dict and StoryContext model
        if hasattr(context, 'model_dump'):
            # Pydantic model
            session_name = getattr(context, 'session_name', 'Unknown Session')
            setting = getattr(context, 'setting', 'generic fantasy')
            characters = getattr(context, 'characters', [])
            previous_events = getattr(context, 'previous_events', [])
            campaign_notes = getattr(context, 'campaign_notes', None)
        else:
            # Dictionary fallback for legacy tests
            session_name = context.get('session_name', 'Unknown Session')
            setting = context.get('setting', 'generic fantasy')
            characters = context.get('characters', [])
            previous_events = context.get('previous_events', [])
            campaign_notes = context.get('campaign_notes', None)

        characters_str = ', '.join(characters) if characters else 'Unknown characters'
        previous_str = '. '.join(previous_events) if previous_events else 'No previous events'
        notes_str = campaign_notes if campaign_notes else 'No additional notes'

        return f"""
        Based on this D&D session transcript:
        {text}

        Create a narrative with these specifications:
        Session: {session_name}
        Setting: {setting}
        Characters: {characters_str}
        Previous Events: {previous_str}
        Campaign Notes: {notes_str}

        Please create an engaging narrative summary of this session.
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

    def validate_context(self, context):
        """Validate and normalize context parameters."""
        # If it's already a StoryContext model, return as-is
        if hasattr(context, 'model_dump'):
            return context

        # Handle dictionary input for backwards compatibility
        if isinstance(context, dict):
            from app.models.story import StoryContext

            # Map old context fields to new StoryContext fields
            session_name = context.get('session_name', 'D&D Session')
            setting = context.get('world', context.get('setting', 'generic fantasy'))
            characters = context.get('characters', [])
            previous_events = context.get('previous_context', [])
            if isinstance(previous_events, str) and previous_events != 'none':
                previous_events = [previous_events]
            elif previous_events == 'none':
                previous_events = []

            campaign_notes = context.get('campaign_notes', None)

            return StoryContext(
                session_name=session_name,
                setting=setting,
                characters=characters,
                previous_events=previous_events,
                campaign_notes=campaign_notes
            )

        return context
