"""Redis access used for health checks, Celery, and short-lived state.

Permanent business records are not stored only in Redis. Repository
implementations remain the source of truth and are in-memory until PostgreSQL
is added.
"""

from __future__ import annotations

from typing import Protocol

import redis.asyncio as aioredis


class RedisService(Protocol):
    async def ping(self) -> bool: ...

    async def close(self) -> None: ...


class LiveRedisService:
    """Short-lived Redis commands. A failed ping does not crash the API."""

    def __init__(self, url: str) -> None:
        self._url = url

    async def ping(self) -> bool:
        client = aioredis.from_url(self._url, socket_connect_timeout=1, socket_timeout=1)
        try:
            response = await client.ping()
            return bool(response)
        except Exception:
            return False
        finally:
            await client.aclose()

    async def close(self) -> None:
        return None


class FakeRedisService:
    """Used by tests so readiness does not require a running Redis."""

    def __init__(self, healthy: bool = True) -> None:
        self.healthy = healthy

    async def ping(self) -> bool:
        return self.healthy

    async def close(self) -> None:
        return None
