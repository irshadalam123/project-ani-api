"""PostgreSQL repository implementations backed by SQLAlchemy async.

Each class in this package implements the corresponding interface from
``app.repositories.interfaces``. They are wired into the DI container by
``app.core.container.build_container`` when ``DATABASE_URL`` is configured.
"""

from app.repositories.postgres._session import build_engine, build_session_factory
from app.repositories.postgres.automation_repository import PostgresAutomationRepository
from app.repositories.postgres.contact_repository import PostgresContactRepository
from app.repositories.postgres.conversation_repository import PostgresConversationRepository
from app.repositories.postgres.execution_repository import PostgresExecutionRepository
from app.repositories.postgres.instagram_repository import PostgresInstagramRepository
from app.repositories.postgres.user_repository import PostgresUserRepository
from app.repositories.postgres.webhook_repository import PostgresWebhookRepository
from app.repositories.postgres.workspace_repository import PostgresWorkspaceRepository

__all__ = [
    "build_engine",
    "build_session_factory",
    "PostgresAutomationRepository",
    "PostgresContactRepository",
    "PostgresConversationRepository",
    "PostgresExecutionRepository",
    "PostgresInstagramRepository",
    "PostgresUserRepository",
    "PostgresWebhookRepository",
    "PostgresWorkspaceRepository",
]
