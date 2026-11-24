"""Automation persistence port.

TODO(postgres): store trigger and actions as JSON columns, indexed by
(workspace_id, instagram_account_id, status).
"""

from abc import ABC, abstractmethod

from app.models.domain.automation import Automation


class AutomationRepository(ABC):
    @abstractmethod
    async def add(self, automation: Automation) -> Automation: ...

    @abstractmethod
    async def get_by_id(self, automation_id: str) -> Automation | None: ...

    @abstractmethod
    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Automation], int]: ...

    @abstractmethod
    async def list_active_for_account(
        self,
        workspace_id: str,
        instagram_account_id: str,
    ) -> list[Automation]: ...

    @abstractmethod
    async def update(self, automation: Automation) -> Automation: ...

    @abstractmethod
    async def delete(self, workspace_id: str, automation_id: str) -> bool: ...
