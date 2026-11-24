"""Data an action needs, without Instagram HTTP details."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class CommentContext:
    workspace_id: str
    instagram_account_id: str
    instagram_business_user_id: str
    comment_id: str
    media_id: str | None
    comment_text: str
    commenter_id: str
    commenter_username: str | None
    contact_id: str | None
    execution_id: str
    automation_id: str
    webhook_event_id: str
    variables: dict[str, str] = field(default_factory=dict)
