import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import text

client = TestClient(app)

print("Debug: test_health_check.py loaded")

@pytest.fixture(scope="module")
def setup_env():
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["SECRET_KEY"] = "test_secret_key"

@pytest.mark.usefixtures("setup_env")
def test_health_check(setup_env):
    print("Debug: test_health_check function executed")
    # Test environment variables
    assert "OPENAI_API_KEY" in os.environ
    assert "DATABASE_URL" in os.environ
    assert "SECRET_KEY" in os.environ

    # Test database connection
    from sqlalchemy import create_engine
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

    # Test application health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}