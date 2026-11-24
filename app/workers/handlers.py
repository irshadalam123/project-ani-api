"""Async task bodies shared by inline dispatch and Celery."""

from app.core.container import get_process_container
from app.core.logging import get_logger

logger = get_logger(__name__)


async def handle_webhook_event(event_id: str) -> None:
    container = get_process_container()
    await container.comment_service().process_webhook_event(event_id)


async def handle_process_comment(event_id: str) -> None:
    container = get_process_container()
    await container.comment_service().process_comment(event_id)


async def handle_send_public_reply(execution_id: str, action_index: int) -> None:
    container = get_process_container()
    await container.comment_service().deliver_action(execution_id, action_index)


async def handle_send_private_reply(execution_id: str, action_index: int) -> None:
    container = get_process_container()
    await container.comment_service().deliver_action(execution_id, action_index)
