"""Conversation and message API schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.models.domain.conversation import ConversationStatus
from app.models.domain.message import MessageDirection, MessageType
from app.schemas.common import Pagination


class ConversationPublic(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    contact_id: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime


class MessagePublic(BaseModel):
    id: str
    conversation_id: str
    direction: MessageDirection
    message_type: MessageType
    text: str
    external_message_id: str | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    success: bool = True
    data: ConversationPublic


class ConversationListResponse(BaseModel):
    success: bool = True
    data: list[ConversationPublic]
    pagination: Pagination


class MessageListResponse(BaseModel):
    success: bool = True
    data: list[MessagePublic]
    pagination: Pagination
