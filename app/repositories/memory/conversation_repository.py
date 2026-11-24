"""In-memory conversation and message repository."""

from app.models.domain.conversation import Conversation
from app.models.domain.message import Message
from app.repositories.interfaces.conversation_repository import ConversationRepository
from app.repositories.memory._support import clone


class InMemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._messages: dict[str, Message] = {}

    async def add(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = clone(conversation)
        return clone(conversation)

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        found = self._conversations.get(conversation_id)
        return clone(found) if found else None

    async def get_for_contact(
        self,
        workspace_id: str,
        instagram_account_id: str,
        contact_id: str,
    ) -> Conversation | None:
        for item in self._conversations.values():
            if (
                item.workspace_id == workspace_id
                and item.instagram_account_id == instagram_account_id
                and item.contact_id == contact_id
            ):
                return clone(item)
        return None

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Conversation], int]:
        items = [item for item in self._conversations.values() if item.workspace_id == workspace_id]
        items.sort(key=lambda item: item.updated_at, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return [clone(item) for item in items[start : start + page_size]], total

    async def update(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = clone(conversation)
        return clone(conversation)

    async def add_message(self, message: Message) -> Message:
        self._messages[message.id] = clone(message)
        return clone(message)

    async def list_messages(
        self,
        conversation_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Message], int]:
        items = [item for item in self._messages.values() if item.conversation_id == conversation_id]
        items.sort(key=lambda item: item.created_at)
        total = len(items)
        start = (page - 1) * page_size
        return [clone(item) for item in items[start : start + page_size]], total
