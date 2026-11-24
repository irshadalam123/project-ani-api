"""Composition root.

Services receive repository interfaces. The in-memory implementations are
constructed here and nowhere else. A PostgreSQL swap replaces this function.
"""

from __future__ import annotations

from typing import Any

from dataclasses import dataclass

from app.automation.engine import AutomationEngine
from app.core.config import Settings
from app.core.rate_limit import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
from app.core.redis import FakeRedisService, LiveRedisService, RedisService
from app.integrations.instagram.client import InstagramClient, build_instagram_client
from app.integrations.instagram.oauth_state import InMemoryOAuthStateStore, OAuthStateStore
from app.integrations.instagram.token_manager import InMemoryTokenManager, TokenManager
from app.integrations.llm.client import LLMClient, build_llm_client
from app.repositories.interfaces.automation_repository import AutomationRepository
from app.repositories.interfaces.contact_repository import ContactRepository
from app.repositories.interfaces.conversation_repository import ConversationRepository
from app.repositories.interfaces.execution_repository import ExecutionRepository
from app.repositories.interfaces.instagram_repository import InstagramRepository
from app.repositories.interfaces.user_repository import UserRepository
from app.repositories.interfaces.webhook_repository import WebhookRepository
from app.repositories.interfaces.workspace_repository import WorkspaceRepository
from app.repositories.memory.automation_repository import InMemoryAutomationRepository
from app.repositories.memory.contact_repository import InMemoryContactRepository
from app.repositories.memory.conversation_repository import InMemoryConversationRepository
from app.repositories.memory.execution_repository import InMemoryExecutionRepository
from app.repositories.memory.instagram_repository import InMemoryInstagramRepository
from app.repositories.memory.user_repository import InMemoryUserRepository
from app.repositories.memory.webhook_repository import InMemoryWebhookRepository
from app.repositories.memory.workspace_repository import InMemoryWorkspaceRepository
from app.repositories.postgres import (
    PostgresAutomationRepository,
    PostgresContactRepository,
    PostgresConversationRepository,
    PostgresExecutionRepository,
    PostgresInstagramRepository,
    PostgresUserRepository,
    PostgresWebhookRepository,
    PostgresWorkspaceRepository,
    build_engine,
    build_session_factory,
)
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.automation_service import AutomationService
from app.services.comment_service import CommentService
from app.services.contact_service import ContactService
from app.services.conversation_service import ConversationService
from app.services.execution_service import ExecutionService
from app.services.instagram_service import InstagramService
from app.services.messaging_service import MessagingService
from app.services.webhook_service import WebhookService
from app.services.workspace_service import WorkspaceService
from app.workers.dispatcher import TaskDispatcher, build_dispatcher

_container: AppContainer | None = None


@dataclass
class AppContainer:
    settings: Settings
    users: UserRepository
    workspaces: WorkspaceRepository
    instagram_accounts: InstagramRepository
    automations: AutomationRepository
    contacts: ContactRepository
    conversations: ConversationRepository
    webhooks: WebhookRepository
    executions: ExecutionRepository
    tokens: TokenManager
    oauth_states: OAuthStateStore
    instagram: InstagramClient
    redis: RedisService
    rate_limiter: RateLimiter
    dispatcher: TaskDispatcher
    llm: LLMClient
    engine: AutomationEngine

    def auth_service(self) -> AuthService:
        return AuthService(self.users, self.workspaces, self.settings)

    def workspace_service(self) -> WorkspaceService:
        return WorkspaceService(self.workspaces)

    def instagram_service(self) -> InstagramService:
        return InstagramService(
            self.instagram_accounts,
            self.instagram,
            self.tokens,
            self.oauth_states,
            self.settings,
        )

    def automation_service(self) -> AutomationService:
        return AutomationService(self.automations, self.instagram_accounts)

    def contact_service(self) -> ContactService:
        return ContactService(self.contacts)

    def conversation_service(self) -> ConversationService:
        return ConversationService(self.conversations)

    def execution_service(self) -> ExecutionService:
        return ExecutionService(self.executions)

    def analytics_service(self) -> AnalyticsService:
        return AnalyticsService(self.webhooks, self.executions)

    def messaging_service(self) -> MessagingService:
        return MessagingService(self.instagram, self.tokens, self.conversation_service())

    def comment_service(self) -> CommentService:
        return CommentService(
            self.webhooks,
            self.instagram_accounts,
            self.automations,
            self.executions,
            self.contact_service(),
            self.messaging_service(),
            self.engine,
            self.settings,
        )

    def webhook_service(self) -> WebhookService:
        return WebhookService(self.webhooks, self.dispatcher, self.settings)


def build_container(settings: Settings) -> AppContainer:
    """Construct the application container.

    When ``settings.database_url`` is non-empty the container uses
    SQLAlchemy async (PostgreSQL) repositories; otherwise it falls back
    to the process-local in-memory implementations so that the project
    continues to work without a database during development.

    This is the *only* composition site. Routes, services, workers, and
    the automation engine are never changed.
    """
    redis_service: RedisService
    if settings.is_test:
        redis_service = FakeRedisService(healthy=True)
    else:
        redis_service = LiveRedisService(settings.redis_url)
    if settings.rate_limit_backend.lower() == "redis":
        rate_limiter: RateLimiter = RedisRateLimiter(settings.redis_url)
    else:
        rate_limiter = InMemoryRateLimiter()

    if settings.database_url.strip():
        # --- PostgreSQL path ---
        engine = build_engine(settings.database_url)
        session_factory = build_session_factory(engine)
        # Shared session for the lifetime of this container.
        # Swap to a per-request session factory when you add request middleware.
        session = session_factory()
        return AppContainer(
            settings=settings,
            users=PostgresUserRepository(session),
            workspaces=PostgresWorkspaceRepository(session),
            instagram_accounts=PostgresInstagramRepository(session),
            automations=PostgresAutomationRepository(session),
            contacts=PostgresContactRepository(session),
            conversations=PostgresConversationRepository(session),
            webhooks=PostgresWebhookRepository(session),
            executions=PostgresExecutionRepository(session),
            tokens=InMemoryTokenManager(),
            oauth_states=InMemoryOAuthStateStore(),
            instagram=build_instagram_client(settings),
            redis=redis_service,
            rate_limiter=rate_limiter,
            dispatcher=build_dispatcher(settings.task_execution_mode),
            llm=build_llm_client(settings),
            engine=AutomationEngine(),
        )

    # --- In-memory path (default) ---
    return AppContainer(
        settings=settings,
        users=InMemoryUserRepository(),
        workspaces=InMemoryWorkspaceRepository(),
        instagram_accounts=InMemoryInstagramRepository(),
        automations=InMemoryAutomationRepository(),
        contacts=InMemoryContactRepository(),
        conversations=InMemoryConversationRepository(),
        webhooks=InMemoryWebhookRepository(),
        executions=InMemoryExecutionRepository(),
        tokens=InMemoryTokenManager(),
        oauth_states=InMemoryOAuthStateStore(),
        instagram=build_instagram_client(settings),
        redis=redis_service,
        rate_limiter=rate_limiter,
        dispatcher=build_dispatcher(settings.task_execution_mode),
        llm=build_llm_client(settings),
        engine=AutomationEngine(),
    )


def set_container(container: AppContainer) -> None:
    global _container
    _container = container


def get_process_container() -> AppContainer:
    if _container is None:
        raise RuntimeError("Application container is not initialized")
    return _container
