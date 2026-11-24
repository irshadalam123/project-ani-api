"""Conversation and message persistence port.

TODO(postgres): ``conversations`` and ``messages`` tables. Messages reference
conversations. Both carry workspace_id for tenant filters.
"""

from abc import ABC, abstractmethod

from app.models.domain.conversation import Conversation
from app.models.domain.message import Message


class ConversationRepository(ABC):
    @abstractmethod
    async def add(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Conversation | None: ...

    @abstractmethod
    async def get_for_contact(
        self,
        workspace_id: str,
        instagram_account_id: str,
        contact_id: str,
    ) -> Conversation | None: ...

    @abstractmethod
    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Conversation], int]: ...

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def add_message(self, message: Message) -> Message: ...

    @abstractmethod
    async def list_messages(
        self,
        conversation_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Message], int]: ...
