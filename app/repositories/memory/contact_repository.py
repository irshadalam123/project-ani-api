"""In-memory contact repository."""

from app.models.domain.contact import Contact
from app.repositories.interfaces.contact_repository import ContactRepository
from app.repositories.memory._support import clone


class InMemoryContactRepository(ContactRepository):
    def __init__(self) -> None:
        self._items: dict[str, Contact] = {}

    async def add(self, contact: Contact) -> Contact:
        self._items[contact.id] = clone(contact)
        return clone(contact)

    async def get_by_id(self, contact_id: str) -> Contact | None:
        found = self._items.get(contact_id)
        return clone(found) if found else None

    async def get_by_instagram_user(
        self,
        workspace_id: str,
        instagram_account_id: str,
        instagram_user_id: str,
    ) -> Contact | None:
        for item in self._items.values():
            if (
                item.workspace_id == workspace_id
                and item.instagram_account_id == instagram_account_id
                and item.instagram_user_id == instagram_user_id
            ):
                return clone(item)
        return None

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Contact], int]:
        items = [item for item in self._items.values() if item.workspace_id == workspace_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return [clone(item) for item in items[start : start + page_size]], total

    async def update(self, contact: Contact) -> Contact:
        self._items[contact.id] = clone(contact)
        return clone(contact)
