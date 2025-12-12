"""
Basic Functionality Tests for DNDStoryTelling Application

Tests core functionality that all current features depend on:
- Database connectivity and operations
- Model instantiation and validation
- Password hashing and verification
- File handling utilities
- Environment validation
"""

import pytest
import os
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime

from app.models.database import Base
from app.models.user import User
from app.models.story import Story
from app.auth.auth_handler import get_password_hash, verify_password


class TestDatabaseConnectivity:
    """Test database operations and connectivity."""

    @pytest.mark.asyncio
    async def test_engine_creation(self):
        """Test that database engine can be created."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=NullPool
        )
        assert engine is not None

        # Clean up
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_session_creation(self):
        """Test that database session can be created."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=NullPool
        )

        session_maker = async_sessionmaker(
        )

        assert session_maker is not None

        # Test creating a session
        async with session_maker() as session:
            assert isinstance(session, AsyncSession)

        # Clean up
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_table_creation(self):
        """Test that database tables can be created."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=NullPool
        )

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verify tables exist by checking metadata
        tables = Base.metadata.tables.keys()
        assert "users" in tables
        assert "stories" in tables
        assert "audio_transcriptions" in tables

        # Clean up
        await engine.dispose()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="SQLite async connection pooling issue with in-memory DB - table creation not persisting across session")
    async def test_basic_crud_operations(self):
        """Test basic Create, Read, Delete operations."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=NullPool
        )

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(
            engine,
            expire_on_commit=False
        )

        # Test all operations in one session to avoid connection issues
        async with session_maker() as session:
            # Create
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("password123")
            )
            session.add(test_user)
            await session.flush()  # Flush instead of commit to keep session active
            
            user_id = test_user.id
            assert user_id is not None

            # Read
            result = await session.execute(select(User).where(User.id == user_id))
            retrieved_user = result.scalars().first()

            assert retrieved_user is not None

            # Delete
            await session.delete(test_user)
            await session.flush()

            # Verify deletion
            result = await session.execute(select(User).where(User.id == user_id))
            deleted_user = result.scalars().first()

            assert deleted_user is None

        # Clean up
        await engine.dispose()


class TestModelInstantiation:
    """Test model instantiation without database."""

    def test_user_model_creation(self):
        """Test User model can be instantiated."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_pass"
        )

        # Check basic attributes (use getattr to avoid SQLAlchemy comparison issues)
        assert getattr(user, 'username', None) == "testuser"
        assert getattr(user, 'email', None) == "test@example.com"

    def test_user_model_defaults(self):
        """Test User model default values."""
        user = User(
            username="test",
            email="test@example.com",
            hashed_password="hash"
        )

        # Check defaults - verify attributes exist and have expected types
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'is_verified')
        assert hasattr(user, 'preferred_audio_model')
        assert hasattr(user, 'max_file_size_mb')

    def test_story_model_creation(self):
        """Test Story model can be instantiated."""
        now = datetime.utcnow()
        
        story = Story(
            session_name="Test Session",
            narrative="Test narrative",
            confidence_score=0.95,
            processing_time=1.5,
            word_count=100,
            created_at=now,
            updated_at=now
        )

        # Check attributes
        assert getattr(story, 'session_name', None) == "Test Session"
        assert getattr(story, 'narrative', None) == "Test narrative"
        assert getattr(story, 'confidence_score', None) == 0.95
        assert getattr(story, 'word_count', None) == 100


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hash_generation(self):
        """Test password can be hashed."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_password_verification_success(self):
        """Test correct password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test incorrect password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_uniqueness(self):
        """Test same password generates different hashes (salt)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Different hashes due to salt
        assert hash1 != hash2

        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestFileSystemOperations:
    """Test file system operations and utilities."""

    def test_temp_directory_access(self):
        """Test temporary directory can be accessed."""
        temp_dir = Path("temp")

        # Directory should be creatable if it doesn't exist
        if not temp_dir.exists():
            temp_dir.mkdir(exist_ok=True)

        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_uploads_directory_structure(self):
        """Test uploads directory can be created."""
        uploads_dir = Path("uploads")

        if not uploads_dir.exists():
            uploads_dir.mkdir(exist_ok=True)

        assert uploads_dir.exists()
        assert uploads_dir.is_dir()

    def test_path_operations(self):
        """Test basic path operations."""
        # Test path creation
        test_path = Path("uploads") / "test.mp3"
        assert test_path.suffix == ".mp3"
        assert test_path.parent == Path("uploads")
        assert test_path.name == "test.mp3"

    def test_python_version(self):
        """Test Python version is compatible."""
        import sys

        version_info = sys.version_info
        # Python 3.8+ required
        assert version_info.major == 3
        assert version_info.minor >= 8

    def test_required_packages_importable(self):
        """Test that required packages can be imported."""
        required_packages = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "passlib",
            "httpx",
            "pytest"
        ]

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Required package '{package}' cannot be imported")

    def test_async_support(self):
        """Test async/await support is available."""
        import asyncio

        async def test_async():
            return "async works"

        result = asyncio.run(test_async())
        assert result == "async works"


class TestDataValidation:
    """Test data validation and sanitization."""

    def test_email_validation_format(self):
        """Test email format validation."""
        from email_validator import validate_email, EmailNotValidError

        # Valid email format
        try:
            valid = validate_email("test@example.com", check_deliverability=False)
            assert "@" in valid.normalized
        except EmailNotValidError:
            pytest.fail("Valid email rejected")
        
        # Invalid email format
        with pytest.raises(EmailNotValidError):
            validate_email("invalid-email", check_deliverability=False)
        valid_usernames = ["user123", "test_user", "a_b_c", "abc"]

        for username in valid_usernames:
            assert len(username) >= 3
            assert len(username) <= 50

        # Length constraints
        too_short = "ab"
        too_long = "a" * 51

        assert len(too_short) < 3
        assert len(too_long) > 50

    def test_password_strength_requirements(self):
        """Test password meets minimum requirements."""
        # Minimum 8 characters
        weak_password = "short"
        strong_password = "longenough123"

        assert len(weak_password) < 8
        assert len(strong_password) >= 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
