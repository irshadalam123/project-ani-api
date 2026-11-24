"""Contacts captured from Instagram comments."""

from __future__ import annotations

from app.core.exceptions import NotFoundException
from app.models.domain.contact import Contact
from app.repositories.interfaces.contact_repository import ContactRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id


class ContactService:
    def __init__(self, contacts: ContactRepository) -> None:
        self._contacts = contacts

    async def list(self, workspace_id: str, *, page: int, page_size: int) -> tuple[list[Contact], int]:
        return await self._contacts.list_by_workspace(workspace_id, page=page, page_size=page_size)

    async def get(self, workspace_id: str, contact_id: str) -> Contact:
        contact = await self._contacts.get_by_id(contact_id)
        if contact is None or contact.workspace_id != workspace_id:
            raise NotFoundException("Contact not found", code="CONTACT_NOT_FOUND")
        return contact

    async def upsert_from_comment(
        self,
        *,
        workspace_id: str,
        instagram_account_id: str,
        instagram_user_id: str,
        username: str | None,
    ) -> Contact:
        existing = await self._contacts.get_by_instagram_user(
            workspace_id,
            instagram_account_id,
            instagram_user_id,
        )
        now = utcnow()
        if existing is None:
            contact = Contact(
                id=new_id(),
                workspace_id=workspace_id,
                instagram_account_id=instagram_account_id,
                instagram_user_id=instagram_user_id,
                username=username,
                created_at=now,
                updated_at=now,
            )
            return await self._contacts.add(contact)
        if username and existing.username != username:
            existing.username = username
            existing.updated_at = now
            return await self._contacts.update(existing)
        return existing
