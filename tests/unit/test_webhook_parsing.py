"""Webhook signature checks and payload normalization."""

import hashlib
import hmac
import json

import pytest

from app.core.exceptions import WebhookVerificationException
from app.integrations.instagram.webhooks import parse_webhook_body, verify_signature, verify_subscription


def test_verification_handshake() -> None:
    assert verify_subscription(mode="subscribe", verify_token="secret", challenge="123", expected_token="secret") == "123"
    with pytest.raises(WebhookVerificationException):
        verify_subscription(mode="subscribe", verify_token="nope", challenge="123", expected_token="secret")


def test_signature_round_trip() -> None:
    body = b'{"object":"instagram"}'
    secret = "app-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    verify_signature(body, f"sha256={digest}", secret)
    with pytest.raises(WebhookVerificationException):
        verify_signature(body, "sha256=deadbeef", secret)


def test_parse_simplified_and_official_comment() -> None:
    simplified = json.dumps(
        {
            "comment_id": "comment_123",
            "media_id": "media_123",
            "instagram_user_id": "user_456",
            "username": "testuser",
            "text": "GUIDE",
        }
    ).encode()
    parsed = parse_webhook_body(simplified, allow_simplified=True)
    assert parsed[0].comment_id == "comment_123"
    assert parsed[0].external_event_id == "comments:comment_123"
    assert parse_webhook_body(simplified, allow_simplified=False) == []

    official = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig_business",
                "time": 1,
                "field": "comments",
                "value": {
                    "id": "c1",
                    "text": "guide",
                    "from": {"id": "commenter", "username": "ada"},
                    "media": {"id": "m1", "media_product_type": "FEED"},
                },
            }
        ],
    }
    comments = parse_webhook_body(json.dumps(official).encode(), allow_simplified=False)
    assert comments[0].business_account_id == "ig_business"
    assert comments[0].commenter_username == "ada"
    assert comments[0].text == "guide"

    changes = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig_business",
                "changes": [{"field": "comments", "value": {"id": "c2", "text": "hello", "from": {"id": "u"}}}],
            }
        ],
    }
    assert parse_webhook_body(json.dumps(changes).encode(), allow_simplified=False)[0].comment_id == "c2"
