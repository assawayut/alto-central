"""Local PostgreSQL database for application data (READ-WRITE).

This module provides a connection to the local PostgreSQL database
for storing application-specific data like ML models, cache, and chat history.
"""

from typing import AsyncGenerator, Optional
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


class LocalDatabase:
    """Local PostgreSQL database connection (READ-WRITE).

    This database is used for:
    - ML model metadata and registry
    - Optimization results cache
    - Chat history and sessions
    - Query cache
    - Feature store
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._engine = None
        self._session_factory = None
        self._connected = False

    async def connect(self) -> None:
        """Initialize the database engine and session factory."""
        try:
            self._engine = create_async_engine(
                self.database_url,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            self._connected = True
            logger.info("Connected to local PostgreSQL (READ-WRITE)")
        except Exception as e:
            logger.error(f"Failed to connect to local database: {e}")
            self._connected = False

    async def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._connected = False
            logger.info("Closed local database connection")

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if not self._session_factory:
            raise RuntimeError("Database not connected")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """Create all tables defined in models."""
        if self._engine:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Created local database tables")


# Global instance
_local_db: Optional[LocalDatabase] = None


async def init_local_db() -> None:
    """Initialize the local database connection.

    This is optional - if the local database is not available,
    the application will continue without it (ML, optimization,
    and chat features will be unavailable).
    """
    global _local_db
    try:
        _local_db = LocalDatabase(settings.LOCAL_DB_URL)
        await _local_db.connect()

        # Create tables if they don't exist
        if _local_db.is_connected:
            await _local_db.create_tables()
    except Exception as e:
        logger.warning(f"Local database not available (optional): {e}")
        logger.info("Application will continue without local database - ML/optimization/chat features will use mock data")


async def close_local_db() -> None:
    """Close the local database connection."""
    global _local_db
    if _local_db:
        await _local_db.close()


def get_local_db() -> Optional[LocalDatabase]:
    """Get the local database instance (may be None if unavailable)."""
    return _local_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting a database session."""
    db = get_local_db()
    async for session in db.get_session():
        yield session
