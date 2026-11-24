"""Queue entry for a stored webhook event."""

from celery import Task

from app.workers.celery_app import celery_app
from app.workers.handlers import handle_webhook_event
from app.workers.tasks._runner import run_task


@celery_app.task(name="process_webhook_event", bind=True, max_retries=5, acks_late=True)
def process_webhook_event(self: Task, event_id: str) -> None:
    run_task(
        self,
        "process_webhook_event",
        {"event_id": event_id},
        lambda: handle_webhook_event(event_id),
    )
