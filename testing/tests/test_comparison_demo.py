"""
Demonstration of different testing approaches: Mocked vs Real vs Unit Testing
This file shows the trade-offs between different testing strategies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.auth.auth_handler import get_password_hash, verify_password, create_access_token


class TestMockedApproach:
    """
    Heavy Mocking Approach - Tests behavior but not actual functionality

    Pros:
    - Fast execution
    - Tests don't depend on external systems
    - Can test error conditions easily

    Cons:
    - May not catch real integration issues
    - Can give false confidence
    - May test mocks instead of real code
    """

    def test_login_with_heavy_mocking(self):
        """Example of heavily mocked test - fast but potentially misleading"""
        with patch('app.models.database.get_db') as mock_db, \
             patch('app.routes.auth.authenticate_user') as mock_auth, \
             patch('app.auth.auth_handler.create_access_token') as mock_token:

            # Mock everything
            mock_auth.return_value = {"username": "testuser", "id": 1}
            mock_token.return_value = "fake_token"

            client = TestClient(app)
            response = client.post("/auth/token", data={
                "username": "testuser",
                "password": "password"
            })

            # This passes but tells us nothing about real functionality
            assert response.status_code == 200
            assert response.json() == {"access_token": "fake_token", "token_type": "bearer"}


class TestUnitApproach:
    """
    Unit Testing Approach - Tests individual functions in isolation

    Pros:
    - Tests specific business logic
    - Fast execution
    - Clear failure points

    Cons:
    - Doesn't test integration between components
    - May miss system-level issues
    """

    def test_password_hashing_unit(self):
        """Test just the password hashing function"""
        password = "testpass123"

        # Test the actual function
        hashed = get_password_hash(password)

        # Verify it's actually hashed (not the same)
        assert hashed != password
        assert len(hashed) > 20  # bcrypt hashes are long
        assert hashed.startswith('$2b$')  # bcrypt format

        # Test verification works
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpass", hashed) is False

    def test_token_creation_unit(self):
        """Test token creation in isolation"""
        user_data = {"sub": "testuser"}

        # Test actual function
        token = create_access_token(data=user_data)

        # Verify token properties
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        assert token.count('.') == 2  # JWT has 3 parts separated by dots


class TestIntegrationApproach:
    """
    Integration Testing Approach - Tests components working together

    Pros:
    - Tests real system behavior
    - Catches integration issues
    - Higher confidence in actual functionality

    Cons:
    - Slower execution
    - More complex setup
    - Harder to isolate failures
    """

    def test_password_flow_integration(self):
        """Test the full password hashing and verification flow"""
        password = "integrationtest123"

        # Step 1: Hash the password (real function)
        hashed = get_password_hash(password)

        # Step 2: Verify the password (real function)
        verification_result = verify_password(password, hashed)

        # Step 3: Test wrong password (real function)
        wrong_verification = verify_password("wrongpassword", hashed)

        # Assert the full flow works
        assert verification_result is True
        assert wrong_verification is False
        assert hashed != password


class TestShowcaseComparison:
    """
    Direct comparison showing why different approaches matter
    """

    def test_mocked_always_passes(self):
        """This mocked test will always pass, even if the real function is broken"""
        with patch('app.auth.auth_handler.get_password_hash') as mock_hash:
            mock_hash.return_value = "fake_hash"

            # This will pass even if get_password_hash is completely broken
            result = get_password_hash("any_password")
            assert result == "fake_hash"

    def test_real_function_might_fail(self):
        """This test uses the real function and will fail if there are actual issues"""
        try:
            # Use the actual function - will fail if bcrypt has issues
            password = "short"  # Keep it short to avoid bcrypt 72-byte limit
            hashed = get_password_hash(password)

            # Test that it actually worked
            assert hashed != password
            assert verify_password(password, hashed) is True

        except Exception as e:
            # This catches real issues that mocked tests would miss
            pytest.fail(f"Real function failed: {e}")


if __name__ == "__main__":
    print("This file demonstrates different testing approaches.")
    print("Run with: pytest testing/tests/test_comparison_demo.py -v")