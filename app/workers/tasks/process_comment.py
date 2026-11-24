"""Process one normalized comment."""

from celery import Task

from app.workers.celery_app import celery_app
from app.workers.handlers import handle_process_comment
from app.workers.tasks._runner import run_task


@celery_app.task(name="process_comment", bind=True, max_retries=5, acks_late=True)
def process_comment(self: Task, event_id: str) -> None:
    run_task(self, "process_comment", {"event_id": event_id}, lambda: handle_process_comment(event_id))
