"""PostgreSQL implementation of WebhookRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.webhook_event import WebhookEvent, WebhookEventStatus, WebhookEventType
from app.models.orm.webhook_event import WebhookEventModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.webhook_repository import WebhookRepository


def _to_domain(row: WebhookEventModel) -> WebhookEvent:
    return WebhookEvent(
        id=row.id,
        external_event_id=row.external_event_id,
        event_type=WebhookEventType(row.event_type),
        workspace_id=row.workspace_id,
        instagram_account_id=row.instagram_account_id,
        payload=dict(row.payload),
        status=WebhookEventStatus(row.status),
        received_at=row.received_at,
        processed_at=row.processed_at,
        error=row.error,
        attempt_count=row.attempt_count,
    )


class PostgresWebhookRepository(WebhookRepository):
    """SQLAlchemy async implementation of :class:`WebhookRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: WebhookEvent) -> WebhookEvent:
        row = WebhookEventModel(
            id=event.id,
            external_event_id=event.external_event_id,
            event_type=event.event_type.value,
            workspace_id=event.workspace_id,
            instagram_account_id=event.instagram_account_id,
            payload=event.payload,
            status=event.status.value,
            received_at=event.received_at,
            processed_at=event.processed_at,
            error=event.error,
            attempt_count=event.attempt_count,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("external_event_id") from exc
        await self._session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, event_id: str) -> WebhookEvent | None:
        row = await self._session.get(WebhookEventModel, event_id)
        return _to_domain(row) if row else None

    async def get_by_external_event_id(
        self, external_event_id: str
    ) -> WebhookEvent | None:
        result = await self._session.execute(
            select(WebhookEventModel).where(
                WebhookEventModel.external_event_id == external_event_id
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        row = await self._session.get(WebhookEventModel, event.id)
        if row is None:
            raise RecordNotFoundError(event.id)
        row.status = event.status.value
        row.processed_at = event.processed_at
        row.error = event.error
        row.attempt_count = event.attempt_count
        row.workspace_id = event.workspace_id
        row.instagram_account_id = event.instagram_account_id
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def list_by_workspace(self, workspace_id: str) -> list[WebhookEvent]:
        result = await self._session.execute(
            select(WebhookEventModel)
            .where(WebhookEventModel.workspace_id == workspace_id)
            .order_by(WebhookEventModel.received_at.desc())
        )
        return [_to_domain(r) for r in result.scalars().all()]
