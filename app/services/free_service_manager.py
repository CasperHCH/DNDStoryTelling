#!/usr/bin/env python3
"""
Free service integration for the main application
Automatically selects best available free service
"""

import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)

async def get_free_story_generator():
    """
    Get the best available free story generator.
    Priority: Ollama > Demo Mode
    """
    try:
        # Try Ollama first (completely free, local AI)
        from app.services.ollama_story_generator import OllamaStoryGenerator

        generator = OllamaStoryGenerator()
        # Test if Ollama is available
        await generator._check_ollama_status()
        logger.info("Using Ollama for free local AI story generation")
        return generator

    except Exception as e:
        logger.info(f"Ollama not available: {e}")

        try:
            # Fallback to Hugging Face (free tier)
            from app.services.huggingface_story_generator import HuggingFaceStoryGenerator

            generator = HuggingFaceStoryGenerator()
            logger.info("Using Hugging Face free tier for story generation")
            return generator

        except Exception as e:
            logger.info(f"Hugging Face not available: {e}")

            # Final fallback to enhanced demo mode
            from app.services.demo_story_generator import demo_generator
            logger.info("Using enhanced demo mode for story generation")
            return demo_generator

async def get_free_audio_processor():
    """
    Get the best available free audio processor.
    Priority: Whisper.cpp > Demo Mode
    """
    try:
        # Try Whisper.cpp first (completely free, local)
        from app.services.whisper_cpp_processor import WhisperCppProcessor

        processor = WhisperCppProcessor()
        await processor._check_whisper_availability()
        logger.info("Using Whisper.cpp for free local audio transcription")
        return processor

    except Exception as e:
        logger.info(f"Whisper.cpp not available: {e}")

        # Fallback to demo mode
        from app.services.demo_audio_processor import DemoAudioProcessor
        processor = DemoAudioProcessor()
        logger.info("Using demo mode for audio processing")
        return processor

def get_startup_message() -> str:
    """Get startup message about free services status"""
    return """
    🆓 FREE D&D STORYTELLING APP STARTED

    💡 To enable full free AI features:

    📥 For Story Generation:
    1. Install Ollama: https://ollama.ai/
    2. Run: ollama pull llama3.2:3b
    3. Restart the app

    🎤 For Audio Transcription:
    1. Install Whisper.cpp: https://github.com/ggerganov/whisper.cpp
    2. Compile and download models
    3. Restart the app

    Current Status: Demo mode active (still fully functional!)
    """

class FreeServiceManager:
    """Manages free service availability and selection"""

    def __init__(self):
        self.story_generator = None
        self.audio_processor = None
        self._initialized = False

    async def initialize(self):
        """Initialize free services"""
        if self._initialized:
            return

        logger.info("Initializing free services...")

        # Initialize story generator
        self.story_generator = await get_free_story_generator()

        # Initialize audio processor
        self.audio_processor = await get_free_audio_processor()

        self._initialized = True
        logger.info("Free services initialized successfully")

    async def generate_story(self, prompt: str, context) -> str:
        """Generate story using free services"""
        if not self._initialized:
            await self.initialize()

        return await self.story_generator.generate_story(prompt, context)

    async def process_audio(self, audio_path: str) -> str:
        """Process audio using free services"""
        if not self._initialized:
            await self.initialize()

        return await self.audio_processor.transcribe_audio(audio_path)

    def get_service_status(self) -> dict:
        """Get status of all free services"""
        return {
            "story_generator": type(self.story_generator).__name__ if self.story_generator else "Not initialized",
            "audio_processor": type(self.audio_processor).__name__ if self.audio_processor else "Not initialized",
            "cost": "Free",
            "privacy": "Complete - nothing leaves your computer",
            "setup_required": self._get_setup_requirements()
        }

    def _get_setup_requirements(self) -> dict:
        """Get what setup is needed for full functionality"""
        requirements = {}

        # Check Ollama
        try:
            import httpx
            response = httpx.get("http://localhost:11434/api/tags", timeout=2)
            requirements["ollama"] = "✅ Available"
        except:
            requirements["ollama"] = "❌ Install from https://ollama.ai/"

        # Check Whisper.cpp
        try:
            import subprocess
            result = subprocess.run(["whisper", "--help"], capture_output=True, timeout=5)
            requirements["whisper_cpp"] = "✅ Available"
        except:
            requirements["whisper_cpp"] = "❌ Install from https://github.com/ggerganov/whisper.cpp"

        return requirements

# Global free service manager instance
free_service_manager = FreeServiceManager()