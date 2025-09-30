"""Database configuration and connection management."""

import logging
from typing import AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.pool import NullPool

from app.config import get_settings

logger = logging.getLogger(__name__)

def _get_database_config():
    """Get database configuration lazily."""
    settings = get_settings()

    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")

    # Ensure async drivers are used for async operations
    database_url = settings.DATABASE_URL
    if "postgresql://" in database_url and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif "sqlite://" in database_url and "+aiosqlite" not in database_url:
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

    return database_url, settings

# Initialize database configuration lazily
DATABASE_URL, settings = _get_database_config()

# Configure engine with connection pooling
if "test" in DATABASE_URL:
    # Use NullPool for testing to avoid connection issues
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,
    )
else:
    # Use connection pooling for production
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,  # Number of connections to maintain in pool
        max_overflow=10,  # Additional connections beyond pool_size
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,  # Recycle connections every hour
    )

# Configure session factory
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
)

Base = declarative_base()

async def init_db() -> None:
    """Initialize database tables and run health check."""
    try:
        async with engine.begin() as conn:
            # Test connection first
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")

            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def health_check_db() -> bool:
    """Check database health."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False