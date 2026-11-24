"""Automation CRUD plus activate and pause."""

from fastapi import APIRouter, Depends, Response

from app.core.dependencies import (
    get_automation_service,
    get_workspace_context,
    pagination_params,
    rate_limit,
)
from app.models.domain.automation import Automation
from app.schemas.automation import (
    AutomationCreateRequest,
    AutomationListResponse,
    AutomationPublic,
    AutomationResponse,
    AutomationUpdateRequest,
)
from app.schemas.common import Pagination, PaginationParams
from app.services.automation_service import AutomationService
from app.services.workspace_service import WorkspaceContext

router = APIRouter(prefix="/automations", tags=["automations"])


def _public(automation: Automation) -> AutomationPublic:
    return AutomationPublic.model_validate(automation.model_dump())


@router.post(
    "",
    response_model=AutomationResponse,
    status_code=201,
    summary="Create an automation",
    dependencies=[Depends(rate_limit("automation_create"))],
)
async def create_automation(
    body: AutomationCreateRequest,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AutomationService = Depends(get_automation_service),
) -> AutomationResponse:
    automation = await service.create(
        context.workspace.id,
        name=body.name,
        description=body.description,
        instagram_account_id=body.instagram_account_id,
        trigger=body.trigger,
        actions=body.actions,
        status=body.status,
    )
    return AutomationResponse(data=_public(automation))


@router.get("", response_model=AutomationListResponse, summary="List automations")
async def list_automations(
    context: WorkspaceContext = Depends(get_workspace_context),
    page: PaginationParams = Depends(pagination_params),
    service: AutomationService = Depends(get_automation_service),
) -> AutomationListResponse:
    items, total = await service.list_automations(
        context.workspace.id, page=page.page, page_size=page.page_size
    )
    return AutomationListResponse(
        data=[_public(item) for item in items],
        pagination=Pagination(page=page.page, page_size=page.page_size, total=total),
    )


@router.get("/{automation_id}", response_model=AutomationResponse, summary="Get an automation")
async def get_automation(
    automation_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AutomationService = Depends(get_automation_service),
) -> AutomationResponse:
    automation = await service.get(context.workspace.id, automation_id)
    return AutomationResponse(data=_public(automation))


@router.patch("/{automation_id}", response_model=AutomationResponse, summary="Update an automation")
async def update_automation(
    automation_id: str,
    body: AutomationUpdateRequest,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AutomationService = Depends(get_automation_service),
) -> AutomationResponse:
    fields = body.model_fields_set
    automation = await service.update(
        context.workspace.id,
        automation_id,
        name=body.name,
        description=body.description,
        trigger=body.trigger,
        actions=body.actions,
        instagram_account_id=body.instagram_account_id,
        description_set="description" in fields,
    )
    return AutomationResponse(data=_public(automation))


@router.delete("/{automation_id}", status_code=204, summary="Delete an automation")
async def delete_automation(
    automation_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AutomationService = Depends(get_automation_service),
) -> Response:
    await service.delete(context.workspace.id, automation_id)
    return Response(status_code=204)


@router.post("/{automation_id}/activate", response_model=AutomationResponse, summary="Activate an automation")
async def activate_automation(
    automation_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AutomationService = Depends(get_automation_service),
) -> AutomationResponse:
    automation = await service.activate(context.workspace.id, automation_id)
    return AutomationResponse(data=_public(automation))


@router.post("/{automation_id}/pause", response_model=AutomationResponse, summary="Pause an automation")
async def pause_automation(
    automation_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AutomationService = Depends(get_automation_service),
) -> AutomationResponse:
    automation = await service.pause(context.workspace.id, automation_id)
    return AutomationResponse(data=_public(automation))
