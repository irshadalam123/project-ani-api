"""Send one public comment reply."""

from celery import Task

from app.workers.celery_app import celery_app
from app.workers.handlers import handle_send_public_reply
from app.workers.tasks._runner import run_task


@celery_app.task(name="send_public_reply", bind=True, max_retries=5, acks_late=True)
def send_public_reply(self: Task, execution_id: str, action_index: int) -> None:
    run_task(
        self,
        "send_public_reply",
        {"execution_id": execution_id, "action_index": str(action_index)},
        lambda: handle_send_public_reply(execution_id, action_index),
    )
