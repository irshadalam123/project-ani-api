"""Demo seed data and OAuth URL construction."""

import pytest

from app.core.container import build_container
from app.integrations.instagram.auth import build_authorization_url
from scripts.seed_demo_data import seed
from tests.conftest import build_test_settings


def test_authorization_url_uses_configured_host() -> None:
    settings = build_test_settings(meta_app_id="12345")
    url = build_authorization_url(settings, "state-token")
    assert url.startswith("https://www.instagram.com/oauth/authorize?")
    assert "client_id=12345" in url
    assert "state=state-token" in url
    assert "instagram_business_manage_comments" in url


@pytest.mark.asyncio
async def test_seed_demo_data_is_idempotent() -> None:
    container = build_container(build_test_settings())
    first = await seed(container)
    second = await seed(container)
    assert first["automations"] == 2
    assert first["contacts"] == 3
    assert second["users"] == 1
    user = await container.users.get_by_email("demo@example.com")
    assert user is not None
    accounts = await container.instagram_accounts.list_by_workspace("00000000-0000-4000-8000-000000000010")
    assert accounts[0].username == "demo_brand"
    token = await container.tokens.get_token(accounts[0].id)
    assert token is not None
    assert "mock" in token.access_token
