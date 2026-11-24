"""Rate limiting.

The default limiter is in-memory so the API can run before Redis is up.
A Redis-backed limiter is available when ``RATE_LIMIT_BACKEND=redis``.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Protocol

import redis


class RateLimiter(Protocol):
    def allow(self, key: str, limit: int, window_seconds: int) -> bool: ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            recent = [stamp for stamp in self._hits[key] if now - stamp < window_seconds]
            if len(recent) >= limit:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            return True


class RedisRateLimiter:
    """Fixed-window counter. Falls open if Redis cannot be reached."""

    def __init__(self, url: str) -> None:
        self._url = url

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            client = redis.Redis.from_url(self._url, socket_connect_timeout=0.5, socket_timeout=0.5)
            namespaced = f"ratelimit:{key}"
            current = int(client.incr(namespaced))
            if current == 1:
                client.expire(namespaced, window_seconds)
            client.close()
            return current <= limit
        except Exception:
            return True
