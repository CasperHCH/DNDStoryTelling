import pytest
from fastapi.testclient import TestClient
from app import app
from app.models.database import Base, engine
from sqlalchemy.orm import Session

client = TestClient(app)

@pytest.fixture(autouse=True)
async def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_register():
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "message" in response.json()

def test_login():
    # First register a user
    client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass"}
    )

    # Then try to login
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()