import os
import pytest

def test_environment_variables():
    """Test that required environment variables are set."""
    # In test environment, OPENAI_API_KEY is optional
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    for var in required_vars:
        assert var in os.environ, f"Environment variable {var} is not set"

    # Check that ENVIRONMENT is set to test
    assert os.environ.get("ENVIRONMENT") == "test", "ENVIRONMENT should be set to 'test' in test mode"

def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    # Check that the response has the expected structure
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data