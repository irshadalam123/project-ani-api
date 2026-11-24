"""SQLAlchemy ORM table definitions.

All mapped classes live here. Only repositories (``app/repositories``)
may import from this package – never services or routes.
"""

from app.models.orm.base import Base, mapper_registry
from app.models.orm.automation import AutomationModel
from app.models.orm.contact import ContactModel
from app.models.orm.conversation import ConversationModel
from app.models.orm.execution import ExecutionModel
from app.models.orm.instagram_account import InstagramAccountModel
from app.models.orm.message import MessageModel
from app.models.orm.user import UserModel, WorkspaceMemberModel
from app.models.orm.webhook_event import WebhookEventModel
from app.models.orm.workspace import WorkspaceModel

__all__ = [
    "Base",
    "mapper_registry",
    "AutomationModel",
    "ContactModel",
    "ConversationModel",
    "ExecutionModel",
    "InstagramAccountModel",
    "MessageModel",
    "UserModel",
    "WorkspaceMemberModel",
    "WebhookEventModel",
    "WorkspaceModel",
]
