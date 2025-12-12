"""Tests for User model."""

import pytest
from app.models.user import User


class TestUserModel:
    """Test User model functionality."""

    def test_user_creation(self):
        """Test basic user creation."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.is_active is True  # Default value
        assert user.created_at is not None

    def test_user_string_representation(self):
        """Test user string representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123"
        )

        user_str = str(user)
        assert "testuser" in user_str
        assert "test@example.com" in user_str

    def test_user_inactive(self):
        """Test inactive user creation."""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password="hashed_password_123",
            is_active=False
        )

        assert user.is_active is False

    def test_user_email_validation(self):
        """Test user with different email formats."""
        # Test valid emails
        valid_emails = [
            "user@example.com",
            "test.user@example.org",
            "user+tag@example.co.uk"
        ]

        for email in valid_emails:
            user = User(
                username=f"user_{email.split('@')[0]}",
                email=email,
                hashed_password="hashed_password_123"
            )
            assert user.email == email

    def test_user_username_variations(self):
        """Test user with different username formats."""
        usernames = ["user123", "test_user", "user-name", "UserName"]

        for username in usernames:
            user = User(
                username=username,
                email=f"{username.lower()}@example.com",
                hashed_password="hashed_password_123"
            )
            assert user.username == username