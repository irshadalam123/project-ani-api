"""PostgreSQL implementation of InstagramRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.instagram_account import InstagramAccount
from app.models.orm.instagram_account import InstagramAccountModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.instagram_repository import InstagramRepository


def _to_domain(row: InstagramAccountModel) -> InstagramAccount:
    return InstagramAccount(
        id=row.id,
        workspace_id=row.workspace_id,
        instagram_user_id=row.instagram_user_id,
        username=row.username,
        name=row.name,
        account_type=row.account_type,
        profile_picture_url=row.profile_picture_url,
        webhook_subscribed=row.webhook_subscribed,
        scopes=list(row.scopes),
        connected_at=row.connected_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class PostgresInstagramRepository(InstagramRepository):
    """SQLAlchemy async implementation of :class:`InstagramRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, account: InstagramAccount) -> InstagramAccount:
        row = InstagramAccountModel(
            id=account.id,
            workspace_id=account.workspace_id,
            instagram_user_id=account.instagram_user_id,
            username=account.username,
            name=account.name,
            account_type=account.account_type,
            profile_picture_url=account.profile_picture_url,
            webhook_subscribed=account.webhook_subscribed,
            scopes=account.scopes,
            connected_at=account.connected_at,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("instagram_account") from exc
        await self._session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, account_id: str) -> InstagramAccount | None:
        row = await self._session.get(InstagramAccountModel, account_id)
        return _to_domain(row) if row else None

    async def get_by_instagram_user_id(
        self, instagram_user_id: str
    ) -> InstagramAccount | None:
        result = await self._session.execute(
            select(InstagramAccountModel).where(
                InstagramAccountModel.instagram_user_id == instagram_user_id
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_by_workspace(self, workspace_id: str) -> list[InstagramAccount]:
        result = await self._session.execute(
            select(InstagramAccountModel).where(
                InstagramAccountModel.workspace_id == workspace_id
            )
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def list_all(self) -> list[InstagramAccount]:
        result = await self._session.execute(select(InstagramAccountModel))
        return [_to_domain(row) for row in result.scalars().all()]

    async def update(self, account: InstagramAccount) -> InstagramAccount:
        row = await self._session.get(InstagramAccountModel, account.id)
        if row is None:
            raise RecordNotFoundError(account.id)
        row.username = account.username
        row.name = account.name
        row.account_type = account.account_type
        row.profile_picture_url = account.profile_picture_url
        row.webhook_subscribed = account.webhook_subscribed
        row.scopes = account.scopes
        row.connected_at = account.connected_at
        row.updated_at = account.updated_at
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def delete(self, workspace_id: str, account_id: str) -> bool:
        row = await self._session.get(InstagramAccountModel, account_id)
        if row is None or row.workspace_id != workspace_id:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
