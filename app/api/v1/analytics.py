"""Workspace analytics overview."""

from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.core.dependencies import get_analytics_service, get_workspace_context
from app.schemas.analytics import AnalyticsOverviewData, AnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService
from app.services.workspace_service import WorkspaceContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Automation activity overview")
async def overview(
    context: WorkspaceContext = Depends(get_workspace_context),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverviewResponse:
    data = await service.overview(context.workspace.id)
    return AnalyticsOverviewResponse(data=AnalyticsOverviewData.model_validate(asdict(data)))
