"""Read automation executions for a workspace."""

from __future__ import annotations

from app.core.exceptions import NotFoundException
from app.models.domain.execution import Execution
from app.repositories.interfaces.execution_repository import ExecutionRepository


class ExecutionService:
    def __init__(self, executions: ExecutionRepository) -> None:
        self._executions = executions

    async def list(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
        automation_id: str | None = None,
    ) -> tuple[list[Execution], int]:
        return await self._executions.list_by_workspace(
            workspace_id,
            page=page,
            page_size=page_size,
            automation_id=automation_id,
        )

    async def get(self, workspace_id: str, execution_id: str) -> Execution:
        execution = await self._executions.get_by_id(execution_id)
        if execution is None or execution.workspace_id != workspace_id:
            raise NotFoundException("Execution not found", code="EXECUTION_NOT_FOUND")
        return execution
