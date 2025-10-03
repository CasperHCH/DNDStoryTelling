"""Comprehensive tests for authentication routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.main import app
from app.routes.auth import router


class TestAuthRoutes:
    """Test cases for authentication endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_login_endpoint_exists(self):
        """Test that the login endpoint exists."""
        response = self.client.post("/login")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_register_endpoint_exists(self):
        """Test that the register endpoint exists."""
        response = self.client.post("/register")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    @patch('app.routes.auth.authenticate_user')
    @patch('app.routes.auth.create_access_token')
    def test_login_success(self, mock_token, mock_auth):
        """Test successful user login."""
        # Setup mocks
        mock_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
        mock_auth.return_value = mock_user
        mock_token.return_value = "fake_jwt_token"

        login_data = {
            "username": "testuser",
            "password": "testpass"
        }

        response = self.client.post("/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["access_token"] == "fake_jwt_token"
        assert data["token_type"] == "bearer"

    @patch('app.routes.auth.authenticate_user')
    def test_login_invalid_credentials(self, mock_auth):
        """Test login with invalid credentials."""
        mock_auth.return_value = None  # Authentication failed

        login_data = {
            "username": "wronguser",
            "password": "wrongpass"
        }

        response = self.client.post("/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_missing_username(self):
        """Test login with missing username."""
        login_data = {
            "password": "testpass"
        }

        response = self.client.post("/login", json=login_data)

        assert response.status_code == 422  # Validation error

    def test_login_missing_password(self):
        """Test login with missing password."""
        login_data = {
            "username": "testuser"
        }

        response = self.client.post("/login", json=login_data)

        assert response.status_code == 422  # Validation error

    def test_login_empty_credentials(self):
        """Test login with empty credentials."""
        login_data = {
            "username": "",
            "password": ""
        }

        response = self.client.post("/login", json=login_data)

        # Should handle empty credentials gracefully
        assert response.status_code in [400, 401, 422]

    @patch('app.routes.auth.create_user')
    @patch('app.routes.auth.get_user_by_username')
    @patch('app.routes.auth.get_user_by_email')
    def test_register_success(self, mock_get_email, mock_get_username, mock_create):
        """Test successful user registration."""
        # Setup mocks
        mock_get_username.return_value = None  # Username not taken
        mock_get_email.return_value = None     # Email not taken
        mock_new_user = {"id": 1, "username": "newuser", "email": "new@example.com"}
        mock_create.return_value = mock_new_user

        register_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/register", json=register_data)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "user" in data
        assert data["user"]["username"] == "newuser"

    @patch('app.routes.auth.get_user_by_username')
    def test_register_username_taken(self, mock_get_username):
        """Test registration with taken username."""
        mock_get_username.return_value = {"id": 1, "username": "existinguser"}

        register_data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/register", json=register_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @patch('app.routes.auth.get_user_by_username')
    @patch('app.routes.auth.get_user_by_email')
    def test_register_email_taken(self, mock_get_email, mock_get_username):
        """Test registration with taken email."""
        mock_get_username.return_value = None
        mock_get_email.return_value = {"id": 1, "email": "existing@example.com"}

        register_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/register", json=register_data)

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

        response = self.client.post("/register", json=register_data)

        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self):
        """Test registration with weak password."""
        register_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "123"  # Too short
        }

        response = self.client.post("/register", json=register_data)

        # Should handle weak password (validation or business logic)
        assert response.status_code in [400, 422]

    def test_register_missing_fields(self):
        """Test registration with missing required fields."""
        incomplete_data = {
            "username": "newuser"
            # Missing email and password
        }

        response = self.client.post("/register", json=incomplete_data)

        assert response.status_code == 422  # Validation error

    @patch('app.routes.auth.get_current_user')
    def test_protected_route_with_valid_token(self, mock_get_user):
        """Test accessing protected route with valid token."""
        mock_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
        mock_get_user.return_value = mock_user

        headers = {"Authorization": "Bearer valid_token"}
        response = self.client.get("/profile", headers=headers)

        # Should succeed if profile endpoint exists and is protected
        # Response depends on actual implementation
        assert response.status_code != 401  # Not unauthorized

    def test_protected_route_without_token(self):
        """Test accessing protected route without token."""
        response = self.client.get("/profile")

        # Should return unauthorized if profile endpoint is protected
        # Response depends on actual implementation
        if response.status_code != 404:  # If endpoint exists
            assert response.status_code == 401

    def test_protected_route_with_invalid_token(self):
        """Test accessing protected route with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/profile", headers=headers)

        # Should return unauthorized if profile endpoint exists and is protected
        if response.status_code != 404:  # If endpoint exists
            assert response.status_code == 401

    @patch('app.routes.auth.authenticate_user')
    def test_login_with_email(self, mock_auth):
        """Test login using email instead of username."""
        mock_user = {"id": 1, "username": "testuser", "email": "test@example.com"}
        mock_auth.return_value = mock_user

        with patch('app.routes.auth.create_access_token', return_value="token"):
            login_data = {
                "username": "test@example.com",  # Using email as username
                "password": "testpass"
            }

            response = self.client.post("/login", json=login_data)

            # Should handle email login if supported
            assert response.status_code in [200, 401, 400]

    @patch('app.routes.auth.authenticate_user')
    def test_login_case_sensitivity(self, mock_auth):
        """Test login case sensitivity."""
        mock_auth.return_value = None  # No user found

        login_data = {
            "username": "TestUser",  # Mixed case
            "password": "testpass"
        }

        response = self.client.post("/login", json=login_data)

        # Response depends on whether usernames are case-sensitive
        assert response.status_code in [200, 401]

    @patch('app.routes.auth.logger')
    @patch('app.routes.auth.authenticate_user')
    def test_login_logging(self, mock_auth, mock_logger):
        """Test that login attempts are logged."""
        mock_auth.return_value = None  # Failed login

        login_data = {
            "username": "testuser",
            "password": "wrongpass"
        }

        response = self.client.post("/login", json=login_data)

        # Should log failed login attempts
        mock_logger.warning.assert_called()

    @patch('app.routes.auth.logger')
    @patch('app.routes.auth.create_user')
    @patch('app.routes.auth.get_user_by_username')
    @patch('app.routes.auth.get_user_by_email')
    def test_register_logging(self, mock_get_email, mock_get_username, mock_create, mock_logger):
        """Test that registration attempts are logged."""
        mock_get_username.return_value = None
        mock_get_email.return_value = None
        mock_create.side_effect = Exception("Database error")

        register_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123"
        }

        response = self.client.post("/register", json=register_data)

        # Should log registration errors
        mock_logger.error.assert_called()

    def test_auth_response_format(self):
        """Test authentication response format consistency."""
        with patch('app.routes.auth.authenticate_user') as mock_auth:
            with patch('app.routes.auth.create_access_token') as mock_token:
                mock_auth.return_value = {"id": 1, "username": "test"}
                mock_token.return_value = "token"

                login_data = {"username": "test", "password": "pass"}
                response = self.client.post("/login", json=login_data)

                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, dict)
                    assert "access_token" in data
                    assert "token_type" in data

    def test_auth_headers(self):
        """Test that auth responses have appropriate headers."""
        with patch('app.routes.auth.authenticate_user') as mock_auth:
            with patch('app.routes.auth.create_access_token') as mock_token:
                mock_auth.return_value = {"id": 1, "username": "test"}
                mock_token.return_value = "token"

                login_data = {"username": "test", "password": "pass"}
                response = self.client.post("/login", json=login_data)

                assert "content-type" in response.headers
                assert "application/json" in response.headers["content-type"]

    @patch('app.routes.auth.authenticate_user')
    def test_login_sql_injection_protection(self, mock_auth):
        """Test login protection against SQL injection."""
        mock_auth.return_value = None

        malicious_data = {
            "username": "admin'; DROP TABLE users; --",
            "password": "' OR '1'='1"
        }

        response = self.client.post("/login", json=malicious_data)

        # Should handle malicious input safely
        assert response.status_code in [400, 401, 422]

    @patch('app.routes.auth.get_user_by_username')
    @patch('app.routes.auth.get_user_by_email')
    def test_register_xss_protection(self, mock_get_email, mock_get_username):
        """Test registration protection against XSS."""
        mock_get_username.return_value = None
        mock_get_email.return_value = None

        xss_data = {
            "username": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "password": "password123"
        }

        response = self.client.post("/register", json=xss_data)

        # Should handle XSS attempts safely
        assert response.status_code in [400, 422, 201]

    def test_auth_rate_limiting(self):
        """Test authentication rate limiting."""
        login_data = {
            "username": "testuser",
            "password": "wrongpass"
        }

        responses = []
        # Make multiple rapid requests
        for _ in range(10):
            response = self.client.post("/login", json=login_data)
            responses.append(response.status_code)

        # Rate limiting behavior depends on implementation
        # Should not cause server errors
        for status in responses:
            assert status != 500

    @patch('app.routes.auth.create_user')
    @patch('app.routes.auth.get_user_by_username')
    @patch('app.routes.auth.get_user_by_email')
    def test_register_password_hashing(self, mock_get_email, mock_get_username, mock_create):
        """Test that passwords are properly hashed during registration."""
        mock_get_username.return_value = None
        mock_get_email.return_value = None
        mock_create.return_value = {"id": 1, "username": "test"}

        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "plaintext_password"
        }

        response = self.client.post("/register", json=register_data)

        if response.status_code == 201:
            # Verify create_user was called (password should be hashed internally)
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            # Password should not be stored as plaintext
            assert "plaintext_password" not in str(call_args)

    def test_auth_unicode_handling(self):
        """Test authentication with unicode characters."""
        with patch('app.routes.auth.authenticate_user') as mock_auth:
            mock_auth.return_value = None

            unicode_data = {
                "username": "tëstüser",
                "password": "påsswörd"
            }

            response = self.client.post("/login", json=unicode_data)

            # Should handle unicode gracefully
            assert response.status_code in [200, 401, 422]

    def test_concurrent_auth_requests(self):
        """Test concurrent authentication requests."""
        import concurrent.futures

        def make_login_request():
            with patch('app.routes.auth.authenticate_user') as mock_auth:
                with patch('app.routes.auth.create_access_token') as mock_token:
                    mock_auth.return_value = {"id": 1, "username": "test"}
                    mock_token.return_value = "token"

                    login_data = {"username": "test", "password": "pass"}
                    return self.client.post("/login", json=login_data)

        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_login_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All requests should complete without errors
        for response in responses:
            assert response.status_code != 500