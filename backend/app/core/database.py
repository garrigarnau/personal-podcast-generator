"""
Database configuration and session management.

This module provides async SQLAlchemy engine and session management
for the Personal Podcast Generator application.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base class for all models
Base = declarative_base()

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://podcast_user:podcast_password@localhost:5432/podcast_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    # Use NullPool for testing environments to avoid connection pooling issues
    poolclass=NullPool if os.getenv("ENVIRONMENT") == "test" else None,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    This should only be used in development/testing.
    In production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections and dispose of the engine.

    Should be called on application shutdown.
    """
    await engine.dispose()
