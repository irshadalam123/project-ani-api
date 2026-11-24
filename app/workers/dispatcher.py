"""Queue webhook processing without doing it inside the HTTP request."""

from __future__ import annotations

from typing import Protocol

from fastapi import BackgroundTasks


class TaskDispatcher(Protocol):
    def enqueue_webhook(self, event_id: str, background_tasks: BackgroundTasks | None) -> None: ...


class InlineTaskDispatcher:
    """Run work after the response, in the API process.

    This is the default until PostgreSQL can share state with a separate
    Celery worker.
    """

    def enqueue_webhook(self, event_id: str, background_tasks: BackgroundTasks | None) -> None:
        from app.workers.handlers import handle_webhook_event

        if background_tasks is None:
            raise RuntimeError("Inline task dispatch requires a FastAPI BackgroundTasks instance")
        background_tasks.add_task(handle_webhook_event, event_id)


class CeleryTaskDispatcher:
    def enqueue_webhook(self, event_id: str, background_tasks: BackgroundTasks | None) -> None:
        _ = background_tasks
        from app.workers.tasks.process_webhook import process_webhook_event

        process_webhook_event.delay(event_id)


def build_dispatcher(task_execution_mode: str) -> TaskDispatcher:
    if task_execution_mode.lower() == "celery":
        return CeleryTaskDispatcher()
    return InlineTaskDispatcher()
