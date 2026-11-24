"""Public comment replies.

Documented edge: ``POST /{ig-comment-id}/replies?message={message}``.

TODO(meta): Confirm this edge on ``graph.instagram.com`` for Instagram Login.
The reference page has historically shown ``graph.facebook.com`` for Facebook
Login. The host and version here come from configuration.
Only top-level comments can be replied to. Hidden comments and live-video
comments are rejected by Meta.
"""

from urllib.parse import quote

from app.core.config import Settings


def public_reply_path(comment_id: str) -> str:
    return f"{quote(comment_id, safe='')}/replies"


def public_reply_query(message: str) -> dict[str, str]:
    return {"message": message}


def require_version(settings: Settings) -> str:
    version = settings.meta_api_version.strip().strip("/")
    if not version:
        raise ValueError("META_API_VERSION is not configured")
    return version
