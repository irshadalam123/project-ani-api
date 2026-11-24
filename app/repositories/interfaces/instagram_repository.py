"""Connected Instagram account persistence port.

TODO(postgres): ``instagram_accounts`` with a unique
(workspace_id, instagram_user_id) constraint. Do not add a token column here;
tokens stay behind TokenManager.
"""

from abc import ABC, abstractmethod

from app.models.domain.instagram_account import InstagramAccount


class InstagramRepository(ABC):
    @abstractmethod
    async def add(self, account: InstagramAccount) -> InstagramAccount: ...

    @abstractmethod
    async def get_by_id(self, account_id: str) -> InstagramAccount | None: ...

    @abstractmethod
    async def get_by_instagram_user_id(self, instagram_user_id: str) -> InstagramAccount | None: ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[InstagramAccount]: ...

    @abstractmethod
    async def list_all(self) -> list[InstagramAccount]: ...

    @abstractmethod
    async def update(self, account: InstagramAccount) -> InstagramAccount: ...

    @abstractmethod
    async def delete(self, workspace_id: str, account_id: str) -> bool: ...
