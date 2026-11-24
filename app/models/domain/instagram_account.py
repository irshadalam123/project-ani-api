"""Connected Instagram professional account.

Access tokens are never stored on this model. They live behind TokenManager.
"""

from datetime import datetime

from pydantic import BaseModel


class InstagramAccount(BaseModel):
    id: str
    workspace_id: str
    instagram_user_id: str
    username: str
    name: str | None = None
    account_type: str | None = None
    profile_picture_url: str | None = None
    webhook_subscribed: bool = False
    scopes: list[str] = []
    connected_at: datetime
    created_at: datetime
    updated_at: datetime
