"""Run async handlers from synchronous Celery tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from celery import Task

from app.core.config import get_settings
from app.core.container import build_container, get_process_container, set_container
from app.core.logging import configure_logging
from app.workers.utils import backoff_seconds, is_transient, record_dead_letter


def ensure_worker_container() -> None:
    try:
        get_process_container()
    except RuntimeError:
        settings = get_settings()
        configure_logging(settings)
        set_container(build_container(settings))


def run_task(
    task: Task,
    task_name: str,
    payload: dict[str, str],
    operation: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    ensure_worker_container()
    settings = get_settings()
    try:
        asyncio.run(operation())
    except Exception as exc:
        if is_transient(exc) and task.request.retries < task.max_retries:
            raise task.retry(
                exc=exc,
                countdown=backoff_seconds(task.request.retries + 1, base=settings.retry_base_seconds),
            ) from exc
        record_dead_letter(task_name, payload, str(exc), redis_url=settings.redis_url)
        if is_transient(exc):
            return
        raise
