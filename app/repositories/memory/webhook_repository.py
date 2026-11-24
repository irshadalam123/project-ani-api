"""In-memory webhook event repository with external-id idempotency."""

from app.models.domain.webhook_event import WebhookEvent
from app.repositories.exceptions import DuplicateRecordError
from app.repositories.interfaces.webhook_repository import WebhookRepository
from app.repositories.memory._support import clone


class InMemoryWebhookRepository(WebhookRepository):
    def __init__(self) -> None:
        self._items: dict[str, WebhookEvent] = {}
        self._by_external: dict[str, str] = {}

    async def add(self, event: WebhookEvent) -> WebhookEvent:
        if event.external_event_id in self._by_external:
            raise DuplicateRecordError(event.external_event_id)
        self._items[event.id] = clone(event)
        self._by_external[event.external_event_id] = event.id
        return clone(event)

    async def get_by_id(self, event_id: str) -> WebhookEvent | None:
        found = self._items.get(event_id)
        return clone(found) if found else None

    async def get_by_external_event_id(self, external_event_id: str) -> WebhookEvent | None:
        event_id = self._by_external.get(external_event_id)
        if event_id is None:
            return None
        return await self.get_by_id(event_id)

    async def update(self, event: WebhookEvent) -> WebhookEvent:
        self._items[event.id] = clone(event)
        self._by_external[event.external_event_id] = event.id
        return clone(event)

    async def list_by_workspace(self, workspace_id: str) -> list[WebhookEvent]:
        items = [item for item in self._items.values() if item.workspace_id == workspace_id]
        items.sort(key=lambda item: item.received_at)
        return [clone(item) for item in items]
