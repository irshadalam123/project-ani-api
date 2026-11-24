"""Execution history."""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_execution_service, get_workspace_context, pagination_params
from app.schemas.common import Pagination, PaginationParams
from app.schemas.execution import ExecutionListResponse, ExecutionPublic, ExecutionResponse
from app.services.execution_service import ExecutionService
from app.services.workspace_service import WorkspaceContext

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=ExecutionListResponse, summary="List automation executions")
async def list_executions(
    context: WorkspaceContext = Depends(get_workspace_context),
    page: PaginationParams = Depends(pagination_params),
    automation_id: str | None = Query(default=None),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionListResponse:
    items, total = await service.list(
        context.workspace.id,
        page=page.page,
        page_size=page.page_size,
        automation_id=automation_id,
    )
    return ExecutionListResponse(
        data=[ExecutionPublic.model_validate(item.model_dump()) for item in items],
        pagination=Pagination(page=page.page, page_size=page.page_size, total=total),
    )


@router.get("/{execution_id}", response_model=ExecutionResponse, summary="Get an execution")
async def get_execution(
    execution_id: str,
    context: WorkspaceContext = Depends(get_workspace_context),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionResponse:
    execution = await service.get(context.workspace.id, execution_id)
    return ExecutionResponse(data=ExecutionPublic.model_validate(execution.model_dump()))
