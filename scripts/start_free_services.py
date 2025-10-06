#!/usr/bin/env python3
"""
Startup script for free services version
Initializes Ollama, downloads models, and starts the web application
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
import httpx
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FreeServicesStartup:
    """Manages startup of free services in Docker"""

    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.default_model = "llama3.2:3b"
        self.whisper_path = "/usr/local/bin/whisper"
        self.whisper_model = "/app/models/whisper/ggml-base.bin"

    async def start_free_services(self):
        """Start all free services and the web application"""
        logger.info("🆓 Starting Free D&D Storytelling Services...")

        # Step 1: Start Ollama service
        await self.start_ollama()

        # Step 2: Ensure models are available
        await self.setup_models()

        # Step 3: Verify Whisper.cpp setup
        self.verify_whisper()

        # Step 4: Initialize database
        await self.init_database()

        # Web application will be started separately

    async def start_ollama(self):
        """Start Ollama service"""
        logger.info("🤖 Starting Ollama service...")

        try:
            # Start Ollama in background
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for Ollama to be ready
            for attempt in range(30):  # 30 seconds timeout
                try:
                    async with httpx.AsyncClient(timeout=2) as client:
                        response = await client.get(f"{self.ollama_url}/api/tags")
                        if response.status_code == 200:
                            logger.info("✅ Ollama service started successfully")
                            return
                except:
                    pass

                await asyncio.sleep(1)

            logger.warning("⚠️ Ollama may not be fully ready, continuing anyway...")

        except Exception as e:
            logger.error(f"❌ Failed to start Ollama: {e}")
            logger.info("📝 App will run in demo mode")

    async def setup_models(self):
        """Download and setup AI models"""
        logger.info("📥 Setting up AI models...")

        try:
            # Check if model is already available
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json()
                    model_names = [model["name"] for model in models.get("models", [])]

                    if any(self.default_model in name for name in model_names):
                        logger.info(f"✅ Model {self.default_model} already available")
                        return

            # Download model if not available
            logger.info(f"📥 Downloading {self.default_model} (this may take several minutes on first run)...")

            process = subprocess.run(
                ["ollama", "pull", self.default_model],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if process.returncode == 0:
                logger.info(f"✅ Model {self.default_model} downloaded successfully")
            else:
                logger.warning(f"⚠️ Model download failed: {process.stderr}")
                logger.info("📝 App will use demo mode fallback")

        except Exception as e:
            logger.error(f"❌ Model setup failed: {e}")
            logger.info("📝 App will use demo mode fallback")

    def verify_whisper(self):
        """Verify Whisper.cpp setup"""
        logger.info("🎤 Verifying Whisper.cpp setup...")

        try:
            # Check if whisper executable exists
            if not os.path.exists(self.whisper_path):
                logger.warning(f"⚠️ Whisper executable not found at {self.whisper_path}")
                return

            # Check if model file exists
            if not os.path.exists(self.whisper_model):
                logger.warning(f"⚠️ Whisper model not found at {self.whisper_model}")
                logger.info("📝 Audio processing will use demo mode")
                return

            # Test whisper
            result = subprocess.run([self.whisper_path, "--help"],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                logger.info("✅ Whisper.cpp ready for audio transcription")
            else:
                logger.warning("⚠️ Whisper.cpp test failed")

        except Exception as e:
            logger.warning(f"⚠️ Whisper verification failed: {e}")
            logger.info("📝 Audio processing will use demo mode")

    async def init_database(self):
        """Initialize database"""
        logger.info("🗄️ Initializing database...")

        try:
            # Create data directory
            os.makedirs("/data", exist_ok=True)

            # Initialize database (will be handled by the app)
            logger.info("✅ Database directory ready")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

    def start_web_app(self):
        """Start the web application"""
        logger.info("🚀 Starting D&D Storytelling web application...")

        try:
            # Set environment variables for free services
            os.environ.update({
                "AI_SERVICE": "ollama",
                "AUDIO_SERVICE": "whisper_cpp",
                "USE_SQLITE": "true",
                "DEMO_MODE_FALLBACK": "true",
                "OLLAMA_BASE_URL": self.ollama_url,
                "OLLAMA_MODEL": self.default_model,
                "WHISPER_EXECUTABLE": self.whisper_path,
                "WHISPER_MODEL_PATH": self.whisper_model,
                "DATABASE_URL": "sqlite:///data/dnd_stories.db"
            })

            # Import and start the application
            sys.path.insert(0, "/app")

            # Run the web server
            import uvicorn
            from app.main import socket_app

            logger.info("🌐 Web application starting on http://0.0.0.0:8000")
            logger.info("🎮 Your free D&D storytelling app is ready!")
            logger.info("📊 Services status:")
            logger.info("   • AI Generation: Ollama (Free)")
            logger.info("   • Audio Processing: Whisper.cpp (Free)")
            logger.info("   • Database: SQLite (Free)")
            logger.info("   • Monthly Cost: $0 🎉")

            uvicorn.run(
                socket_app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )

        except Exception as e:
            logger.error(f"❌ Failed to start web application: {e}")
            raise

async def setup_services():
    """Setup services without starting the web server"""
    startup = FreeServicesStartup()

    # Setup all services except web app
    await startup.start_ollama()
    await startup.setup_models()
    startup.verify_whisper()
    await startup.init_database()

    return startup

def main():
    """Main startup function"""
    try:
        # Setup services
        startup = asyncio.run(setup_services())

        # Start web application (synchronous)
        startup.start_web_app()

    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"💥 Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()