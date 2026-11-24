"""Retry classification, backoff, and dead-letter recording.

Permanent errors are not retried. Transient errors use exponential backoff.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

import redis

from app.core.exceptions import AppException

T = TypeVar("T")
from app.core.logging import get_logger

logger = get_logger(__name__)


def is_transient(exc: BaseException) -> bool:
    if isinstance(exc, AppException):
        return exc.transient
    return False


async def run_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int,
    base_seconds: float,
) -> T:
    """Run an async operation, retrying only transient application errors."""
    attempt = 1
    while True:
        try:
            return await operation()
        except AppException as exc:
            if not exc.transient or attempt >= max_attempts:
                raise
            await asyncio.sleep(backoff_seconds(attempt, base=base_seconds))
            attempt += 1


def backoff_seconds(attempt: int, *, base: float, cap: float = 60.0) -> float:
    """``attempt`` is 1-based."""
    if attempt < 1:
        attempt = 1
    return min(cap, base * (2 ** (attempt - 1)))


def record_dead_letter(
    task_name: str,
    payload: dict[str, str],
    error: str,
    *,
    redis_url: str,
) -> None:
    """Record a terminal failure.

    Redis is used only as a short overflow list. The webhook or execution row
    remains the business record. If Redis is down, the structured log is enough.
    """
    logger.error("dead_letter", task=task_name, error=error, **payload)
    body = json.dumps({"task": task_name, "payload": payload, "error": error[:500]})
    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        client.lpush("dead_letter", body)
        client.ltrim("dead_letter", 0, 999)
        client.close()
    except Exception:
        logger.warning("dead_letter_redis_unavailable", task=task_name)
