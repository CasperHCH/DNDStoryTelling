"""User model for authentication and user management."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    """User model for storing user authentication and profile data."""

    __tablename__ = "users"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # API Configuration (encrypted in production)
    openai_api_key = Column(Text)  # Encrypted storage recommended
    confluence_api_token = Column(Text)  # Encrypted storage recommended
    confluence_url = Column(String(500))
    confluence_parent_page_id = Column(String(50))

    # User preferences
    preferred_audio_model = Column(String(50), default="base")
    max_file_size_mb = Column(Integer, default=50)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        return self.username

    def has_openai_config(self) -> bool:
        """Check if user has OpenAI configuration."""
        return bool(self.openai_api_key)

    def has_confluence_config(self) -> bool:
        """Check if user has Confluence configuration."""
        return bool(
            self.confluence_api_token and self.confluence_url and self.confluence_parent_page_id
        )
