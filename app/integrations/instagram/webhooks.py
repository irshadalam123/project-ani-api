"""Instagram webhook verification, signatures, and payload parsing.

Meta's webhook handshake is a GET with hub.mode, hub.verify_token, and
hub.challenge. Event posts are signed with X-Hub-Signature-256 using the
app secret.

TODO(meta): Comment notifications are documented both as ``entry.field`` /
``entry.value`` (Instagram Login) and as ``entry.changes[]`` (older Graph
webhook shape). This parser accepts both. Confirm which shape your app
receives after you subscribe to the ``comments`` field.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from app.core.exceptions import WebhookVerificationException
from app.integrations.instagram.types import NormalizedComment


def verify_subscription(
    *,
    mode: str | None,
    verify_token: str | None,
    challenge: str | None,
    expected_token: str,
) -> str:
    if not expected_token:
        raise WebhookVerificationException("META_WEBHOOK_VERIFY_TOKEN is not configured")
    if mode != "subscribe" or not verify_token or not challenge:
        raise WebhookVerificationException("Webhook verification parameters are incomplete")
    if not hmac.compare_digest(verify_token, expected_token):
        raise WebhookVerificationException("Webhook verify token does not match")
    return challenge


def verify_signature(body: bytes, signature_header: str | None, app_secret: str) -> None:
    """Validate ``X-Hub-Signature-256``.

    When the app secret is empty (local mock mode) verification is skipped.
    Production startup refuses an empty secret.
    """
    if not app_secret:
        return
    if not signature_header or not signature_header.startswith("sha256="):
        raise WebhookVerificationException("Missing Instagram webhook signature")
    digest = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    if not hmac.compare_digest(expected, signature_header):
        raise WebhookVerificationException("Invalid Instagram webhook signature")


def parse_webhook_body(body: bytes, *, allow_simplified: bool) -> list[NormalizedComment]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebhookVerificationException("Webhook body is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise WebhookVerificationException("Webhook body must be a JSON object")
    if payload.get("object") == "instagram":
        return _parse_official(payload)
    if allow_simplified and _looks_simplified(payload):
        return [_parse_simplified(payload)]
    return []


def _looks_simplified(payload: dict[str, Any]) -> bool:
    return all(key in payload for key in ("comment_id", "text", "instagram_user_id"))


def _parse_simplified(payload: dict[str, Any]) -> NormalizedComment:
    comment_id = str(payload["comment_id"])
    business_id = payload.get("instagram_business_account_id") or payload.get("recipient_id")
    return NormalizedComment(
        external_event_id=f"comments:{comment_id}",
        event_type="COMMENT",
        comment_id=comment_id,
        media_id=str(payload["media_id"]) if payload.get("media_id") is not None else None,
        text=str(payload.get("text") or ""),
        commenter_id=str(payload["instagram_user_id"]),
        commenter_username=str(payload["username"]) if payload.get("username") else None,
        business_account_id=str(business_id) if business_id else None,
        parent_id=str(payload["parent_id"]) if payload.get("parent_id") else None,
        raw=payload,
    )


def _parse_official(payload: dict[str, Any]) -> list[NormalizedComment]:
    comments: list[NormalizedComment] = []
    entries = payload.get("entry")
    if not isinstance(entries, list):
        return comments
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        business_id = str(entry["id"]) if entry.get("id") is not None else None
        changes = entry.get("changes")
        if isinstance(changes, list):
            for change in changes:
                if not isinstance(change, dict):
                    continue
                field = str(change.get("field") or "")
                value = change.get("value")
                if field in {"comments", "live_comments"} and isinstance(value, dict):
                    parsed = _parse_comment_value(business_id, field, value)
                    if parsed is not None:
                        comments.append(parsed)
            continue
        field = str(entry.get("field") or "")
        value = entry.get("value")
        if field in {"comments", "live_comments"} and isinstance(value, dict):
            parsed = _parse_comment_value(business_id, field, value)
            if parsed is not None:
                comments.append(parsed)
    return comments


def _parse_comment_value(
    business_id: str | None,
    field: str,
    value: dict[str, Any],
) -> NormalizedComment | None:
    comment_id = value.get("id")
    if comment_id is None:
        return None
    from_value = value.get("from")
    media_value = value.get("media")
    sender: dict[str, Any] = from_value if isinstance(from_value, dict) else {}
    media: dict[str, Any] = media_value if isinstance(media_value, dict) else {}
    event_type = "LIVE_COMMENT" if field == "live_comments" else "COMMENT"
    comment_id_text = str(comment_id)
    return NormalizedComment(
        external_event_id=f"{field}:{comment_id_text}",
        event_type=event_type,
        comment_id=comment_id_text,
        media_id=str(media["id"]) if isinstance(media, dict) and media.get("id") is not None else None,
        text=str(value.get("text") or ""),
        commenter_id=str(sender.get("id") or ""),
        commenter_username=str(sender["username"]) if sender.get("username") else None,
        business_account_id=business_id,
        parent_id=str(value["parent_id"]) if value.get("parent_id") else None,
        raw={"field": field, "value": value, "business_account_id": business_id},
    )
