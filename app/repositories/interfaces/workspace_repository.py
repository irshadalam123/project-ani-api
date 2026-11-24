"""Workspace and membership persistence port.

TODO(postgres): ``workspaces`` plus ``workspace_members`` with a unique
(workspace_id, user_id) constraint.
"""

from abc import ABC, abstractmethod

from app.models.domain.user import WorkspaceMember
from app.models.domain.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def add(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    async def get_by_id(self, workspace_id: str) -> Workspace | None: ...

    @abstractmethod
    async def update(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember: ...

    @abstractmethod
    async def get_membership(self, workspace_id: str, user_id: str) -> WorkspaceMember | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: str) -> list[Workspace]: ...
