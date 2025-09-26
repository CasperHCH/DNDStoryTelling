import pytest
from fastapi.testclient import TestClient
from app import app
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture
def auth_headers():
    # Login and get token
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_upload_text(auth_headers):
    with patch('app.services.story_generator.StoryGenerator.generate_story') as mock_generate:
        mock_generate.return_value = "Generated story"
        response = client.post(
            "/story/upload",
            files={"file": ("test.txt", "Test session content")},
            headers=auth_headers,
            data={"context": '{"tone": "heroic"}'}
        )
        assert response.status_code == 200
        assert "story" in response.json()