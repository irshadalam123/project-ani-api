"""One run of an automation against a single comment."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExecutionStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ActionResultStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ActionResult(BaseModel):
    action_index: int
    action_type: str
    status: ActionResultStatus = ActionResultStatus.PENDING
    external_id: str | None = None
    error: str | None = None
    rendered_text: str | None = None


class Execution(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    automation_id: str
    webhook_event_id: str
    comment_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    action_results: list[ActionResult] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
