# filepath: c:\repos\DNDStoryTelling\tests\conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base
from app.models.user import User
from app.auth.auth_handler import get_password_hash, create_access_token
import os
from fastapi.testclient import TestClient
from app import app

TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dndstory_test"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
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
def authorized_client(test_token):
    client = TestClient(app)
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_token}"
    }
    return client

@pytest.fixture
def test_audio_file(tmp_path):
    from pydub import AudioSegment
    audio = AudioSegment.silent(duration=1000)
    file_path = tmp_path / "test_audio.wav"
    audio.export(str(file_path), format="wav")
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