"""Workspace membership and authorization."""

from dataclasses import dataclass

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.models.domain.user import User, WorkspaceMember, WorkspaceRole
from app.models.domain.workspace import Workspace
from app.repositories.interfaces.workspace_repository import WorkspaceRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id


@dataclass(slots=True)
class WorkspaceContext:
    user: User
    workspace: Workspace
    role: str


class WorkspaceService:
    def __init__(self, workspaces: WorkspaceRepository) -> None:
        self._workspaces = workspaces

    async def create(self, user: User, name: str) -> Workspace:
        now = utcnow()
        workspace = Workspace(
            id=new_id(),
            name=name.strip(),
            owner_id=user.id,
            created_at=now,
            updated_at=now,
        )
        await self._workspaces.add(workspace)
        await self._workspaces.add_member(
            WorkspaceMember(
                id=new_id(),
                workspace_id=workspace.id,
                user_id=user.id,
                role=WorkspaceRole.OWNER,
                created_at=now,
            )
        )
        return workspace

    async def list_for_user(self, user_id: str) -> list[Workspace]:
        return await self._workspaces.list_for_user(user_id)

    async def authorize(self, user: User, workspace_id: str | None) -> WorkspaceContext:
        memberships = await self._workspaces.list_for_user(user.id)
        workspace: Workspace | None
        if workspace_id is None:
            if len(memberships) == 1:
                workspace = memberships[0]
            elif not memberships:
                raise NotFoundException("No workspace is available for this user", code="WORKSPACE_NOT_FOUND")
            else:
                raise ValidationException(
                    "X-Workspace-Id is required when you belong to more than one workspace",
                    code="WORKSPACE_REQUIRED",
                )
        else:
            workspace = await self._workspaces.get_by_id(workspace_id)
            if workspace is None or all(item.id != workspace_id for item in memberships):
                raise AuthorizationException(
                    "You do not have access to this workspace",
                    code="WORKSPACE_FORBIDDEN",
                )
        if workspace is None:
            raise NotFoundException("No workspace is available for this user", code="WORKSPACE_NOT_FOUND")
        member = await self._workspaces.get_membership(workspace.id, user.id)
        if member is None:
            raise AuthorizationException(
                "You do not have access to this workspace",
                code="WORKSPACE_FORBIDDEN",
            )
        return WorkspaceContext(user=user, workspace=workspace, role=member.role)
