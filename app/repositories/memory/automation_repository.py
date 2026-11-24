"""In-memory automation repository."""

from app.models.domain.automation import Automation, AutomationStatus
from app.repositories.interfaces.automation_repository import AutomationRepository
from app.repositories.memory._support import clone


class InMemoryAutomationRepository(AutomationRepository):
    def __init__(self) -> None:
        self._items: dict[str, Automation] = {}

    async def add(self, automation: Automation) -> Automation:
        self._items[automation.id] = clone(automation)
        return clone(automation)

    async def get_by_id(self, automation_id: str) -> Automation | None:
        found = self._items.get(automation_id)
        return clone(found) if found else None

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Automation], int]:
        items = [item for item in self._items.values() if item.workspace_id == workspace_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]
        return [clone(item) for item in page_items], total

    async def list_active_for_account(
        self,
        workspace_id: str,
        instagram_account_id: str,
    ) -> list[Automation]:
        items = [
            item
            for item in self._items.values()
            if item.workspace_id == workspace_id
            and item.instagram_account_id == instagram_account_id
            and item.status == AutomationStatus.ACTIVE
        ]
        items.sort(key=lambda item: item.created_at)
        return [clone(item) for item in items]

    async def update(self, automation: Automation) -> Automation:
        self._items[automation.id] = clone(automation)
        return clone(automation)

    async def delete(self, workspace_id: str, automation_id: str) -> bool:
        current = self._items.get(automation_id)
        if current is None or current.workspace_id != workspace_id:
            return False
        del self._items[automation_id]
        return True
