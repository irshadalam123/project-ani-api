"""Instagram HTTP client and local mock.

Real calls use httpx. Mock mode never contacts Meta. URLs are built from
``META_GRAPH_BASE_URL`` and ``META_API_VERSION`` so a version change does not
require code edits.

Retries are limited to idempotent GET requests and HTTP 429. Message sends are
not retried inside the client; the worker retries only transient failures and
checks execution state first so a private reply is not sent twice.
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.core.logging import get_logger
from app.integrations.instagram.auth import build_authorization_url, parse_short_lived_token
from app.integrations.instagram.comments import public_reply_path, public_reply_query
from app.integrations.instagram.exceptions import (
    InstagramConfigError,
    InstagramPermanentError,
    InstagramRateLimitError,
    InstagramTransientError,
)
from app.integrations.instagram.media import MEDIA_FIELDS, media_path
from app.integrations.instagram.messaging import private_reply_body, private_reply_path
from app.integrations.instagram.types import (
    InstagramMedia,
    InstagramProfile,
    LongLivedToken,
    SendResult,
    ShortLivedToken,
)

logger = get_logger(__name__)

_RATE_LIMIT_CODES = {4, 17, 32, 613}
_MAX_GET_ATTEMPTS = 3


class InstagramClient:
    """Port implemented by the HTTP client and the mock client."""

    async def get_authorization_url(self, state: str) -> str:
        raise NotImplementedError

    async def exchange_code_for_token(self, code: str) -> ShortLivedToken:
        raise NotImplementedError

    async def exchange_long_lived_token(self, access_token: str) -> LongLivedToken:
        raise NotImplementedError

    async def get_account(self, access_token: str) -> InstagramProfile:
        raise NotImplementedError

    async def get_media(self, access_token: str, media_id: str) -> InstagramMedia:
        raise NotImplementedError

    async def send_private_reply(
        self,
        access_token: str,
        instagram_user_id: str,
        comment_id: str,
        text: str,
    ) -> SendResult:
        raise NotImplementedError

    async def send_public_comment_reply(
        self,
        access_token: str,
        comment_id: str,
        text: str,
    ) -> SendResult:
        raise NotImplementedError

    async def subscribe_webhooks(self, access_token: str, instagram_user_id: str) -> None:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None


class HttpInstagramClient(InstagramClient):
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def get_authorization_url(self, state: str) -> str:
        return build_authorization_url(self._settings, state)

    async def exchange_code_for_token(self, code: str) -> ShortLivedToken:
        self._require_app_credentials()
        response = await self._request(
            "POST",
            self._settings.meta_oauth_token_url,
            retry=False,
            data={
                "client_id": self._settings.meta_app_id,
                "client_secret": self._settings.meta_app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": self._settings.meta_redirect_uri,
                "code": code,
            },
        )
        return parse_short_lived_token(response)

    async def exchange_long_lived_token(self, access_token: str) -> LongLivedToken:
        self._require_app_credentials()
        # TODO(meta): This call is documented on graph.instagram.com/access_token
        # without a version segment. Confirm before changing the path.
        url = f"{self._settings.meta_graph_base_url.rstrip('/')}/access_token"
        payload = await self._request(
            "GET",
            url,
            retry=True,
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": self._settings.meta_app_secret,
            },
        )
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise InstagramPermanentError("Long-lived token response did not include an access token")
        expires_in = payload.get("expires_in")
        return LongLivedToken(
            access_token=token,
            expires_in=int(expires_in) if isinstance(expires_in, int) else None,
            token_type=str(payload.get("token_type") or "bearer"),
        )

    async def get_account(self, access_token: str) -> InstagramProfile:
        # TODO(meta): Confirm /me fields for Instagram Login. user_id, username,
        # name, and account_type are requested because they identify the
        # professional account. Drop any field Meta rejects for your app.
        payload = await self._graph(
            "GET",
            "me",
            access_token,
            retry=True,
            params={"fields": "user_id,username,name,account_type,profile_picture_url"},
        )
        instagram_user_id = payload.get("user_id") or payload.get("id")
        username = payload.get("username")
        if instagram_user_id is None or not isinstance(username, str):
            raise InstagramPermanentError("Instagram account response was missing id or username")
        return InstagramProfile(
            instagram_user_id=str(instagram_user_id),
            username=username,
            name=str(payload["name"]) if payload.get("name") else None,
            account_type=str(payload["account_type"]) if payload.get("account_type") else None,
            profile_picture_url=(
                str(payload["profile_picture_url"]) if payload.get("profile_picture_url") else None
            ),
        )

    async def get_media(self, access_token: str, media_id: str) -> InstagramMedia:
        payload = await self._graph(
            "GET",
            media_path(media_id),
            access_token,
            retry=True,
            params={"fields": MEDIA_FIELDS},
        )
        return InstagramMedia(
            id=str(payload.get("id") or media_id),
            caption=str(payload["caption"]) if payload.get("caption") else None,
            media_type=str(payload["media_type"]) if payload.get("media_type") else None,
            media_product_type=(
                str(payload["media_product_type"]) if payload.get("media_product_type") else None
            ),
            permalink=str(payload["permalink"]) if payload.get("permalink") else None,
        )

    async def send_private_reply(
        self,
        access_token: str,
        instagram_user_id: str,
        comment_id: str,
        text: str,
    ) -> SendResult:
        payload = await self._graph(
            "POST",
            private_reply_path(instagram_user_id),
            access_token,
            retry=False,
            json_body=private_reply_body(comment_id, text),
        )
        return SendResult(
            success=True,
            message_id=str(payload["message_id"]) if payload.get("message_id") else None,
            recipient_id=str(payload["recipient_id"]) if payload.get("recipient_id") else None,
        )

    async def send_public_comment_reply(
        self,
        access_token: str,
        comment_id: str,
        text: str,
    ) -> SendResult:
        payload = await self._graph(
            "POST",
            public_reply_path(comment_id),
            access_token,
            retry=False,
            params=public_reply_query(text),
        )
        reply_id = payload.get("id")
        return SendResult(success=True, message_id=str(reply_id) if reply_id else None)

    async def subscribe_webhooks(self, access_token: str, instagram_user_id: str) -> None:
        # TODO(meta): Docs describe POST /me/subscribed_apps?subscribed_fields=...
        # Confirm whether /{ig-user-id}/subscribed_apps is required for your app.
        _ = instagram_user_id
        await self._graph(
            "POST",
            "me/subscribed_apps",
            access_token,
            retry=False,
            params={"subscribed_fields": self._settings.meta_webhook_fields},
        )

    def _require_app_credentials(self) -> None:
        if not self._settings.meta_app_id.strip() or not self._settings.meta_app_secret.strip():
            raise InstagramConfigError("META_APP_ID and META_APP_SECRET are required")

    def _graph_url(self, path: str) -> str:
        version = self._settings.meta_api_version.strip().strip("/")
        if not version:
            raise InstagramConfigError(
                "META_API_VERSION is not configured. Set the Graph API version enabled for your Meta app."
            )
        base = self._settings.meta_graph_base_url.rstrip("/")
        return f"{base}/{version}/{path.lstrip('/')}"

    async def _graph(
        self,
        method: str,
        path: str,
        access_token: str,
        *,
        retry: bool,
        params: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            method,
            self._graph_url(path),
            retry=retry,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            json_body=json_body,
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        retry: bool,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        attempt = 1
        while True:
            try:
                response = await self._http.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_body,
                )
            except httpx.TimeoutException as exc:
                if retry and attempt < _MAX_GET_ATTEMPTS:
                    await asyncio.sleep(self._backoff(attempt))
                    attempt += 1
                    continue
                raise InstagramTransientError("Instagram request timed out") from exc
            except httpx.TransportError as exc:
                if retry and attempt < _MAX_GET_ATTEMPTS:
                    await asyncio.sleep(self._backoff(attempt))
                    attempt += 1
                    continue
                raise InstagramTransientError("Instagram request failed before a response") from exc

            logger.info(
                "instagram_http_response",
                method=method,
                path=_safe_path(url),
                status_code=response.status_code,
            )
            if response.status_code == 429 or _is_rate_limited(response):
                retry_after = _retry_after(response)
                if retry and attempt < _MAX_GET_ATTEMPTS:
                    await asyncio.sleep(retry_after or self._backoff(attempt))
                    attempt += 1
                    continue
                raise InstagramRateLimitError(retry_after=retry_after)
            if response.status_code >= 500:
                if retry and attempt < _MAX_GET_ATTEMPTS:
                    await asyncio.sleep(self._backoff(attempt))
                    attempt += 1
                    continue
                raise InstagramTransientError(f"Instagram returned HTTP {response.status_code}")
            if response.status_code >= 400:
                raise InstagramPermanentError(_error_message(response))
            if not response.content:
                return {}
            parsed = response.json()
            if isinstance(parsed, dict):
                return parsed
            raise InstagramPermanentError("Instagram returned a non-object JSON response")

    def _backoff(self, attempt: int) -> float:
        return min(8.0, self._settings.retry_base_seconds * (2 ** (attempt - 1)))


class MockInstagramClient(InstagramClient):
    """Deterministic stand-in used when MOCK_EXTERNAL_SERVICES is true."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get_authorization_url(self, state: str) -> str:
        return build_authorization_url(self._settings, state)

    async def exchange_code_for_token(self, code: str) -> ShortLivedToken:
        return ShortLivedToken(
            access_token=f"mock-short-{code}",
            user_id="mock-ig-user",
            permissions=self._settings.oauth_scope_list,
        )

    async def exchange_long_lived_token(self, access_token: str) -> LongLivedToken:
        _ = access_token
        return LongLivedToken(access_token="mock-long-lived-token", expires_in=5_184_000)

    async def get_account(self, access_token: str) -> InstagramProfile:
        _ = access_token
        return InstagramProfile(
            instagram_user_id="mock-ig-user",
            username="mock_professional",
            name="Mock Professional",
            account_type="BUSINESS",
        )

    async def get_media(self, access_token: str, media_id: str) -> InstagramMedia:
        _ = access_token
        return InstagramMedia(id=media_id, caption="Mock media", media_type="IMAGE", media_product_type="FEED")

    async def send_private_reply(
        self,
        access_token: str,
        instagram_user_id: str,
        comment_id: str,
        text: str,
    ) -> SendResult:
        _ = (access_token, instagram_user_id, text)
        return SendResult(success=True, message_id=f"mock_message_{comment_id}")

    async def send_public_comment_reply(
        self,
        access_token: str,
        comment_id: str,
        text: str,
    ) -> SendResult:
        _ = (access_token, text)
        return SendResult(success=True, message_id=f"mock_reply_{comment_id}")

    async def subscribe_webhooks(self, access_token: str, instagram_user_id: str) -> None:
        _ = (access_token, instagram_user_id)
        return None


def build_instagram_client(settings: Settings) -> InstagramClient:
    if settings.mock_external_services:
        return MockInstagramClient(settings)
    return HttpInstagramClient(settings)


def _safe_path(url: str) -> str:
    """Drop the query string so tokens and secrets are not logged."""
    return url.split("?", 1)[0]


def _retry_after(response: httpx.Response) -> float | None:
    header = response.headers.get("retry-after")
    if header and header.isdigit():
        return float(header)
    return None


def _is_rate_limited(response: httpx.Response) -> bool:
    try:
        payload = response.json()
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    error = payload.get("error")
    if not isinstance(error, dict):
        return False
    code = error.get("code")
    return isinstance(code, int) and code in _RATE_LIMIT_CODES


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return f"Instagram request failed with HTTP {response.status_code}"
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return str(error["message"])
    return f"Instagram request failed with HTTP {response.status_code}"


def redact_query(params: dict[str, str]) -> str:
    """Utility for tests. Never includes secret parameter values."""
    hidden = {key: "***" if "secret" in key or "token" in key else value for key, value in params.items()}
    return urlencode(hidden)
