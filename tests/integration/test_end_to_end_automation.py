"""Full mock comment-to-DM flow, including a duplicate webhook."""

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.integrations.instagram.client import MockInstagramClient
from app.models.domain.webhook_event import WebhookEventStatus
from tests.conftest import auth_headers


class CountingClient(MockInstagramClient):
    def __init__(self, settings: object) -> None:
        super().__init__(settings)  # type: ignore[arg-type]
        self.public_calls = 0
        self.private_calls = 0

    async def send_public_comment_reply(self, access_token: str, comment_id: str, text: str):  # type: ignore[no-untyped-def]
        self.public_calls += 1
        return await super().send_public_comment_reply(access_token, comment_id, text)

    async def send_private_reply(self, access_token: str, instagram_user_id: str, comment_id: str, text: str):  # type: ignore[no-untyped-def]
        self.private_calls += 1
        return await super().send_private_reply(access_token, instagram_user_id, comment_id, text)


def test_comment_webhook_runs_public_and_private_replies_once(client: TestClient) -> None:
    counter = CountingClient(client.app.state.settings)
    client.app.state.container.instagram = counter

    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "password": "a-strong-password",
            "full_name": "Flow Owner",
        },
    )
    token = registered.json()["data"]["access_token"]
    workspace = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Flow Studio"},
    )
    assert workspace.status_code == 201
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Workspace-Id": workspace.json()["data"]["id"],
    }
    connect = client.get("/api/v1/instagram/connect", headers=headers)
    state = parse_qs(urlparse(connect.json()["data"]["authorization_url"]).query)["state"][0]
    account = client.get("/api/v1/instagram/callback", params={"code": "mock_code", "state": state})
    account_id = account.json()["data"]["id"]

    created = client.post(
        "/api/v1/automations",
        headers=headers,
        json={
            "name": "Guide",
            "instagram_account_id": account_id,
            "trigger": {"type": "COMMENT_KEYWORD", "keywords": ["GUIDE"], "match_type": "CONTAINS"},
            "actions": [
                {"type": "PUBLIC_REPLY", "text": "Check your DM 🚀"},
                {"type": "PRIVATE_REPLY", "text": "Here is your guide!"},
            ],
        },
    )
    automation_id = created.json()["data"]["id"]
    activated = client.post(f"/api/v1/automations/{automation_id}/activate", headers=headers)
    assert activated.json()["data"]["status"] == "ACTIVE"

    payload = {
        "comment_id": "comment_123",
        "media_id": "media_123",
        "instagram_user_id": "user_456",
        "username": "testuser",
        "text": "GUIDE",
    }
    first = client.post("/webhooks/instagram", json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["data"]["accepted"] is True
    assert len(first.json()["data"]["event_ids"]) == 1

    executions = client.get("/api/v1/executions", headers=headers)
    assert executions.status_code == 200, executions.text
    body = executions.json()
    assert body["pagination"]["total"] == 1
    execution = body["data"][0]
    assert execution["status"] == "SUCCEEDED"
    assert execution["comment_id"] == "comment_123"
    assert execution["automation_id"] == automation_id
    assert [item["action_type"] for item in execution["action_results"]] == ["PUBLIC_REPLY", "PRIVATE_REPLY"]
    assert all(item["status"] == "SUCCESS" for item in execution["action_results"])
    assert execution["action_results"][0]["external_id"] == "mock_reply_comment_123"
    assert execution["action_results"][1]["external_id"] == "mock_message_comment_123"
    assert execution["action_results"][0]["rendered_text"] == "Check your DM 🚀"
    assert execution["action_results"][1]["rendered_text"] == "Here is your guide!"

    contacts = client.get("/api/v1/contacts", headers=headers)
    assert contacts.json()["pagination"]["total"] == 1
    assert contacts.json()["data"][0]["username"] == "testuser"

    conversations = client.get("/api/v1/conversations", headers=headers)
    assert conversations.json()["pagination"]["total"] == 1
    conversation_id = conversations.json()["data"][0]["id"]
    messages = client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=headers)
    assert messages.json()["data"][0]["text"] == "Here is your guide!"
    assert messages.json()["data"][0]["direction"] == "OUTBOUND"

    overview = client.get("/api/v1/analytics/overview", headers=headers)
    assert overview.json()["data"]["comments_received"] == 1
    assert overview.json()["data"]["comments_matched"] == 1
    assert overview.json()["data"]["automations_triggered"] == 1
    assert overview.json()["data"]["public_replies_sent"] == 1
    assert overview.json()["data"]["private_replies_sent"] == 1
    assert overview.json()["data"]["messages_sent"] == 2
    assert overview.json()["data"]["failed_messages"] == 0

    duplicate = client.post("/webhooks/instagram", json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["data"]["event_ids"] == []
    assert duplicate.json()["data"]["duplicate_event_ids"]
    again = client.get("/api/v1/executions", headers=headers)
    assert again.json()["pagination"]["total"] == 1
    assert counter.public_calls == 1
    assert counter.private_calls == 1

    import asyncio

    event_id = first.json()["data"]["event_ids"][0]
    event = asyncio.run(client.app.state.container.webhooks.get_by_id(event_id))
    assert event is not None
    event.status = WebhookEventStatus.RECEIVED
    asyncio.run(client.app.state.container.webhooks.update(event))
    asyncio.run(client.app.state.container.comment_service().process_webhook_event(event_id))
    assert counter.public_calls == 1
    assert counter.private_calls == 1
