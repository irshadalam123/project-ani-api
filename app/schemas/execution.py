"""Execution history schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.models.domain.execution import ActionResult, ExecutionStatus
from app.schemas.common import Pagination


class ExecutionPublic(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    automation_id: str
    webhook_event_id: str
    comment_id: str
    status: ExecutionStatus
    action_results: list[ActionResult]
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class ExecutionResponse(BaseModel):
    success: bool = True
    data: ExecutionPublic


class ExecutionListResponse(BaseModel):
    success: bool = True
    data: list[ExecutionPublic]
    pagination: Pagination
