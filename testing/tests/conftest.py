"""Test configuration and fixtures."""

import os
import sys
import pytest
import warnings
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

# Suppress PyTorch warnings during testing
warnings.filterwarnings("ignore", category=FutureWarning, message=".*weights_only.*")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up test environment variables before importing the app
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-development-only-that-is-long-enough-for-validation"
os.environ["SKIP_AUDIO_TESTS"] = "true"  # Skip audio tests in CI/CD
os.environ["MOCK_AUDIO_PROCESSING"] = "true"  # Use mocked audio processing

# Now import after environment is set
from app.config import get_settings
from app.main import app as fastapi_app
from app.models.database import Base
from app.models.user import User
from app.auth.auth_handler import get_password_hash, create_access_token

# Clear the settings cache to ensure test environment variables are used
get_settings.cache_clear()

TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

@pytest.fixture(scope="session")
def engine():
    # Use synchronous SQLite for test database operations
    sync_test_url = "sqlite:///test.db"
    engine = create_engine(sync_test_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        confluence_parent_page_id="123456789",  # Example: Replace with the ID of the parent page in Confluence where new pages will be created
        openai_api_key="test_openai_key",  # Example: Replace with your OpenAI API key
        confluence_api_token="test_confluence_token",  # Example: Replace with your Confluence API token
        confluence_url="https://test.atlassian.net"  # Example: Replace with your Confluence Cloud URL
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_token(test_user):
    return create_access_token(data={"sub": test_user.username})

@pytest.fixture
def app():
    """App fixture for testing."""
    return fastapi_app

@pytest.fixture
def client():
    """Basic test client fixture."""
    return TestClient(fastapi_app)

@pytest.fixture
def authorized_client(test_token):
    client = TestClient(fastapi_app)
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_token}"
    }
    return client

@pytest.fixture
def test_audio_file(tmp_path):
    """Create a test audio file (skipped if audio dependencies not available)."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.silent(duration=1000)
        file_path = tmp_path / "test_audio.wav"
        audio.export(str(file_path), format="wav")
        return file_path
    except (ImportError, RuntimeError):
        # Create a mock audio file for testing
        file_path = tmp_path / "test_audio.wav"
        file_path.write_bytes(b"MOCK_AUDIO_DATA")
        return file_path

@pytest.fixture
def mock_openai_response():
    return {
        "choices": [
            {
                "message": {
                    "content": "Test generated story"
                }
            }
        ]
    }


@pytest.fixture(autouse=True)
def mock_whisper_globally():
    """Mock Whisper globally to avoid loading actual models."""
    with patch('app.services.audio_processor.whisper') as mock_whisper:
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "Mock transcription result from audio file",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Mock transcription result from audio file",
                    "confidence": 0.95
                }
            ],
            "language": "en"
        }
        mock_whisper.load_model.return_value = mock_model
        yield mock_whisper


@pytest.fixture
def mock_audio_processor():
    """Mock audio processor that doesn't require actual Whisper models."""
    from testing.mocks.audio_mock import MockAudioProcessor
    return MockAudioProcessor()


@pytest.fixture
def sample_audio_content():
    """Generate sample audio file content for testing."""
    # Minimal WAV file header
    return (
        b'RIFF'
        + (44).to_bytes(4, 'little')  # File size - 8
        + b'WAVE'
        + b'fmt '
        + (16).to_bytes(4, 'little')  # Subchunk1Size
        + (1).to_bytes(2, 'little')   # AudioFormat (PCM)
        + (1).to_bytes(2, 'little')   # NumChannels (mono)
        + (22050).to_bytes(4, 'little')  # SampleRate
        + (22050).to_bytes(4, 'little')  # ByteRate
        + (1).to_bytes(2, 'little')   # BlockAlign
        + (8).to_bytes(2, 'little')   # BitsPerSample
        + b'data'
        + (0).to_bytes(4, 'little')   # Subchunk2Size
    )


@pytest.fixture
def api_key():
    """Provide test API key."""
    return "test-openai-api-key-12345"