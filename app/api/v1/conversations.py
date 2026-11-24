"""Conversation reads. This is not a real-time inbox."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_conversation_service, get_workspace_context, pagination_params
from app.models.domain.conversation import Conversation
from app.models.domain.message import Message
from app.schemas.common import Pagination, PaginationParams
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationPublic,
    ConversationResponse,
    MessageListResponse,
    MessagePublic,
)
from app.services.conversation_service import ConversationService
from app.services.workspace_service import WorkspaceContext

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse, summary="List conversations")
async def list_conversations(
    context: WorkspaceContext = Depends(get_workspace_context),
    page: PaginationParams = Depends(pagination_params),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    items, total = await service.list_conversations(
        context.workspace.id, page=page.page, page_size=page.page_size
    )
    return ConversationListResponse(
        data=[ConversationPublic.model_validate(item.model_dump()) for item in items],
        pagination=Pagination(page=page.page, page_size=page.page_size, total=total),
    )


@router.get("/{conversation_id}", response_model=ConversationResponse, summary="Get a conversation")
async def get_conversation(
    conversation_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    conversation: Conversation = await service.get(context.workspace.id, conversation_id)
    return ConversationResponse(data=ConversationPublic.model_validate(conversation.model_dump()))


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="List messages in a conversation",
)
async def list_messages(
    conversation_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    page: PaginationParams = Depends(pagination_params),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageListResponse:
    items, total = await service.list_messages(
        context.workspace.id,
        conversation_id,
        page=page.page,
        page_size=page.page_size,
    )
    messages: list[Message] = items
    return MessageListResponse(
        data=[MessagePublic.model_validate(item.model_dump()) for item in messages],
        pagination=Pagination(page=page.page, page_size=page.page_size, total=total),
    )
