"""
Test Configuration for Strategic Testing Approach
This replaces the heavily mocked tests with a balanced approach.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_db


def pytest_configure():
    """Configure pytest for strategic testing."""
    # Set up test markers
    pytest.mark.unit = pytest.mark.unit
    pytest.mark.integration = pytest.mark.integration
    pytest.mark.functional = pytest.mark.functional


# Test Database Setup (only external dependency we "mock")
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_strategic.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for tests - only thing we 'mock'."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create and clean up test database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override."""
    # Override only the database dependency
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Real user data for testing - no mocking."""
    return {
        "username": "realuser",
        "email": "real@example.com",
        "password": "realpass123"
    }


# Custom test markers for organization
def pytest_configure(config):
    """Configure custom test markers."""
    config.addinivalue_line("markers", "unit: Unit tests - test individual functions")
    config.addinivalue_line("markers", "integration: Integration tests - test components together")
    config.addinivalue_line("markers", "functional: Functional tests - test complete workflows")
    config.addinivalue_line("markers", "real: Tests using real implementations (no mocking)")
    config.addinivalue_line("markers", "strategic: Tests with strategic, minimal mocking")