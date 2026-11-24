"""Values exchanged with the Instagram integration.

These types describe outcomes of documented Meta calls. They are not a copy of
every Graph field. Confirm field names against the current Meta documentation
before relying on them in production.
"""

from pydantic import BaseModel, Field


class ShortLivedToken(BaseModel):
    access_token: str
    user_id: str
    permissions: list[str] = Field(default_factory=list)

    def __repr__(self) -> str:
        return f"ShortLivedToken(user_id={self.user_id!r}, access_token='***')"


class LongLivedToken(BaseModel):
    access_token: str
    expires_in: int | None = None
    token_type: str = "bearer"

    def __repr__(self) -> str:
        return "LongLivedToken(access_token='***')"


class InstagramProfile(BaseModel):
    instagram_user_id: str
    username: str
    name: str | None = None
    account_type: str | None = None
    profile_picture_url: str | None = None


class InstagramMedia(BaseModel):
    id: str
    caption: str | None = None
    media_type: str | None = None
    media_product_type: str | None = None
    permalink: str | None = None


class SendResult(BaseModel):
    success: bool
    message_id: str | None = None
    recipient_id: str | None = None


class StoredToken(BaseModel):
    """Token held by TokenManager. Never log or return this from the API."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    scopes: list[str] = Field(default_factory=list)

    def __repr__(self) -> str:
        return "StoredToken(access_token='***')"


class NormalizedComment(BaseModel):
    """Comment extracted from a Meta webhook or the local mock payload."""

    external_event_id: str
    event_type: str
    comment_id: str
    media_id: str | None = None
    text: str = ""
    commenter_id: str
    commenter_username: str | None = None
    business_account_id: str | None = None
    parent_id: str | None = None
    raw: dict[str, object] = Field(default_factory=dict)
