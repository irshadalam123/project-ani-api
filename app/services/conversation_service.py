"""Conversation reads and outbound message recording."""

from __future__ import annotations

from app.core.exceptions import NotFoundException
from app.models.domain.conversation import Conversation, ConversationStatus
from app.models.domain.message import Message, MessageDirection, MessageType
from app.repositories.interfaces.conversation_repository import ConversationRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id


class ConversationService:
    def __init__(self, conversations: ConversationRepository) -> None:
        self._conversations = conversations

    async def list_conversations(
        self, workspace_id: str, *, page: int, page_size: int
    ) -> tuple[list[Conversation], int]:
        return await self._conversations.list_by_workspace(workspace_id, page=page, page_size=page_size)

    async def get(self, workspace_id: str, conversation_id: str) -> Conversation:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None or conversation.workspace_id != workspace_id:
            raise NotFoundException("Conversation not found", code="CONVERSATION_NOT_FOUND")
        return conversation

    async def list_messages(
        self,
        workspace_id: str,
        conversation_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Message], int]:
        await self.get(workspace_id, conversation_id)
        return await self._conversations.list_messages(conversation_id, page=page, page_size=page_size)

    async def record_outbound(
        self,
        *,
        workspace_id: str,
        instagram_account_id: str,
        contact_id: str,
        text: str,
        external_message_id: str | None,
    ) -> Message:
        conversation = await self._conversations.get_for_contact(
            workspace_id,
            instagram_account_id,
            contact_id,
        )
        now = utcnow()
        if conversation is None:
            conversation = Conversation(
                id=new_id(),
                workspace_id=workspace_id,
                instagram_account_id=instagram_account_id,
                contact_id=contact_id,
                status=ConversationStatus.OPEN,
                created_at=now,
                updated_at=now,
            )
            await self._conversations.add(conversation)
        else:
            conversation.updated_at = now
            conversation.status = ConversationStatus.OPEN
            await self._conversations.update(conversation)
        message = Message(
            id=new_id(),
            conversation_id=conversation.id,
            workspace_id=workspace_id,
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.TEXT,
            text=text,
            external_message_id=external_message_id,
            created_at=now,
        )
        return await self._conversations.add_message(message)
