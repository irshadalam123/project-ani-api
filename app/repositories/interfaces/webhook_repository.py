"""Webhook event persistence port.

TODO(postgres): unique index on external_event_id for idempotency.
"""

from abc import ABC, abstractmethod

from app.models.domain.webhook_event import WebhookEvent


class WebhookRepository(ABC):
    @abstractmethod
    async def add(self, event: WebhookEvent) -> WebhookEvent: ...

    @abstractmethod
    async def get_by_id(self, event_id: str) -> WebhookEvent | None: ...

    @abstractmethod
    async def get_by_external_event_id(self, external_event_id: str) -> WebhookEvent | None: ...

    @abstractmethod
    async def update(self, event: WebhookEvent) -> WebhookEvent: ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[WebhookEvent]: ...
