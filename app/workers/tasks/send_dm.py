"""Send one private reply (Instagram DM to the commenter)."""

from celery import Task

from app.workers.celery_app import celery_app
from app.workers.handlers import handle_send_private_reply
from app.workers.tasks._runner import run_task


@celery_app.task(name="send_private_reply", bind=True, max_retries=5, acks_late=True)
def send_private_reply(self: Task, execution_id: str, action_index: int) -> None:
    run_task(
        self,
        "send_private_reply",
        {"execution_id": execution_id, "action_index": str(action_index)},
        lambda: handle_send_private_reply(execution_id, action_index),
    )
