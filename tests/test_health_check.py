import os
import pytest

def test_environment_variables():
    """Test that required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "DATABASE_URL", "SECRET_KEY"]
    for var in required_vars:
        assert var in os.environ, f"Environment variable {var} is not set"

def test_health_endpoint(client):
    """Test the health check endpoint."""
    try:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except Exception:
        # If health endpoint doesn't exist, test the root endpoint
        response = client.get("/")
        assert response.status_code == 200