import pytest
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.database import Base
from fastapi.testclient import TestClient
import tempfile
from pathlib import Path

# Test database URL - use the one from environment or fallback to async PostgreSQL test URL
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/dndstory_test")
# For sync operations, convert asyncpg to psycopg2 URL
TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://") if "+asyncpg" in TEST_DATABASE_URL else TEST_DATABASE_URL

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def app():
    """Create the FastAPI app for testing."""
    from app.main import app
    return app

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture(scope="session")
def sync_test_engine():
    """Create synchronous test database engine for sync tests."""
    engine = create_engine(TEST_DATABASE_URL_SYNC, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Create a database session for testing."""
    Session = sessionmaker(test_engine, class_=AsyncSession)
    async with Session() as session:
        yield session

@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def audio_file():
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        # Create a minimal WAV file header
        wav_header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        tmp.write(wav_header)
        tmp.flush()
        yield tmp.name

    # Clean up
    try:
        os.unlink(tmp.name)
    except:
        pass# Mock configurations for tests that don't need actual services
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("CONFLUENCE_API_TOKEN", "test_confluence_token")
    monkeypatch.setenv("CONFLUENCE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)