"""Instagram OAuth connect, callback, and account management."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    get_instagram_service,
    get_workspace_context,
    rate_limit,
)
from app.models.domain.instagram_account import InstagramAccount
from app.schemas.instagram import (
    ConnectData,
    ConnectResponse,
    InstagramAccountListResponse,
    InstagramAccountPublic,
    InstagramAccountResponse,
)
from app.services.instagram_service import InstagramService
from app.services.workspace_service import WorkspaceContext

router = APIRouter(prefix="/instagram", tags=["instagram"])


def _public(account: InstagramAccount) -> InstagramAccountPublic:
    return InstagramAccountPublic.model_validate(account.model_dump())


@router.get(
    "/connect",
    response_model=ConnectResponse,
    summary="Build the Meta OAuth authorization URL",
    dependencies=[Depends(rate_limit("instagram"))],
)
async def connect(
    context: WorkspaceContext = Depends(get_workspace_context),
    service: InstagramService = Depends(get_instagram_service),
) -> ConnectResponse:
    link = await service.connect_link(context.user.id, context.workspace.id)
    return ConnectResponse(data=ConnectData(authorization_url=link.authorization_url, state=link.state))


@router.get(
    "/callback",
    response_model=InstagramAccountResponse,
    summary="Exchange the OAuth code and store the professional account",
)
async def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: InstagramService = Depends(get_instagram_service),
) -> InstagramAccountResponse:
    """Meta redirects the browser here. The state value ties the code to a workspace.

    The access token is stored and is not part of this response.
    """
    account = await service.handle_callback(code, state, error)
    return InstagramAccountResponse(data=_public(account))


@router.get(
    "/accounts",
    response_model=InstagramAccountListResponse,
    summary="List Instagram accounts connected to the workspace",
)
async def list_accounts(
    context: WorkspaceContext = Depends(get_workspace_context),
    service: InstagramService = Depends(get_instagram_service),
) -> InstagramAccountListResponse:
    accounts = await service.list_accounts(context.workspace.id)
    return InstagramAccountListResponse(data=[_public(item) for item in accounts])


@router.delete(
    "/accounts/{account_id}",
    summary="Disconnect an Instagram account",
    dependencies=[Depends(rate_limit("instagram"))],
)
async def disconnect(
    account_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: InstagramService = Depends(get_instagram_service),
) -> dict[str, object]:
    await service.disconnect(context.workspace.id, account_id)
    return {"success": True, "data": {"deleted": True}}
