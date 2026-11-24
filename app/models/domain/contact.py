"""Instagram contact captured from a comment or message."""

from datetime import datetime

from pydantic import BaseModel, Field


class Contact(BaseModel):
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
