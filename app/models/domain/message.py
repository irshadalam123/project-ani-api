"""A single inbound or outbound message inside a conversation."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class MessageDirection(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class MessageType(StrEnum):
    TEXT = "TEXT"
    BUTTON = "BUTTON"
    SYSTEM = "SYSTEM"


class Message(BaseModel):
    id: str
    conversation_id: str
    workspace_id: str
    direction: MessageDirection
    message_type: MessageType = MessageType.TEXT
    text: str
    external_message_id: str | None = None
    created_at: datetime
