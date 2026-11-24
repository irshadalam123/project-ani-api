"""Webhook HTTP verification."""

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import build_test_settings


def test_webhook_verification_challenge(client: TestClient) -> None:
    response = client.get(
        "/webhooks/instagram",
        params={"hub.mode": "subscribe", "hub.verify_token": "test-verify-token", "hub.challenge": "999"},
    )
    assert response.status_code == 200
    assert response.text == "999"
    rejected = client.get(
        "/webhooks/instagram",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "999"},
    )
    assert rejected.status_code == 403
    assert rejected.json()["error"]["code"] == "WEBHOOK_VERIFICATION_FAILED"


def test_signed_official_webhook_is_idempotent() -> None:
    secret = "meta-app-secret"
    application = create_app(build_test_settings(meta_app_secret=secret))
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig_business",
                "time": 1,
                "field": "comments",
                "value": {
                    "id": "comment_999",
                    "text": "hello",
                    "from": {"id": "user_1", "username": "ada"},
                    "media": {"id": "media_1"},
                },
            }
        ],
    }
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    with TestClient(application) as client:
        accepted = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"content-type": "application/json", "x-hub-signature-256": signature},
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["data"]["event_ids"]
        replay = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"content-type": "application/json", "x-hub-signature-256": signature},
        )
        assert replay.json()["data"]["duplicate_event_ids"]
        bad = client.post(
            "/webhooks/instagram",
            content=body,
            headers={"content-type": "application/json", "x-hub-signature-256": "sha256=nope"},
        )
        assert bad.status_code == 403
