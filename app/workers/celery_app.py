"""Celery application.

The worker uses the same settings as the API. Until PostgreSQL exists, the API
defaults to inline execution so jobs see the in-memory repositories. Point
TASK_EXECUTION_MODE at celery only when the worker can read the same store.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "instagram_dm_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    imports=[
        "app.workers.tasks.process_webhook",
        "app.workers.tasks.process_comment",
        "app.workers.tasks.send_dm",
        "app.workers.tasks.send_public_reply",
    ],
)
