"""Integration tests for authentication routes using real database."""

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_db
from app.models.user import User
from app.auth.auth_handler import get_password_hash


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_test_db():
    """Override database dependency for tests."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create test database tables and clean up after each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(test_db):
    """Create test client with test database."""
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user():
    """Create a test user in the database."""
    async with TestSessionLocal() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword123"),
            is_active=True,
            is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


class TestAuthenticationIntegration:
    """Integration tests for authentication with real database operations."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client):
        """Test registering a completely new user."""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }

        response = await client.post("/auth/register", json=register_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User created successfully"

        # Verify user was actually created in database
        async with TestSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "newuser")
            )
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.email == "newuser@example.com"
            assert user.is_active is True
            # Verify password was hashed (not stored as plain text)
            assert user.hashed_password != "securepassword123"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user):
        """Test registering with existing username."""
        register_data = {
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "securepassword123"
        }

        response = await client.post("/auth/register", json=register_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        """Test registering with existing email."""
        register_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Already exists
            "password": "securepassword123"
        }

        response = await client.post("/auth/register", json=register_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        response = await client.post("/auth/token", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_login_invalid_username(self, client):
        """Test login with non-existent username."""
        login_data = {
            "username": "nonexistentuser",
            "password": "anypassword"
        }

        response = await client.post("/auth/token", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = await client.post("/auth/token", data=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client):
        """Test login with missing required fields."""
        # Missing password
        response = await client.post("/auth/token", data={"username": "testuser"})
        assert response.status_code == 422

        # Missing username
        response = await client.post("/auth/token", data={"password": "password"})
        assert response.status_code == 422

        # Missing both
        response = await client.post("/auth/token", data={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_register_invalid_email_format(self, client):
        """Test registration with invalid email format."""
        register_data = {
            "username": "newuser",
            "email": "invalid-email-format",
            "password": "securepassword123"
        }

        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_register_password_too_short(self, client):
        """Test registration with password that's too short."""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "short"  # Less than 8 characters
        }

        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_register_invalid_username_format(self, client):
        """Test registration with invalid username format."""
        register_data = {
            "username": "ab",  # Too short
            "email": "newuser@example.com",
            "password": "securepassword123"
        }

        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_full_auth_flow(self, client):
        """Test complete authentication flow: register -> login -> use token."""
        # 1. Register new user
        register_data = {
            "username": "flowuser",
            "email": "flowuser@example.com",
            "password": "flowpassword123"
        }

        register_response = await client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201

        # 2. Login with new user
        login_data = {
            "username": "flowuser",
            "password": "flowpassword123"
        }

        login_response = await client.post("/auth/token", data=login_data)
        assert login_response.status_code == 200

        token_data = login_response.json()
        access_token = token_data["access_token"]

        # 3. Use token to access protected endpoint (if you have any)
        # This would test token validation
        headers = {"Authorization": f"Bearer {access_token}"}

        # Test with a protected endpoint if available
        # For now, just verify the token exists and has expected format
        assert access_token
        assert "." in access_token  # JWT tokens have dots