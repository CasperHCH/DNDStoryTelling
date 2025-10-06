"""Application configuration management."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


def _get_env_files() -> List[str]:
    """Get list of environment files, filtering out None values."""
    env_files = []

    environment = os.getenv("ENVIRONMENT", "").lower()
    is_test = environment in ("test", "testing")

    # Add test-specific env files if they exist
    if is_test and os.path.exists(".env.docker.test"):
        env_files.append(".env.docker.test")
    if is_test and os.path.exists(".env.test.minimal"):
        env_files.append(".env.test.minimal")

    # Always try to load .env if it exists
    if os.path.exists(".env"):
        env_files.append(".env")

    return env_files


class Settings(BaseSettings):
    """Application settings with validation and type safety."""

    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # Database settings
    DATABASE_URL: str = Field(...)

    # Security settings
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS settings (stored as comma-separated strings, parsed to lists)
    ALLOWED_HOSTS: str = Field(default="*")
    CORS_ORIGINS: str = Field(default="*")

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    CONFLUENCE_API_TOKEN: Optional[str] = Field(default=None)
    CONFLUENCE_URL: Optional[str] = Field(default=None)
    CONFLUENCE_PARENT_PAGE_ID: Optional[str] = Field(default=None)

    # Server settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Application settings
    APP_NAME: str = Field(default="D&D Story Telling")
    VERSION: str = Field(default="1.0.0")

    # File upload settings
    MAX_FILE_SIZE: int = Field(default=5 * 1024 * 1024 * 1024)  # 5GB for D&D session recordings
    UPLOAD_DIR: str = Field(default="uploads")

    # Audio processing settings (stored as comma-separated string, parsed to list)
    SUPPORTED_AUDIO_FORMATS: str = Field(default="mp3,wav,m4a,ogg,flac")

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=3600)  # 1 hour

    # Database connection pooling
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_POOL_RECYCLE: int = Field(default=3600)  # 1 hour

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default=None)

    # Health check settings
    HEALTH_CHECK_ENDPOINT: str = Field(default="/health")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10)

    # Socket.IO settings
    SOCKETIO_PING_INTERVAL: int = Field(default=25000)  # 25 seconds
    SOCKETIO_PING_TIMEOUT: int = Field(default=20000)   # 20 seconds
    SOCKETIO_MAX_HTTP_BUFFER_SIZE: int = Field(default=1000000)  # 1MB

    # Free Services Configuration
    AI_SERVICE: str = Field(default="openai")  # Options: "openai", "ollama", "demo"
    AUDIO_SERVICE: str = Field(default="openai")  # Options: "openai", "whisper_cpp", "demo"
    USE_SQLITE: bool = Field(default=False)  # Use SQLite instead of PostgreSQL
    DEMO_MODE_FALLBACK: bool = Field(default=True)  # Fall back to demo mode on errors
    
    # Ollama Configuration (Free Local AI)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3.2:3b")
    
    # Whisper.cpp Configuration (Free Audio)
    WHISPER_EXECUTABLE: str = Field(default="whisper")
    WHISPER_MODEL_PATH: str = Field(default="models/ggml-base.bin")
    
    # SQLite Configuration
    SQLITE_PATH: str = Field(default="data/dnd_stories.db")

    model_config = ConfigDict(
        env_file=_get_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate and normalize database URL."""
        if not v:
            raise ValueError("DATABASE_URL is required")

        # Ensure async driver for PostgreSQL
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://")

        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        # Allow shorter keys in test environment
        import os

        if os.getenv("ENVIRONMENT", "").lower() in ("test", "testing"):
            if len(v) < 8:
                raise ValueError(
                    "SECRET_KEY must be at least 8 characters long in test environment"
                )
        else:
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("ALLOWED_HOSTS", "CORS_ORIGINS", "SUPPORTED_AUDIO_FORMATS", mode="before")
    @classmethod
    def parse_list_settings(cls, v) -> str:
        """Ensure list settings are strings for storage."""
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT.lower() in ("test", "testing")

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get ALLOWED_HOSTS as a list."""
        return [item.strip() for item in self.ALLOWED_HOSTS.split(",") if item.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS_ORIGINS as a list."""
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    @property
    def supported_audio_formats_list(self) -> List[str]:
        """Get SUPPORTED_AUDIO_FORMATS as a list."""
        return [item.strip() for item in self.SUPPORTED_AUDIO_FORMATS.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
