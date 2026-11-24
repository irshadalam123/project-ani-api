"""OAuth helpers for Instagram Business Login.

Documented endpoints (confirm in the Meta App Dashboard before production):

- Authorization: https://www.instagram.com/oauth/authorize
- Code exchange: https://api.instagram.com/oauth/access_token
- Long-lived exchange: https://graph.instagram.com/access_token
  with grant_type=ig_exchange_token

TODO(meta): The short-lived token JSON shape has varied between a flat object
and a ``data`` array. ``parse_short_lived_token`` accepts both. Verify the
shape returned for your app.
"""

from urllib.parse import urlencode

from app.core.config import Settings
from app.integrations.instagram.exceptions import InstagramPermanentError
from app.integrations.instagram.types import ShortLivedToken


def build_authorization_url(settings: Settings, state: str) -> str:
    """Build the Meta authorization URL from configuration.

    TODO(meta): META_APP_ID, META_APP_SECRET, META_REDIRECT_URI, and
    META_OAUTH_SCOPES must match the Instagram product settings in the Meta
    App Dashboard. Do not request scopes the app has not been approved for.
    """
    client_id = settings.meta_app_id.strip() or ("mock-app-id" if settings.mock_external_services else "")
    if not client_id:
        raise InstagramPermanentError(
            "META_APP_ID is not configured",
            code="INSTAGRAM_NOT_CONFIGURED",
        )
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": settings.meta_redirect_uri,
            "response_type": "code",
            "scope": ",".join(settings.oauth_scope_list),
            "state": state,
        }
    )
    return f"{settings.meta_oauth_authorize_url}?{query}"


def parse_short_lived_token(payload: dict[str, object]) -> ShortLivedToken:
    record: dict[str, object] = payload
    data = payload.get("data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        record = data[0]
    access_token = record.get("access_token")
    user_id = record.get("user_id")
    if not isinstance(access_token, str) or not access_token:
        raise InstagramPermanentError("Instagram token response did not include an access token")
    if user_id is None:
        raise InstagramPermanentError("Instagram token response did not include a user id")
    permissions_raw = record.get("permissions") or record.get("scope") or []
    permissions: list[str] = []
    if isinstance(permissions_raw, str):
        permissions = [item.strip() for item in permissions_raw.split(",") if item.strip()]
    elif isinstance(permissions_raw, list):
        permissions = [str(item) for item in permissions_raw]
    return ShortLivedToken(
        access_token=access_token,
        user_id=str(user_id),
        permissions=permissions,
    )
