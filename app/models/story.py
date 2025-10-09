"""Story models for D&D story generation system."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.models.database import Base


class StoryContext(BaseModel):
    """Context information for story generation."""

    session_name: str = Field(..., description="Name of the D&D session")
    characters: List[str] = Field(default_factory=list, description="List of character names")
    setting: str = Field(..., description="Campaign setting or location")
    previous_events: List[str] = Field(default_factory=list, description="Previous session events")
    campaign_notes: Optional[str] = Field(None, description="Additional campaign context")
    dm_notes: Optional[str] = Field(None, description="DM-specific notes")

    @validator("characters")
    def validate_characters(cls, v):
        """Validate character list."""
        if isinstance(v, str):
            return [v]  # Convert single string to list
        return v

    @validator("previous_events")
    def validate_previous_events(cls, v):
        """Validate previous events list."""
        if isinstance(v, str):
            return [v]  # Convert single string to list
        return v

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class StoryResult(BaseModel):
    """Result of story generation process."""

    narrative: str = Field(..., description="Generated story narrative")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in story quality")
    processing_time: float = Field(..., gt=0, description="Time taken to generate story (seconds)")
    word_count: Optional[int] = Field(None, description="Number of words in narrative")
    key_events: List[str] = Field(
        default_factory=list, description="Key events identified in story"
    )
    characters_mentioned: List[str] = Field(
        default_factory=list, description="Characters mentioned in story"
    )
    themes: List[str] = Field(default_factory=list, description="Themes identified in story")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    def __post_init__(self):
        """Calculate derived fields after initialization."""
        if self.word_count is None:
            self.word_count = len(self.narrative.split())

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class AudioTranscriptionResult(BaseModel):
    """Result of audio transcription process."""

    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected language")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence")
    duration: float = Field(..., gt=0, description="Audio duration in seconds")
    processing_time: float = Field(..., gt=0, description="Processing time in seconds")
    processing_successful: bool = Field(..., description="Whether processing succeeded")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


# Database models
class Story(Base):
    """Database model for stored stories."""

    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(255), nullable=False, index=True)
    narrative = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    processing_time = Column(Float, nullable=False)
    word_count = Column(Integer, nullable=False)
    key_events = Column(JSON, nullable=True)
    characters_mentioned = Column(JSON, nullable=True)
    themes = Column(JSON, nullable=True)
    story_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_story_result(self) -> StoryResult:
        """Convert database model to StoryResult."""
        return StoryResult(
            narrative=self.narrative,
            confidence_score=self.confidence_score,
            processing_time=self.processing_time,
            word_count=self.word_count,
            key_events=self.key_events or [],
            characters_mentioned=self.characters_mentioned or [],
            themes=self.themes or [],
            metadata=self.story_metadata or {},
            created_at=self.created_at,
        )


class AudioTranscription(Base):
    """Database model for stored audio transcriptions."""

    __tablename__ = "audio_transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash for deduplication
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    processing_time = Column(Float, nullable=False)
    file_size = Column(Integer, nullable=True)
    transcription_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to user
    user = relationship("User", back_populates="audio_transcriptions")

    def to_transcription_result(self) -> AudioTranscriptionResult:
        """Convert database model to AudioTranscriptionResult."""
        return AudioTranscriptionResult(
            text=self.text,
            language=self.language,
            confidence=self.confidence,
            duration=self.duration,
            processing_time=self.processing_time,
            processing_successful=True,
            metadata=self.transcription_metadata or {},
            created_at=self.created_at,
        )
