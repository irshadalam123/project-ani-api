"""Webhook response schemas."""

from pydantic import BaseModel, Field


class WebhookIngestData(BaseModel):
    accepted: bool
    event_ids: list[str] = Field(default_factory=list)
    duplicate_event_ids: list[str] = Field(default_factory=list)


class WebhookIngestResponse(BaseModel):
    success: bool = True
    data: WebhookIngestData
