"""Alembic environment configuration for async SQLAlchemy migrations."""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
from logging.config import fileConfig

from alembic import context
from app.core.config import get_settings
from app.models.orm import Base
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ORM metadata for 'autogenerate' support
target_metadata = Base.metadata


def get_url() -> str:
    """Retrieve database URL from alembic.ini, DATABASE_URL, or app settings."""
    url = config.get_main_option("sqlalchemy.url")
    if not url or url.startswith("driver://"):
        url = os.getenv("DATABASE_URL") or get_settings().database_url

    if not url or not url.strip():
        raise RuntimeError(
            "PostgreSQL is not configured. DATABASE_URL is empty and no valid "
            "sqlalchemy.url was found in alembic.ini."
        )

    # Normalize to asyncpg driver for async SQLAlchemy
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations within a connection transaction."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(connectable: AsyncEngine) -> None:
    """Run migrations asynchronously using the provided engine."""
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async SQLAlchemy engine."""
    url = get_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool_exec:
            pool_exec.submit(lambda: asyncio.run(run_async_migrations(connectable))).result()
    else:
        asyncio.run(run_async_migrations(connectable))


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

