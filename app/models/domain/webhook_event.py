"""Normalized webhook event stored before background processing."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class WebhookEventStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"


class WebhookEventType(StrEnum):
    COMMENT = "COMMENT"
    LIVE_COMMENT = "LIVE_COMMENT"
    UNKNOWN = "UNKNOWN"


class WebhookEvent(BaseModel):
    id: str
    external_event_id: str
    event_type: WebhookEventType
    workspace_id: str | None = None
    instagram_account_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    status: WebhookEventStatus = WebhookEventStatus.RECEIVED
    received_at: datetime
    processed_at: datetime | None = None
    error: str | None = None
    attempt_count: int = 0
