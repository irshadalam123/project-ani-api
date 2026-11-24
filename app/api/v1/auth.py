"""Registration, login, and the current user."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_auth_service, get_current_user, rate_limit
from app.models.domain.user import User
from app.schemas.auth import (
    AuthData,
    AuthResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    UserPublic,
    WorkspacePublic,
)
from app.services.auth_service import AuthResult, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _auth_response(result: AuthResult) -> AuthResponse:
    return AuthResponse(
        data=AuthData(
            access_token=result.access_token,
            expires_in=result.expires_in,
            user=_user_public(result.user),
            workspace=WorkspacePublic.model_validate(result.workspace.model_dump()),
        )
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    summary="Create a user and a default workspace",
    dependencies=[Depends(rate_limit("auth"))],
)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    result = await service.register(body.email, body.password, body.full_name, body.workspace_name)
    return _auth_response(result)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Exchange email and password for an access token",
    dependencies=[Depends(rate_limit("auth"))],
)
async def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    result = await service.login(body.email, body.password)
    return _auth_response(result)


@router.get("/me", response_model=MeResponse, summary="Return the authenticated user")
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(data=_user_public(user))
