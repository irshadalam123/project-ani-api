"""Template rendering and retry policy."""

import pytest

from app.integrations.instagram.exceptions import InstagramPermanentError, InstagramTransientError
from app.utils.text import render_template
from app.workers.utils import backoff_seconds, is_transient, run_with_retry


def test_render_template_leaves_unknown_variables() -> None:
    rendered = render_template("Hey {{first_name}}, {{username}} {{missing}}", {"first_name": "Ava", "username": "ava"})
    assert rendered == "Hey Ava, ava {{missing}}"


def test_render_template_empty_known_value() -> None:
    assert render_template("Hey {{first_name}}", {"first_name": ""}) == "Hey "


def test_backoff_is_exponential_and_capped() -> None:
    assert backoff_seconds(1, base=1) == 1
    assert backoff_seconds(2, base=1) == 2
    assert backoff_seconds(3, base=1) == 4
    assert backoff_seconds(10, base=1, cap=8) == 8


def test_transient_classification() -> None:
    assert is_transient(InstagramTransientError("timeout"))
    assert not is_transient(InstagramPermanentError("bad request"))
    assert not is_transient(RuntimeError("boom"))


@pytest.mark.asyncio
async def test_retry_then_success_and_permanent_is_not_retried() -> None:
    calls = {"count": 0}

    async def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise InstagramTransientError("try again")
        return "ok"

    assert await run_with_retry(flaky, max_attempts=3, base_seconds=0) == "ok"
    assert calls["count"] == 3

    async def permanent() -> str:
        raise InstagramPermanentError("no")

    with pytest.raises(InstagramPermanentError):
        await run_with_retry(permanent, max_attempts=4, base_seconds=0)
