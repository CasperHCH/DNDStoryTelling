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

TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/dndstory_test"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

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
        openai_api_key="test_openai_key",
        confluence_api_token="test_confluence_token",
        confluence_url="https://test.atlassian.net"
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