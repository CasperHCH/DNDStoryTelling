"""Basic application tests to ensure the app starts correctly."""
import pytest

def test_app_creation(app):
    """Test that the FastAPI app can be created."""
    assert app is not None
    assert hasattr(app, 'routes')

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    # Should return either the main page or an API response
    assert response.status_code in [200, 404]

def test_client_creation(client):
    """Test that the test client can be created."""
    assert client is not None