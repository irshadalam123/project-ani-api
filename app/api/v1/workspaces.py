"""Workspace creation and listing."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_workspace_service
from app.models.domain.user import User
from app.models.domain.workspace import Workspace
from app.schemas.auth import WorkspaceCreateRequest, WorkspacePublic
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _public(workspace: Workspace) -> dict[str, object]:
    return WorkspacePublic.model_validate(workspace.model_dump()).model_dump(mode="json")


@router.get("", summary="List workspaces for the current user")
async def list_workspaces(
    user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> dict[str, object]:
    workspaces = await service.list_for_user(user.id)
    return {"success": True, "data": [_public(item) for item in workspaces]}


@router.post("", summary="Create a workspace", status_code=201)
async def create_workspace(
    body: WorkspaceCreateRequest,
    user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
) -> dict[str, object]:
    workspace = await service.create(user, body.name)
    return {"success": True, "data": _public(workspace)}
