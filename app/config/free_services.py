#!/usr/bin/env python3
"""
Free service configuration for D&D Storytelling App
Zero-cost alternatives to paid APIs
"""

import os
from typing import Literal, Optional
from pydantic import BaseSettings

class FreeServicesConfig(BaseSettings):
    """Configuration for completely free services"""

    # AI Service Selection
    AI_SERVICE: Literal["ollama", "demo", "huggingface"] = "ollama"

    # Ollama Configuration (Completely Free Local AI)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"  # Free models: llama3.2:3b, mistral:7b, codellama:7b

    # Hugging Face (Free Tier)
    HUGGINGFACE_API_KEY: Optional[str] = None  # Optional, free tier available
    HUGGINGFACE_MODEL: str = "microsoft/DialoGPT-medium"

    # Audio Processing Selection
    AUDIO_SERVICE: Literal["whisper_cpp", "demo"] = "whisper_cpp"

    # Whisper.cpp Configuration (Completely Free Local)
    WHISPER_EXECUTABLE: str = "whisper"
    WHISPER_MODEL_PATH: str = "models/ggml-large-v3.bin"

    # Export Services (All Free)
    ENABLE_PDF_EXPORT: bool = True  # Uses ReportLab (free)
    ENABLE_WORD_EXPORT: bool = True  # Uses python-docx (free)
    ENABLE_CONFLUENCE: bool = False  # Disable paid Confluence

    # Database (Free Options)
    USE_SQLITE: bool = True  # Free alternative to PostgreSQL
    SQLITE_PATH: str = "data/dnd_stories.db"

    # File Storage (Local/Free)
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024 * 1024  # 5GB

    # Demo Mode Fallbacks
    DEMO_MODE_MESSAGES: bool = True
    ENHANCED_DEMO_RESPONSES: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

# Free service recommendations
FREE_SERVICE_GUIDE = {
    "ai_services": {
        "ollama": {
            "name": "Ollama (Recommended)",
            "cost": "100% Free",
            "setup": "Download from https://ollama.ai/",
            "models": {
                "llama3.2:3b": "4GB - Fast, good quality",
                "llama3.2:7b": "8GB - Better quality",
                "mistral:7b": "4GB - Great for storytelling",
                "codellama:7b": "4GB - Good for technical content"
            },
            "pros": ["Completely offline", "No API keys", "High quality", "Privacy"],
            "cons": ["Requires local installation", "Uses disk space"]
        },
        "huggingface": {
            "name": "Hugging Face Transformers",
            "cost": "Free tier available",
            "setup": "pip install transformers",
            "models": {
                "microsoft/DialoGPT-medium": "Conversational AI",
                "facebook/blenderbot-400M-distill": "Chatbot",
                "gpt2": "Text generation"
            },
            "pros": ["Easy to use", "Many models", "Free tier"],
            "cons": ["Limited free quota", "Requires internet"]
        },
        "demo": {
            "name": "Enhanced Demo Mode",
            "cost": "100% Free",
            "setup": "No setup required",
            "pros": ["Always works", "No dependencies", "Instant"],
            "cons": ["Not AI-generated", "Limited responses"]
        }
    },
    "audio_services": {
        "whisper_cpp": {
            "name": "Whisper.cpp (Recommended)",
            "cost": "100% Free",
            "setup": "https://github.com/ggerganov/whisper.cpp",
            "models": {
                "base": "150MB - Fast, basic accuracy",
                "small": "500MB - Good balance",
                "medium": "1.5GB - Better accuracy",
                "large-v3": "3GB - Best accuracy"
            },
            "pros": ["Completely offline", "High accuracy", "No API keys", "Privacy"],
            "cons": ["Requires compilation", "Uses disk space"]
        },
        "demo": {
            "name": "Demo Audio Processing",
            "cost": "100% Free",
            "setup": "No setup required",
            "pros": ["Always works", "No dependencies"],
            "cons": ["No real transcription", "Placeholder only"]
        }
    }
}

def print_free_alternatives_guide():
    """Print comprehensive guide for free alternatives"""
    print("🆓 COMPLETELY FREE D&D APP SETUP GUIDE")
    print("=" * 60)
    print()

    print("🎯 GOAL: Zero-cost D&D storytelling with local AI")
    print()

    print("📋 STEP 1: Install Ollama (Free Local AI)")
    print("1. Download: https://ollama.ai/")
    print("2. Install and start Ollama service")
    print("3. Download a model: `ollama pull llama3.2:3b`")
    print("4. Test: `ollama run llama3.2:3b \"Tell me a D&D story\"`")
    print()

    print("📋 STEP 2: Install Whisper.cpp (Free Audio)")
    print("1. Clone: `git clone https://github.com/ggerganov/whisper.cpp.git`")
    print("2. Build: `cd whisper.cpp && make`")
    print("3. Download model: `make large-v3`")
    print("4. Test with sample audio file")
    print()

    print("📋 STEP 3: Configure Your App")
    print("Create a `.env` file with:")
    print("```")
    print("AI_SERVICE=ollama")
    print("AUDIO_SERVICE=whisper_cpp")
    print("USE_SQLITE=true")
    print("ENABLE_CONFLUENCE=false")
    print("```")
    print()

    print("💰 COST BREAKDOWN:")
    print("• OpenAI API: $0 (replaced with Ollama)")
    print("• Audio transcription: $0 (replaced with Whisper.cpp)")
    print("• Database: $0 (SQLite instead of hosted PostgreSQL)")
    print("• Hosting: $0 (run locally or use free hosting)")
    print("• Total monthly cost: $0 🎉")
    print()

    print("🚀 BENEFITS:")
    print("• 100% offline after initial setup")
    print("• No API keys or billing accounts needed")
    print("• Complete privacy - nothing leaves your computer")
    print("• High-quality AI story generation")
    print("• Accurate audio transcription")
    print("• No usage limits or quotas")
    print()

    print("📊 SYSTEM REQUIREMENTS:")
    print("• 8GB RAM minimum (16GB recommended)")
    print("• 10GB free disk space for models")
    print("• Modern CPU with multiple cores")
    print("• GPU optional but helps with performance")

if __name__ == "__main__":
    print_free_alternatives_guide()