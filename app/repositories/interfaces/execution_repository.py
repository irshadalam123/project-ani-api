"""Automation execution persistence port.

TODO(postgres): unique (automation_id, comment_id) so a comment cannot be
answered twice by the same automation.
"""

from abc import ABC, abstractmethod

from app.models.domain.execution import ActionResult, Execution


class ExecutionRepository(ABC):
    @abstractmethod
    async def create_if_absent(self, execution: Execution) -> tuple[Execution, bool]: ...

    @abstractmethod
    async def get_by_id(self, execution_id: str) -> Execution | None: ...

    @abstractmethod
    async def get_by_automation_and_comment(
        self,
        automation_id: str,
        comment_id: str,
    ) -> Execution | None: ...

    @abstractmethod
    async def save_action_result(self, execution_id: str, result: ActionResult) -> Execution: ...

    @abstractmethod
    async def update(self, execution: Execution) -> Execution: ...

    @abstractmethod
    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
        automation_id: str | None = None,
    ) -> tuple[list[Execution], int]: ...

    @abstractmethod
    async def list_for_event(self, webhook_event_id: str) -> list[Execution]: ...
