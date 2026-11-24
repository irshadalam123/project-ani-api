"""Async SQLAlchemy engine and session factory.

This module is the *only* place that opens a database connection.
Every postgres repository receives an ``AsyncSession`` from the caller
(``build_container``); nothing here runs at import time.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(database_url: str) -> AsyncEngine:
    """Return an async engine for *database_url*.

    The URL must use the ``postgresql+asyncpg://`` scheme. If another PostgreSQL
    scheme is provided, it is automatically normalized to ``postgresql+asyncpg://``.
    """
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql+psycopg2://"):
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    return create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a callable that produces ``AsyncSession`` objects."""
    return async_sessionmaker(engine, expire_on_commit=False)
