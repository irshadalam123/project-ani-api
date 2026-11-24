"""Automation API behavior."""

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def connect_mock_account(client: TestClient, headers: dict[str, str]) -> str:
    connect = client.get("/api/v1/instagram/connect", headers=headers)
    assert connect.status_code == 200, connect.text
    state = parse_qs(urlparse(connect.json()["data"]["authorization_url"]).query)["state"][0]
    callback = client.get("/api/v1/instagram/callback", params={"code": "mock_code", "state": state})
    assert callback.status_code == 200, callback.text
    account = callback.json()["data"]
    assert "access_token" not in account
    assert account["webhook_subscribed"] is True
    return str(account["id"])


def test_create_activate_pause_and_reject_other_workspace(client: TestClient) -> None:
    headers = auth_headers(client)
    account_id = connect_mock_account(client, headers)
    created = client.post(
        "/api/v1/automations",
        headers=headers,
        json={
            "name": "AI Roadmap",
            "instagram_account_id": account_id,
            "trigger": {"type": "COMMENT_KEYWORD", "keywords": ["guide"], "match_type": "CONTAINS"},
            "actions": [
                {"type": "PUBLIC_REPLY", "text": "Check your DM"},
                {"type": "PRIVATE_REPLY", "text": "Here is your guide!"},
            ],
        },
    )
    assert created.status_code == 201, created.text
    automation_id = created.json()["data"]["id"]
    assert created.json()["data"]["status"] == "DRAFT"

    listed = client.get("/api/v1/automations", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["pagination"]["total"] == 1

    active = client.post(f"/api/v1/automations/{automation_id}/activate", headers=headers)
    assert active.json()["data"]["status"] == "ACTIVE"
    paused = client.post(f"/api/v1/automations/{automation_id}/pause", headers=headers)
    assert paused.json()["data"]["status"] == "PAUSED"
    cannot_pause = client.post(f"/api/v1/automations/{automation_id}/pause", headers=headers)
    assert cannot_pause.status_code == 409

    other = auth_headers(client, "other@example.com")
    hidden = client.get(f"/api/v1/automations/{automation_id}", headers=other)
    assert hidden.status_code == 404
