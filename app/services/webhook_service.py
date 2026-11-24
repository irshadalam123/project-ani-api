"""Accept Instagram webhooks, store them once, and queue processing."""

from dataclasses import dataclass

from fastapi import BackgroundTasks

from app.core.config import Settings
from app.core.exceptions import ValidationException
from app.core.logging import get_logger
from app.integrations.instagram.webhooks import parse_webhook_body, verify_signature, verify_subscription
from app.models.domain.webhook_event import WebhookEvent, WebhookEventStatus, WebhookEventType
from app.repositories.exceptions import DuplicateRecordError
from app.repositories.interfaces.webhook_repository import WebhookRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id
from app.workers.dispatcher import TaskDispatcher

logger = get_logger(__name__)


@dataclass(slots=True)
class IngestResult:
    accepted: bool
    event_ids: list[str]
    duplicate_event_ids: list[str]


class WebhookService:
    def __init__(
        self,
        webhooks: WebhookRepository,
        dispatcher: TaskDispatcher,
        settings: Settings,
    ) -> None:
        self._webhooks = webhooks
        self._dispatcher = dispatcher
        self._settings = settings

    def verify(self, mode: str | None, token: str | None, challenge: str | None) -> str:
        return verify_subscription(
            mode=mode,
            verify_token=token,
            challenge=challenge,
            expected_token=self._settings.meta_webhook_verify_token,
        )

    async def ingest(
        self,
        body: bytes,
        signature: str | None,
        background_tasks: BackgroundTasks | None,
    ) -> IngestResult:
        if len(body) > self._settings.request_max_body_bytes:
            raise ValidationException("Webhook body is too large", code="PAYLOAD_TOO_LARGE")
        verify_signature(body, signature, self._settings.meta_app_secret)
        comments = parse_webhook_body(
            body,
            allow_simplified=self._settings.mock_external_services or not self._settings.is_production,
        )
        accepted: list[str] = []
        duplicates: list[str] = []
        for comment in comments:
            existing = await self._webhooks.get_by_external_event_id(comment.external_event_id)
            if existing is not None:
                duplicates.append(existing.id)
                continue
            event_type = (
                WebhookEventType.LIVE_COMMENT
                if comment.event_type == "LIVE_COMMENT"
                else WebhookEventType.COMMENT
            )
            event = WebhookEvent(
                id=new_id(),
                external_event_id=comment.external_event_id,
                event_type=event_type,
                payload={"comment": comment.model_dump()},
                status=WebhookEventStatus.RECEIVED,
                received_at=utcnow(),
                attempt_count=0,
            )
            try:
                await self._webhooks.add(event)
            except DuplicateRecordError:
                raced = await self._webhooks.get_by_external_event_id(comment.external_event_id)
                if raced is not None:
                    duplicates.append(raced.id)
                continue
            self._dispatcher.enqueue_webhook(event.id, background_tasks)
            accepted.append(event.id)
            logger.info("webhook_queued", event_id=event.id, external_event_id=comment.external_event_id)
        return IngestResult(accepted=True, event_ids=accepted, duplicate_event_ids=duplicates)
