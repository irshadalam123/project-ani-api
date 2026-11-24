"""Local registration and login.

Users live in the user repository. Replacing that repository with PostgreSQL
does not change this service.
"""

from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import AuthenticationException, ConflictException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain.user import User, WorkspaceMember, WorkspaceRole
from app.models.domain.workspace import Workspace
from app.repositories.exceptions import DuplicateRecordError
from app.repositories.interfaces.user_repository import UserRepository
from app.repositories.interfaces.workspace_repository import WorkspaceRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id


@dataclass(slots=True)
class AuthResult:
    access_token: str
    expires_in: int
    user: User
    workspace: Workspace


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        workspaces: WorkspaceRepository,
        settings: Settings,
    ) -> None:
        self._users = users
        self._workspaces = workspaces
        self._settings = settings

    async def register(self, email: str, password: str, full_name: str, workspace_name: str | None) -> AuthResult:
        normalized = email.strip().lower()
        existing = await self._users.get_by_email(normalized)
        if existing is not None:
            raise ConflictException("An account with this email already exists", code="EMAIL_ALREADY_REGISTERED")
        now = utcnow()
        user = User(
            id=new_id(),
            email=normalized,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        try:
            await self._users.add(user)
        except DuplicateRecordError as exc:
            raise ConflictException(
                "An account with this email already exists",
                code="EMAIL_ALREADY_REGISTERED",
            ) from exc
        workspace = await self._create_workspace(user, workspace_name or f"{user.full_name}'s Workspace")
        return self._result(user, workspace)

    async def login(self, email: str, password: str) -> AuthResult:
        user = await self._users.get_by_email(email.strip().lower())
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid email or password", code="INVALID_CREDENTIALS")
        workspaces = await self._workspaces.list_for_user(user.id)
        if not workspaces:
            workspace = await self._create_workspace(user, f"{user.full_name}'s Workspace")
        else:
            workspace = workspaces[0]
        return self._result(user, workspace)

    async def get_user(self, user_id: str) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationException("User not found", code="USER_NOT_FOUND")
        return user

    async def _create_workspace(self, user: User, name: str) -> Workspace:
        now = utcnow()
        workspace = Workspace(
            id=new_id(),
            name=name.strip() or "Workspace",
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

    def _result(self, user: User, workspace: Workspace) -> AuthResult:
        minutes = self._settings.jwt_access_token_expire_minutes
        return AuthResult(
            access_token=create_access_token(user.id, self._settings),
            expires_in=minutes * 60,
            user=user,
            workspace=workspace,
        )
