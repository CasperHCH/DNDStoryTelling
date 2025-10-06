"""Comprehensive tests for authentication routes with proper mocking."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.main import app
from app.models.user import User


class TestAuthRoutes:
    """Test cases for authentication endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_login_endpoint_exists(self):
        """Test that the login endpoint exists."""
        response = self.client.post("/auth/token")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_register_endpoint_exists(self):
        """Test that the register endpoint exists."""
        response = self.client.post("/auth/register")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    @patch('app.models.database.get_db')
    @patch('app.auth.auth_handler.create_access_token')
    @patch('app.auth.auth_handler.verify_password')
    def test_login_success(self, mock_verify, mock_token, mock_get_db):
        """Test successful user login."""
        # Setup mock database session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        
        # Mock user from database
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"
        
        # Mock the database query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result
        
        # Setup other mocks
        mock_verify.return_value = True
        mock_token.return_value = "fake_jwt_token"

        # Use form data as expected by OAuth2PasswordRequestForm
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }

        response = self.client.post("/auth/token", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["access_token"] == "fake_jwt_token"
        assert data["token_type"] == "bearer"

    @patch('app.models.database.get_db')
    def test_login_invalid_credentials(self, mock_get_db):
        """Test login with invalid credentials."""
        # Setup mock database session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        
        # Mock no user found in database
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        login_data = {
            "username": "wronguser",
            "password": "wrongpass"
        }

        response = self.client.post("/auth/token", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_missing_username(self):
        """Test login with missing username."""
        login_data = {
            "password": "testpass"
        }

        response = self.client.post("/auth/token", data=login_data)

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self):
        """Test login with missing password."""
        login_data = {
            "username": "testuser"
        }

        response = self.client.post("/auth/token", data=login_data)

        assert response.status_code == 422  # Validation error

    @patch('app.models.database.get_db')
    @patch('app.auth.auth_handler.get_password_hash')
    def test_register_success(self, mock_hash, mock_get_db):
        """Test successful user registration."""
        # Setup mock database session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        
        # Mock that user doesn't exist (both queries return None)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Mock password hashing
        mock_hash.return_value = "hashed_password"
        
        # Mock user creation (add method and flush/refresh)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        register_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/auth/register", json=register_data)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "User created successfully"

    @patch('app.models.database.get_db')
    def test_register_username_taken(self, mock_get_db):
        """Test registration with taken username."""
        # Setup mock database session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        
        # Mock existing user found (first query for username)
        mock_existing_user = MagicMock()
        mock_existing_user.id = 1
        mock_existing_user.username = "existinguser"
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_user
        mock_session.execute.return_value = mock_result

        register_data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/auth/register", json=register_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @patch('app.models.database.get_db')
    def test_register_email_taken(self, mock_get_db):
        """Test registration with taken email."""
        # Setup mock database session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session
        
        # First call (username check) returns None, second call (email check) returns existing user
        mock_existing_user = MagicMock()
        mock_existing_user.id = 1
        mock_existing_user.email = "existing@example.com"
        
        mock_result = AsyncMock()
        # First call returns None (username not taken), second call returns user (email taken)
        mock_result.scalar_one_or_none.side_effect = [None, mock_existing_user]
        mock_session.execute.return_value = mock_result

        register_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/auth/register", json=register_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_register_invalid_email(self):
        """Test registration with invalid email format."""
        register_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": "newpass123"
        }

        response = self.client.post("/auth/register", json=register_data)

        # Should return validation error
        assert response.status_code == 422

    def test_register_missing_fields(self):
        """Test registration with missing required fields."""
        # Missing username
        register_data = {
            "email": "test@example.com",
            "password": "testpass"
        }

        response = self.client.post("/auth/register", json=register_data)
        assert response.status_code == 422

        # Missing email
        register_data = {
            "username": "testuser",
            "password": "testpass"
        }

        response = self.client.post("/auth/register", json=register_data)
        assert response.status_code == 422

        # Missing password
        register_data = {
            "username": "testuser",
            "email": "test@example.com"
        }

        response = self.client.post("/auth/register", json=register_data)
        assert response.status_code == 422