"""In-memory execution repository."""

from app.models.domain.execution import (
    ActionResult,
    ActionResultStatus,
    Execution,
    ExecutionStatus,
)
from app.repositories.interfaces.execution_repository import ExecutionRepository
from app.repositories.memory._support import clone
from app.utils.datetime import utcnow


class InMemoryExecutionRepository(ExecutionRepository):
    def __init__(self) -> None:
        self._items: dict[str, Execution] = {}

    def _key(self, automation_id: str, comment_id: str) -> str:
        return f"{automation_id}:{comment_id}"

    def _index(self) -> dict[str, str]:
        return {self._key(item.automation_id, item.comment_id): item.id for item in self._items.values()}

    async def create_if_absent(self, execution: Execution) -> tuple[Execution, bool]:
        existing_id = self._index().get(self._key(execution.automation_id, execution.comment_id))
        if existing_id is not None:
            return clone(self._items[existing_id]), False
        self._items[execution.id] = clone(execution)
        return clone(execution), True

    async def get_by_id(self, execution_id: str) -> Execution | None:
        found = self._items.get(execution_id)
        return clone(found) if found else None

    async def get_by_automation_and_comment(
        self,
        automation_id: str,
        comment_id: str,
    ) -> Execution | None:
        existing_id = self._index().get(self._key(automation_id, comment_id))
        if existing_id is None:
            return None
        return clone(self._items[existing_id])

    async def save_action_result(self, execution_id: str, result: ActionResult) -> Execution:
        current = self._items[execution_id]
        updated_results = []
        replaced = False
        for item in current.action_results:
            if item.action_index == result.action_index:
                updated_results.append(result)
                replaced = True
            else:
                updated_results.append(item)
        if not replaced:
            updated_results.append(result)
        updated_results.sort(key=lambda item: item.action_index)
        current.action_results = updated_results
        if any(item.status == ActionResultStatus.PENDING for item in updated_results):
            current.status = ExecutionStatus.RUNNING
        elif any(item.status == ActionResultStatus.FAILED for item in updated_results):
            current.status = ExecutionStatus.FAILED
            current.completed_at = utcnow()
        else:
            current.status = ExecutionStatus.SUCCEEDED
            current.completed_at = utcnow()
        current.updated_at = utcnow()
        self._items[execution_id] = clone(current)
        return clone(current)

    async def update(self, execution: Execution) -> Execution:
        self._items[execution.id] = clone(execution)
        return clone(execution)

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
        automation_id: str | None = None,
    ) -> tuple[list[Execution], int]:
        items = [item for item in self._items.values() if item.workspace_id == workspace_id]
        if automation_id is not None:
            items = [item for item in items if item.automation_id == automation_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return [clone(item) for item in items[start : start + page_size]], total

    async def list_for_event(self, webhook_event_id: str) -> list[Execution]:
        items = [item for item in self._items.values() if item.webhook_event_id == webhook_event_id]
        return [clone(item) for item in items]
