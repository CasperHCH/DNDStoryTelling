"""
Simple demonstration showing the difference between mocked and real testing
This addresses your concern about whether extensive mocking makes tests meaningless.
"""

import pytest
from unittest.mock import Mock, patch

from app.auth.auth_handler import create_access_token, verify_password


class TestMockingProblemDemonstration:
    """
    This demonstrates why you're right to be concerned about excessive mocking
    """

    def test_heavily_mocked_password_test(self):
        """
        This mocked test will ALWAYS pass, even if the real password function is broken.
        This is the problem you identified - it doesn't test anything real!
        """
        with patch('app.auth.auth_handler.verify_password') as mock_verify:
            # Mock returns whatever we want
            mock_verify.return_value = True

            # This will pass even if verify_password is completely broken
            result = verify_password("any_password", "any_hash")
            assert result is True

            # But we learned nothing about whether the real function works!

    def test_real_password_verification(self):
        """
        This tests the actual function - and will catch real problems
        """
        # Test that we can verify a password we know is correct
        # Using short password to avoid bcrypt 72-byte limit
        password = "test123"

        # Test with a known good bcrypt hash for "test123"
        # This is a real bcrypt hash generated for the password "test123"
        known_hash = "$2b$12$GqiUyafAyV5jd3L0lOjzOuXwC5DCmW8s5LzFU6TKr7qBsrRRnLw6G"

        # This tests the REAL function - will fail if bcrypt is broken
        result = verify_password(password, known_hash)
        assert result is True

        # Test wrong password
        wrong_result = verify_password("wrongpass", known_hash)
        assert wrong_result is False

    def test_token_creation_real_vs_mocked(self):
        """
        Compare mocked vs real token creation
        """
        # === MOCKED VERSION ===
        with patch('app.auth.auth_handler.create_access_token') as mock_token:
            mock_token.return_value = "fake_token"

            # This will always return "fake_token" regardless of input
            mocked_result = create_access_token({"sub": "testuser"})
            assert mocked_result == "fake_token"
            # ✗ This tells us nothing about whether token creation actually works

        # === REAL VERSION ===
        # Test the actual function
        real_result = create_access_token({"sub": "testuser"})

        # Verify it's a real JWT token
        assert isinstance(real_result, str)
        assert len(real_result) > 50  # JWT tokens are long
        assert real_result.count('.') == 2  # JWT format: header.payload.signature
        # ✓ This tests actual functionality


class TestBetterTestingApproach:
    """
    Better approaches that balance speed with confidence
    """

    def test_token_format_validation(self):
        """
        Test the real function but focus on specific behavior
        """
        # Use the real function
        token = create_access_token({"sub": "testuser", "role": "admin"})

        # Test specific properties we care about
        assert isinstance(token, str)
        assert len(token) > 100  # Reasonable length
        assert token.count('.') == 2  # JWT structure
        assert not token.startswith('fake')  # Not a mock

        # Different input should produce different token
        token2 = create_access_token({"sub": "otheruser"})
        assert token != token2

    def test_strategic_mocking(self):
        """
        Example of strategic mocking - mock external dependencies, test our logic
        """
        # Mock external time dependency, but test our token logic
        with patch('app.auth.auth_handler.datetime') as mock_dt:
            from datetime import datetime, timedelta

            # Set a fixed time
            fixed_time = datetime(2024, 1, 1, 12, 0, 0)
            mock_dt.utcnow.return_value = fixed_time
            mock_dt.timedelta = timedelta  # Keep real timedelta

            # Test our token creation with predictable time
            token = create_access_token({"sub": "testuser"})

            # Verify it's still a real token, just with controlled time
            assert isinstance(token, str)
            assert token.count('.') == 2


class TestYourConcernIsValid:
    """
    Demonstrates why your concern about mocking is absolutely correct
    """

    def test_mock_hides_real_problems(self):
        """
        This shows how mocking can hide actual bugs
        """
        # If we mock everything, we never catch real issues
        with patch('app.auth.auth_handler.get_password_hash') as mock_hash, \
             patch('app.auth.auth_handler.verify_password') as mock_verify:

            mock_hash.return_value = "mocked_hash"
            mock_verify.return_value = True

            # This test passes but is completely meaningless
            from app.auth.auth_handler import get_password_hash, verify_password

            hashed = get_password_hash("password_too_long_will_break_in_real_system" * 10)
            verified = verify_password("any_password", hashed)

            assert hashed == "mocked_hash"
            assert verified is True

            # ❌ This passed but told us NOTHING about real behavior
            # ❌ Real system would fail with "password too long" error
            # ❌ Mocked tests hide this completely


def test_conclusion_about_mocking():
    """
    Your instinct is correct: heavy mocking often makes tests meaningless.

    Better approach:
    1. Test real functions when possible
    2. Mock only external dependencies (databases, APIs, file systems)
    3. Use integration tests for critical paths
    4. Mock strategically, not extensively
    """
    # Test real token creation
    token = create_access_token({"sub": "user123"})

    # Verify real properties
    assert isinstance(token, str)
    assert len(token) > 50
    assert '.' in token  # JWT structure

    # This gives us real confidence that token creation works