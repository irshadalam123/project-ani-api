"""Automation definition: trigger, conditions, and actions."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class AutomationStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class MatchType(StrEnum):
    EXACT = "EXACT"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    REGEX = "REGEX"


class TriggerType(StrEnum):
    COMMENT_KEYWORD = "COMMENT_KEYWORD"
    ANY_COMMENT = "ANY_COMMENT"


class ActionType(StrEnum):
    PUBLIC_REPLY = "PUBLIC_REPLY"
    PRIVATE_REPLY = "PRIVATE_REPLY"


class KeywordTrigger(BaseModel):
    type: Literal["COMMENT_KEYWORD"] = "COMMENT_KEYWORD"
    keywords: list[str] = Field(min_length=1)
    match_type: MatchType = MatchType.CONTAINS


class AnyCommentTrigger(BaseModel):
    type: Literal["ANY_COMMENT"] = "ANY_COMMENT"


Trigger = Annotated[KeywordTrigger | AnyCommentTrigger, Field(discriminator="type")]


class PublicReplyAction(BaseModel):
    type: Literal["PUBLIC_REPLY"] = "PUBLIC_REPLY"
    text: str = Field(min_length=1, max_length=1000)


class PrivateReplyAction(BaseModel):
    type: Literal["PRIVATE_REPLY"] = "PRIVATE_REPLY"
    text: str = Field(min_length=1, max_length=1000)


Action = Annotated[PublicReplyAction | PrivateReplyAction, Field(discriminator="type")]


class Automation(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    name: str
    description: str | None = None
    status: AutomationStatus = AutomationStatus.DRAFT
    trigger: Trigger
    actions: list[Action]
    created_at: datetime
    updated_at: datetime
