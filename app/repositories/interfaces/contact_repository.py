"""Contact persistence port.

TODO(postgres): unique (workspace_id, instagram_account_id, instagram_user_id).
"""

from abc import ABC, abstractmethod

from app.models.domain.contact import Contact


class ContactRepository(ABC):
    @abstractmethod
    async def add(self, contact: Contact) -> Contact: ...

    @abstractmethod
    async def get_by_id(self, contact_id: str) -> Contact | None: ...

    @abstractmethod
    async def get_by_instagram_user(
        self,
        workspace_id: str,
        instagram_account_id: str,
        instagram_user_id: str,
    ) -> Contact | None: ...

    @abstractmethod
    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Contact], int]: ...

    @abstractmethod
    async def update(self, contact: Contact) -> Contact: ...
