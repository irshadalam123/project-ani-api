"""Authentication, authorization, and error envelopes."""

from fastapi.testclient import TestClient

from app.core.redis import FakeRedisService
from tests.conftest import auth_headers, build_test_settings
from app.main import create_app


def test_register_login_and_me(client: TestClient) -> None:
    headers = auth_headers(client)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "owner@example.com"
    assert "password" not in me.json()["data"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "a-strong-password"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["access_token"]

    duplicate = client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "password": "a-strong-password", "full_name": "Avery Owner"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    bad = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "wrong-password"})
    assert bad.status_code == 401
    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401
    assert missing.json()["success"] is False
    assert missing.headers["x-request-id"]


def test_workspace_isolation(client: TestClient) -> None:
    first = auth_headers(client, "one@example.com")
    second = auth_headers(client, "two@example.com")
    created = client.post(
        "/api/v1/workspaces",
        headers=first,
        json={"name": "Private Studio"},
    )
    assert created.status_code == 201
    private_id = created.json()["data"]["id"]
    denied = client.get("/api/v1/automations", headers={**second, "X-Workspace-Id": private_id})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "WORKSPACE_FORBIDDEN"


def test_validation_and_not_found_envelopes(client: TestClient) -> None:
    headers = auth_headers(client)
    invalid = client.post("/api/v1/auth/register", json={"email": "not-an-email"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    missing = client.get("/api/v1/automations/does-not-exist", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "AUTOMATION_NOT_FOUND"


def test_health_and_readiness(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"]["redis"] == "ok"

    application = create_app(build_test_settings())
    application.state.container.redis = FakeRedisService(healthy=False)
    with TestClient(application) as broken:
        down = broken.get("/health/ready")
    assert down.status_code == 503
    assert down.json()["checks"]["redis"] == "unavailable"
