"""Contact reads."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_contact_service, get_workspace_context, pagination_params
from app.models.domain.contact import Contact
from app.schemas.common import Pagination, PaginationParams
from app.schemas.contact import ContactListResponse, ContactPublic, ContactResponse
from app.services.contact_service import ContactService
from app.services.workspace_service import WorkspaceContext

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _public(contact: Contact) -> ContactPublic:
    return ContactPublic.model_validate(contact.model_dump())


@router.get("", response_model=ContactListResponse, summary="List contacts")
async def list_contacts(
    context: WorkspaceContext = Depends(get_workspace_context),
    page: PaginationParams = Depends(pagination_params),
    service: ContactService = Depends(get_contact_service),
) -> ContactListResponse:
    items, total = await service.list(context.workspace.id, page=page.page, page_size=page.page_size)
    return ContactListResponse(
        data=[_public(item) for item in items],
        pagination=Pagination(page=page.page, page_size=page.page_size, total=total),
    )


@router.get("/{contact_id}", response_model=ContactResponse, summary="Get a contact")
async def get_contact(
    contact_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: ContactService = Depends(get_contact_service),
) -> ContactResponse:
    contact = await service.get(context.workspace.id, contact_id)
    return ContactResponse(data=_public(contact))
