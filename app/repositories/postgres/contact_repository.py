"""PostgreSQL implementation of ContactRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.contact import Contact
from app.models.orm.contact import ContactModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.contact_repository import ContactRepository


def _to_domain(row: ContactModel) -> Contact:
    return Contact(
        id=row.id,
        workspace_id=row.workspace_id,
        instagram_account_id=row.instagram_account_id,
        instagram_user_id=row.instagram_user_id,
        username=row.username,
        first_name=row.first_name,
        last_name=row.last_name,
        created_at=row.created_at,
        updated_at=row.updated_at,
        metadata=dict(row.metadata_),
    )


class PostgresContactRepository(ContactRepository):
    """SQLAlchemy async implementation of :class:`ContactRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, contact: Contact) -> Contact:
        row = ContactModel(
            id=contact.id,
            workspace_id=contact.workspace_id,
            instagram_account_id=contact.instagram_account_id,
            instagram_user_id=contact.instagram_user_id,
            username=contact.username,
            first_name=contact.first_name,
            last_name=contact.last_name,
            metadata_=contact.metadata,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("contact") from exc
        await self._session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, contact_id: str) -> Contact | None:
        row = await self._session.get(ContactModel, contact_id)
        return _to_domain(row) if row else None

    async def get_by_instagram_user(
        self,
        workspace_id: str,
        instagram_account_id: str,
        instagram_user_id: str,
    ) -> Contact | None:
        result = await self._session.execute(
            select(ContactModel).where(
                ContactModel.workspace_id == workspace_id,
                ContactModel.instagram_account_id == instagram_account_id,
                ContactModel.instagram_user_id == instagram_user_id,
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Contact], int]:
        base_q = select(ContactModel).where(ContactModel.workspace_id == workspace_id)
        count_result = await self._session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            base_q.order_by(ContactModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_to_domain(r) for r in result.scalars().all()], total

    async def update(self, contact: Contact) -> Contact:
        row = await self._session.get(ContactModel, contact.id)
        if row is None:
            raise RecordNotFoundError(contact.id)
        row.username = contact.username
        row.first_name = contact.first_name
        row.last_name = contact.last_name
        row.metadata_ = contact.metadata
        row.updated_at = contact.updated_at
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)
