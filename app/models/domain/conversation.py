"""Conversation between a connected account and a contact."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ConversationStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Conversation(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    contact_id: str
    status: ConversationStatus = ConversationStatus.OPEN
    created_at: datetime
    updated_at: datetime
