"""Application configuration management."""

import os
from typing import List, Optional
from functools import lru_cache
from pydantic import BaseSettings, Field, validator
from pydantic import ConfigDict

class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY", min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    CONFLUENCE_API_TOKEN: Optional[str] = Field(default=None, env="CONFLUENCE_API_TOKEN")
    CONFLUENCE_URL: Optional[str] = Field(default=None, env="CONFLUENCE_URL")
    CONFLUENCE_PARENT_PAGE_ID: Optional[str] = Field(default=None, env="CONFLUENCE_PARENT_PAGE_ID")
    
    # Application settings
    APP_NAME: str = Field(default="D&D Story Telling", env="APP_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    
    # Audio processing settings
    SUPPORTED_AUDIO_FORMATS: List[str] = Field(
        default=["mp3", "wav", "m4a", "ogg", "flac"],
        env="SUPPORTED_AUDIO_FORMATS"
    )
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True
    )
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate and normalize database URL."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        
        # Ensure async driver for PostgreSQL
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("ALLOWED_HOSTS", "CORS_ORIGINS", pre=True)
    def parse_list_settings(cls, v) -> List[str]:
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
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

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Global settings instance
settings = get_settings()