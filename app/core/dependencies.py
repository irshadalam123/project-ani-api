"""FastAPI dependencies.

Routes resolve services from the process container. They do not construct
repositories.
"""

from collections.abc import Callable

from fastapi import Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.container import AppContainer
from app.core.exceptions import AuthenticationException, RateLimitException
from app.core.security import decode_access_token
from app.models.domain.user import User
from app.schemas.common import PaginationParams
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.automation_service import AutomationService
from app.services.contact_service import ContactService
from app.services.execution_service import ExecutionService
from app.services.conversation_service import ConversationService
from app.services.instagram_service import InstagramService
from app.services.webhook_service import WebhookService
from app.services.workspace_service import WorkspaceContext, WorkspaceService

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_auth_service(container: AppContainer = Depends(get_container)) -> AuthService:
    return container.auth_service()


def get_workspace_service(container: AppContainer = Depends(get_container)) -> WorkspaceService:
    return container.workspace_service()


def get_instagram_service(container: AppContainer = Depends(get_container)) -> InstagramService:
    return container.instagram_service()


def get_automation_service(container: AppContainer = Depends(get_container)) -> AutomationService:
    return container.automation_service()


def get_contact_service(container: AppContainer = Depends(get_container)) -> ContactService:
    return container.contact_service()


def get_conversation_service(container: AppContainer = Depends(get_container)) -> ConversationService:
    return container.conversation_service()


def get_execution_service(container: AppContainer = Depends(get_container)) -> ExecutionService:
    return container.execution_service()


def get_analytics_service(container: AppContainer = Depends(get_container)) -> AnalyticsService:
    return container.analytics_service()


def get_webhook_service(container: AppContainer = Depends(get_container)) -> WebhookService:
    return container.webhook_service()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationException()
    user_id = decode_access_token(credentials.credentials, request.app.state.settings)
    user = await auth_service.get_user(user_id)
    import structlog

    structlog.contextvars.bind_contextvars(user_id=user.id)
    return user


async def get_workspace_context(
    workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceContext:
    context = await workspace_service.authorize(user, workspace_id)
    import structlog

    structlog.contextvars.bind_contextvars(workspace_id=context.workspace.id, user_id=user.id)
    return context


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def rate_limit(bucket: str) -> Callable:
    async def _limit(request: Request, container: AppContainer = Depends(get_container)) -> None:
        settings = container.settings
        if not settings.rate_limit_enabled:
            return
        limits = {
            "auth": settings.rate_limit_auth_per_minute,
            "automation_create": settings.rate_limit_automation_create_per_minute,
            "instagram": settings.rate_limit_instagram_per_minute,
            "webhook": settings.rate_limit_webhook_per_minute,
        }
        limit = limits.get(bucket, 60)
        host = request.client.host if request.client else "unknown"
        allowed = container.rate_limiter.allow(f"{bucket}:{host}", limit, 60)
        if not allowed:
            raise RateLimitException()

    return _limit
