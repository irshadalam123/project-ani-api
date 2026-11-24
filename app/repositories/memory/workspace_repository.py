"""In-memory workspace repository."""

from app.models.domain.user import WorkspaceMember
from app.models.domain.workspace import Workspace
from app.repositories.interfaces.workspace_repository import WorkspaceRepository
from app.repositories.memory._support import clone


class InMemoryWorkspaceRepository(WorkspaceRepository):
    def __init__(self) -> None:
        self._workspaces: dict[str, Workspace] = {}
        self._members: dict[str, WorkspaceMember] = {}

    async def add(self, workspace: Workspace) -> Workspace:
        self._workspaces[workspace.id] = clone(workspace)
        return clone(workspace)

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        found = self._workspaces.get(workspace_id)
        return clone(found) if found else None

    async def update(self, workspace: Workspace) -> Workspace:
        self._workspaces[workspace.id] = clone(workspace)
        return clone(workspace)

    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        self._members[member.id] = clone(member)
        return clone(member)

    async def get_membership(self, workspace_id: str, user_id: str) -> WorkspaceMember | None:
        for member in self._members.values():
            if member.workspace_id == workspace_id and member.user_id == user_id:
                return clone(member)
        return None

    async def list_for_user(self, user_id: str) -> list[Workspace]:
        workspace_ids = [
            member.workspace_id for member in self._members.values() if member.user_id == user_id
        ]
        workspaces = [self._workspaces[item_id] for item_id in workspace_ids if item_id in self._workspaces]
        workspaces.sort(key=lambda item: item.created_at)
        return [clone(item) for item in workspaces]
