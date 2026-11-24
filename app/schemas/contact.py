"""Contact API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import Pagination


class ContactPublic(BaseModel):
    id: str
    workspace_id: str
    instagram_account_id: str
    instagram_user_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)


class ContactResponse(BaseModel):
    success: bool = True
    data: ContactPublic


class ContactListResponse(BaseModel):
    success: bool = True
    data: list[ContactPublic]
    pagination: Pagination
