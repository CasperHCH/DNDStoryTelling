#!/usr/bin/env python3
"""
Startup script for D&D Story Telling application that uses environment configuration.
This script reads HOST and PORT from environment variables and starts the server accordingly.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

try:
    from app.config import get_settings

    def main():
        """Start the server using configuration from environment variables."""
        settings = get_settings()

        # Get host and port from config (which reads from environment)
        host = settings.HOST
        port = settings.PORT

        print(f"Starting D&D Story Telling server...")
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Debug: {settings.DEBUG}")
        print(f"Max File Size: {settings.MAX_FILE_SIZE / (1024*1024*1024):.1f}GB")
        print(f"Log Level: {settings.LOG_LEVEL}")

        # Start uvicorn with the configured host and port
        cmd = [
            "uvicorn",
            "app.main:socket_app",
            "--host", str(host),
            "--port", str(port),
        ]

        # Add reload for development
        if settings.is_development:
            cmd.append("--reload")
            print("Development mode: Auto-reload enabled")

        # Add log level
        cmd.extend(["--log-level", settings.LOG_LEVEL.lower()])

        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd)

except ImportError as e:
    print(f"Error importing configuration: {e}")
    print("Starting with default settings...")

    # Fallback to environment variables directly
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")

    cmd = [
        "uvicorn",
        "app.main:socket_app",
        "--host", host,
        "--port", port,
        "--log-level", os.getenv("LOG_LEVEL", "info").lower()
    ]

    print(f"Fallback execution: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()