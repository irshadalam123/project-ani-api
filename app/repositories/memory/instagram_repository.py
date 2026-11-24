"""In-memory Instagram account repository."""

from app.models.domain.instagram_account import InstagramAccount
from app.repositories.interfaces.instagram_repository import InstagramRepository
from app.repositories.memory._support import clone


class InMemoryInstagramRepository(InstagramRepository):
    def __init__(self) -> None:
        self._items: dict[str, InstagramAccount] = {}

    async def add(self, account: InstagramAccount) -> InstagramAccount:
        self._items[account.id] = clone(account)
        return clone(account)

    async def get_by_id(self, account_id: str) -> InstagramAccount | None:
        found = self._items.get(account_id)
        return clone(found) if found else None

    async def get_by_instagram_user_id(self, instagram_user_id: str) -> InstagramAccount | None:
        for item in self._items.values():
            if item.instagram_user_id == instagram_user_id:
                return clone(item)
        return None

    async def list_by_workspace(self, workspace_id: str) -> list[InstagramAccount]:
        items = [item for item in self._items.values() if item.workspace_id == workspace_id]
        items.sort(key=lambda item: item.created_at)
        return [clone(item) for item in items]

    async def list_all(self) -> list[InstagramAccount]:
        return [clone(item) for item in self._items.values()]

    async def update(self, account: InstagramAccount) -> InstagramAccount:
        self._items[account.id] = clone(account)
        return clone(account)

    async def delete(self, workspace_id: str, account_id: str) -> bool:
        current = self._items.get(account_id)
        if current is None or current.workspace_id != workspace_id:
            return False
        del self._items[account_id]
        return True
