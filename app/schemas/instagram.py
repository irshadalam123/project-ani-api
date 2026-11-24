"""Instagram connection schemas. Access tokens are never included."""

from datetime import datetime

from pydantic import BaseModel, Field


class ConnectData(BaseModel):
    authorization_url: str
    state: str


class ConnectResponse(BaseModel):
    success: bool = True
    data: ConnectData


class InstagramAccountPublic(BaseModel):
    id: str
    workspace_id: str
    instagram_user_id: str
    username: str
    name: str | None = None
    account_type: str | None = None
    profile_picture_url: str | None = None
    webhook_subscribed: bool
    scopes: list[str] = Field(default_factory=list)
    connected_at: datetime
    created_at: datetime
    updated_at: datetime


class InstagramAccountResponse(BaseModel):
    success: bool = True
    data: InstagramAccountPublic


class InstagramAccountListResponse(BaseModel):
    success: bool = True
    data: list[InstagramAccountPublic]


class DeletedResponse(BaseModel):
    success: bool = True
    data: dict[str, bool]
