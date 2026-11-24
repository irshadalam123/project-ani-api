"""Automation API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.domain.automation import Action, AutomationStatus, Trigger
from app.schemas.common import Pagination


class AutomationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    instagram_account_id: str = Field(min_length=1)
    status: AutomationStatus = AutomationStatus.DRAFT
    trigger: Trigger
    actions: list[Action] = Field(min_length=1)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "AI Roadmap",
                    "description": "Send the roadmap when someone comments GUIDE",
                    "instagram_account_id": "account-id",
                    "status": "ACTIVE",
                    "trigger": {
                        "type": "COMMENT_KEYWORD",
                        "keywords": ["guide", "ai guide"],
                        "match_type": "CONTAINS",
                    },
                    "actions": [
                        {"type": "PUBLIC_REPLY", "text": "I've sent you a DM 🚀"},
                        {
                            "type": "PRIVATE_REPLY",
                            "text": "Hey {{first_name}}, here's your AI roadmap!",
                        },
                    ],
                }
            ]
        }
    }


class AutomationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    instagram_account_id: str | None = None
    trigger: Trigger | None = None
    actions: list[Action] | None = Field(default=None, min_length=1)


class AutomationPublic(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    name: str
    description: str | None = None
    status: AutomationStatus
    trigger: Trigger
    actions: list[Action]
    created_at: datetime
    updated_at: datetime


class AutomationResponse(BaseModel):
    success: bool = True
    data: AutomationPublic


class AutomationListResponse(BaseModel):
    success: bool = True
    data: list[AutomationPublic]
    pagination: Pagination
