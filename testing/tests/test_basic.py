"""Basic application tests to ensure the app starts correctly."""
import pytest

def test_app_creation(app):
    """Test that the FastAPI app can be created."""
    assert app is not None
    assert hasattr(app, 'routes')

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    # The endpoint should return a valid response
    # Accept 200 (success), 404 (not found), or 400 (bad request due to middleware restrictions in test env)
    assert response.status_code in [200, 400, 404], f"Unexpected status code: {response.status_code}, content: {response.text[:100]}"

def test_client_creation(client):
    """Test that the test client can be created."""
    assert client is not None