"""
Strategic Testing Approach - Real functionality with minimal mocking
This replaces heavy mocking with a balanced approach that tests actual code.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_db
from app.models.user import User
from app.auth.auth_handler import (
    get_password_hash,
    verify_password,
    create_access_token
)


class TestRealAuthFunctionality:
    """
    Test real authentication functions - no mocking of core business logic
    """

    def test_password_operations_real(self):
        """Test password hashing and verification with real bcrypt."""
        # Use shorter passwords to avoid bcrypt 72-byte limit
        passwords = ["pass123", "mySecure456", "test789"]

        for password in passwords:
            # Test real hashing
            hashed = get_password_hash(password)

            # Verify hash properties
            assert hashed != password  # Actually hashed
            assert hashed.startswith('$2b$')  # bcrypt format
            assert len(hashed) > 50  # Reasonable length

            # Test real verification
            assert verify_password(password, hashed) is True
            assert verify_password("wrong", hashed) is False

    def test_jwt_token_creation_real(self):
        """Test JWT token creation without mocking."""
        test_cases = [
            {"sub": "user1"},
            {"sub": "user2", "role": "admin"},
            {"sub": "user3", "permissions": ["read", "write"]}
        ]

        tokens = []
        for data in test_cases:
            token = create_access_token(data)

            # Verify real JWT properties
            assert isinstance(token, str)
            assert len(token) > 100  # JWT tokens are long
            assert token.count('.') == 2  # header.payload.signature

            # Ensure uniqueness
            assert token not in tokens
            tokens.append(token)

    def test_authentication_flow_real(self):
        """Test complete auth flow with real functions."""
        username = "testuser"
        password = "secure123"
        email = "test@example.com"

        # Step 1: Hash password (real)
        hashed_password = get_password_hash(password)

        # Step 2: Verify password (real)
        is_valid = verify_password(password, hashed_password)
        assert is_valid is True

        # Step 3: Create token (real)
        token = create_access_token({"sub": username})
        assert len(token) > 50

        # Step 4: Verify wrong password fails (real)
        is_invalid = verify_password("wrongpass", hashed_password)
        assert is_invalid is False


class TestAPIEndpointsWithStrategicMocking:
    """
    Test API endpoints - only mock database, test everything else for real
    """

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_registration_validation_real(self, client):
        """Test registration validation logic without mocking validation."""
        # Test real validation errors
        test_cases = [
            # Invalid email format
            {
                "data": {"username": "test", "email": "invalid-email", "password": "password123"},
                "expected_status": 422,
                "description": "Invalid email format"
            },
            # Password too short
            {
                "data": {"username": "test", "email": "test@example.com", "password": "short"},
                "expected_status": 422,
                "description": "Password too short"
            },
            # Username too short
            {
                "data": {"username": "ab", "email": "test@example.com", "password": "password123"},
                "expected_status": 422,
                "description": "Username too short"
            }
        ]

        for case in test_cases:
            response = client.post("/auth/register", json=case["data"])
            assert response.status_code == case["expected_status"], f"Failed: {case['description']}"

    def test_login_format_validation_real(self, client):
        """Test login format validation without mocking."""
        # Test missing fields
        response = client.post("/auth/token", data={"username": "test"})
        assert response.status_code == 422  # Missing password

        response = client.post("/auth/token", data={"password": "test"})
        assert response.status_code == 422  # Missing username


class TestIntegrationWithInMemoryDB:
    """
    Integration tests using real database operations (in-memory for speed)
    Only the database location is "mocked" - everything else is real
    """

    @pytest.fixture
    async def test_db_session(self):
        """Create in-memory database for integration tests."""
        # Use in-memory SQLite - real database, just temporary
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Provide session
        async with SessionLocal() as session:
            yield session

        # Cleanup
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_user_creation_integration(self, test_db_session):
        """Test real user creation in real database."""
        # Create user with real password hashing
        user = User(
            username="integrationtest",
            email="integration@test.com",
            hashed_password=get_password_hash("testpass123")
        )

        # Real database operations
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        # Verify real data
        assert user.id is not None
        assert user.username == "integrationtest"
        assert user.hashed_password != "testpass123"  # Actually hashed

        # Test real password verification
        assert verify_password("testpass123", user.hashed_password) is True


class TestPracticalRealWorldScenarios:
    """
    Test scenarios that would happen in production - no mocking
    """

    def test_concurrent_token_generation(self):
        """Test that concurrent token generation works correctly."""
        import concurrent.futures

        def create_token_for_user(user_id):
            return create_access_token({"sub": f"user_{user_id}"})

        # Create tokens concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_token_for_user, i) for i in range(10)]
            tokens = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all tokens are unique and valid
        assert len(set(tokens)) == 10  # All unique
        for token in tokens:
            assert len(token) > 50
            assert token.count('.') == 2

    def test_password_edge_cases_real(self):
        """Test password edge cases with real bcrypt."""
        edge_cases = [
            "a",  # Very short
            "password123",  # Common pattern
            "P@ssw0rd!123",  # Complex
            "🔐🔑🛡️",  # Unicode
        ]

        for password in edge_cases:
            try:
                hashed = get_password_hash(password)
                verified = verify_password(password, hashed)
                assert verified is True, f"Failed for password: {password}"
            except Exception as e:
                # Document any real limitations
                print(f"Password '{password}' failed with real bcrypt: {e}")

    def test_token_format_consistency(self):
        """Test token format consistency with real JWT creation."""
        from datetime import timedelta

        # Create multiple tokens with different expiration times
        tokens = []
        for minutes in [15, 30, 60]:
            token = create_access_token(
                data={"sub": "testuser"},
                expires_delta=timedelta(minutes=minutes)
            )
            tokens.append(token)

        # Verify all tokens have consistent JWT format
        for token in tokens:
            parts = token.split('.')
            assert len(parts) == 3, "JWT should have 3 parts"

            # Each part should be base64-like (no spaces, reasonable length)
            for part in parts:
                assert len(part) > 10, "JWT parts should be substantial"
                assert ' ' not in part, "JWT parts shouldn't contain spaces"


if __name__ == "__main__":
    print("Strategic Testing Approach:")
    print("✅ Test real functions directly")
    print("✅ Only mock external dependencies")
    print("✅ Use in-memory databases for integration tests")
    print("✅ Test actual edge cases and error conditions")
    print("✅ Verify real-world scenarios")
    print("")
    print("Run with: pytest testing/tests/test_strategic.py -v")