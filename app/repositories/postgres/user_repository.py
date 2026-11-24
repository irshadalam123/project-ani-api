"""PostgreSQL implementation of UserRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.user import User, WorkspaceMember
from app.models.orm.user import UserModel, WorkspaceMemberModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.user_repository import UserRepository


def _to_domain(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        full_name=row.full_name,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_orm(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class PostgresUserRepository(UserRepository):
    """SQLAlchemy async implementation of :class:`UserRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        """
        Insert a new user and commit the transaction so the record persists.
        """
        row = _to_orm(user)
        self._session.add(row)
        try:
            await self._session.flush()
            # Commit the transaction after a successful flush.
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("email") from exc
        await self._session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, user_id: str) -> User | None:
        row = await self._session.get(UserModel, user_id)
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def update(self, user: User) -> User:
        row = await self._session.get(UserModel, user.id)
        if row is None:
            raise RecordNotFoundError(user.id)
        row.email = user.email
        row.password_hash = user.password_hash
        row.full_name = user.full_name
        row.is_active = user.is_active
        row.updated_at = user.updated_at
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)
