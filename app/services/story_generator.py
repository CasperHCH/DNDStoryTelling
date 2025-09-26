from openai import AsyncOpenAI
import os

class StoryGenerator:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_story(self, text: str, context: dict) -> str:
        prompt = self._create_prompt(text, context)
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a creative writer specializing in D&D campaign narratives."},
                {"role": "user", "content": prompt}
            ]
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