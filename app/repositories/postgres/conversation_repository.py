"""PostgreSQL implementation of ConversationRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.conversation import Conversation, ConversationStatus
from app.models.domain.message import Message, MessageDirection, MessageType
from app.models.orm.conversation import ConversationModel
from app.models.orm.message import MessageModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.conversation_repository import ConversationRepository


def _conv_to_domain(row: ConversationModel) -> Conversation:
    return Conversation(
        id=row.id,
        workspace_id=row.workspace_id,
        instagram_account_id=row.instagram_account_id,
        contact_id=row.contact_id,
        status=ConversationStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _msg_to_domain(row: MessageModel) -> Message:
    return Message(
        id=row.id,
        conversation_id=row.conversation_id,
        workspace_id=row.workspace_id,
        direction=MessageDirection(row.direction),
        message_type=MessageType(row.message_type),
        text=row.text,
        external_message_id=row.external_message_id,
        created_at=row.created_at,
    )


class PostgresConversationRepository(ConversationRepository):
    """SQLAlchemy async implementation of :class:`ConversationRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, conversation: Conversation) -> Conversation:
        row = ConversationModel(
            id=conversation.id,
            workspace_id=conversation.workspace_id,
            instagram_account_id=conversation.instagram_account_id,
            contact_id=conversation.contact_id,
            status=conversation.status.value,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("conversation") from exc
        await self._session.refresh(row)
        return _conv_to_domain(row)

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        row = await self._session.get(ConversationModel, conversation_id)
        return _conv_to_domain(row) if row else None

    async def get_for_contact(
        self,
        workspace_id: str,
        instagram_account_id: str,
        contact_id: str,
    ) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.workspace_id == workspace_id,
                ConversationModel.instagram_account_id == instagram_account_id,
                ConversationModel.contact_id == contact_id,
            )
        )
        row = result.scalar_one_or_none()
        return _conv_to_domain(row) if row else None

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Conversation], int]:
        base_q = select(ConversationModel).where(
            ConversationModel.workspace_id == workspace_id
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            base_q.order_by(ConversationModel.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_conv_to_domain(r) for r in result.scalars().all()], total

    async def update(self, conversation: Conversation) -> Conversation:
        row = await self._session.get(ConversationModel, conversation.id)
        if row is None:
            raise RecordNotFoundError(conversation.id)
        row.status = conversation.status.value
        row.updated_at = conversation.updated_at
        await self._session.flush()
        await self._session.refresh(row)
        return _conv_to_domain(row)

    async def add_message(self, message: Message) -> Message:
        row = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            workspace_id=message.workspace_id,
            direction=message.direction.value,
            message_type=message.message_type.value,
            text=message.text,
            external_message_id=message.external_message_id,
            created_at=message.created_at,
        )
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("message") from exc
        await self._session.refresh(row)
        return _msg_to_domain(row)

    async def list_messages(
        self,
        conversation_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Message], int]:
        base_q = select(MessageModel).where(
            MessageModel.conversation_id == conversation_id
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            base_q.order_by(MessageModel.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_msg_to_domain(r) for r in result.scalars().all()], total
