"""Shared API test client."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def build_test_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "test",
        "debug": True,
        "database_url": "",
        "secret_key": "test-secret-key",
        "jwt_secret": "test-jwt-secret-with-32-characters-min",
        "mock_external_services": True,
        "rate_limit_enabled": False,
        "task_execution_mode": "inline",
        "meta_webhook_verify_token": "test-verify-token",
        "meta_app_id": "mock-app-id",
        "meta_app_secret": "",
        "meta_api_version": "v21.0",
        "cors_origins": "http://localhost:5173",
        "trusted_hosts": "localhost,127.0.0.1,testserver",
        "seed_demo_data": False,
        "retry_base_seconds": 0,
        "retry_max_attempts": 3,
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.fixture
def client() -> Iterator[TestClient]:
    application = create_app(build_test_settings())
    with TestClient(application) as test_client:
        yield test_client


def auth_headers(client: TestClient, email: str = "owner@example.com") -> dict[str, str]:
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "a-strong-password",
            "full_name": "Avery Owner",
            "workspace_name": "Avery Studio",
        },
    )
    assert registered.status_code == 200, registered.text
    body = registered.json()
    return {
        "Authorization": f"Bearer {body['data']['access_token']}",
        "X-Workspace-Id": body["data"]["workspace"]["id"],
    }
