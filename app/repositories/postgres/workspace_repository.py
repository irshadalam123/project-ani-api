"""PostgreSQL implementation of WorkspaceRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.user import WorkspaceMember
from app.models.domain.workspace import Workspace
from app.models.orm.user import WorkspaceMemberModel
from app.models.orm.workspace import WorkspaceModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.workspace_repository import WorkspaceRepository


def _workspace_to_domain(row: WorkspaceModel) -> Workspace:
    return Workspace(
        id=row.id,
        name=row.name,
        owner_id=row.owner_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _member_to_domain(row: WorkspaceMemberModel) -> WorkspaceMember:
    return WorkspaceMember(
        id=row.id,
        workspace_id=row.workspace_id,
        user_id=row.user_id,
        role=row.role,
        created_at=row.created_at,
    )


class PostgresWorkspaceRepository(WorkspaceRepository):
    """SQLAlchemy async implementation of :class:`WorkspaceRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workspace: Workspace) -> Workspace:
        """Insert a new workspace and commit the transaction."""
        row = WorkspaceModel(
            id=workspace.id,
            name=workspace.name,
            owner_id=workspace.owner_id,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("workspace") from exc
        await self._session.refresh(row)
        return _workspace_to_domain(row)

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        row = await self._session.get(WorkspaceModel, workspace_id)
        return _workspace_to_domain(row) if row else None

    async def update(self, workspace: Workspace) -> Workspace:
        row = await self._session.get(WorkspaceModel, workspace.id)
        if row is None:
            raise RecordNotFoundError(workspace.id)
        row.name = workspace.name
        row.owner_id = workspace.owner_id
        row.updated_at = workspace.updated_at
        await self._session.flush()
        await self._session.refresh(row)
        return _workspace_to_domain(row)

    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        row = WorkspaceMemberModel(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role,
            created_at=member.created_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("workspace_member") from exc
        await self._session.refresh(row)
        return _member_to_domain(row)

    async def get_membership(
        self, workspace_id: str, user_id: str
    ) -> WorkspaceMember | None:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        return _member_to_domain(row) if row else None

    async def list_for_user(self, user_id: str) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel)
            .join(
                WorkspaceMemberModel,
                WorkspaceMemberModel.workspace_id == WorkspaceModel.id,
            )
            .where(WorkspaceMemberModel.user_id == user_id)
        )
        return [_workspace_to_domain(row) for row in result.scalars().all()]
