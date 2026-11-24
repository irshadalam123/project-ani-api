"""Engine selection and duplicate-execution guard."""

import pytest

from app.automation.context import CommentContext
from app.automation.engine import AutomationEngine
from app.models.domain.automation import (
    Automation,
    AutomationStatus,
    KeywordTrigger,
    MatchType,
    PrivateReplyAction,
    PublicReplyAction,
)
from app.models.domain.execution import ActionResult, ActionResultStatus, Execution, ExecutionStatus
from app.utils.datetime import utcnow


class RecordingExecutor:
    def __init__(self) -> None:
        self.public: list[str] = []
        self.private: list[str] = []

    async def execute_public_reply(self, ctx: CommentContext, text: str) -> ActionResult:
        self.public.append(text)
        return ActionResult(action_index=0, action_type="PUBLIC_REPLY", status=ActionResultStatus.SUCCESS, external_id="pub")

    async def execute_private_reply(self, ctx: CommentContext, text: str) -> ActionResult:
        self.private.append(text)
        return ActionResult(action_index=1, action_type="PRIVATE_REPLY", status=ActionResultStatus.SUCCESS, external_id="priv")


def _automation() -> Automation:
    now = utcnow()
    return Automation(
        id="auto",
        workspace_id="ws",
        instagram_account_id="ig",
        name="Guide",
        status=AutomationStatus.ACTIVE,
        trigger=KeywordTrigger(keywords=["GUIDE"], match_type=MatchType.CONTAINS),
        actions=[
            PublicReplyAction(text="Check your DM"),
            PrivateReplyAction(text="Here is your guide, {{username}}!"),
        ],
        created_at=now,
        updated_at=now,
    )


def test_selects_only_active_matching_automations() -> None:
    engine = AutomationEngine()
    paused = _automation()
    paused.status = AutomationStatus.PAUSED
    paused.id = "paused"
    assert engine.select("please send GUIDE", [_automation(), paused])[0].id == "auto"
    assert engine.select("guidance", [_automation()]) == []


@pytest.mark.asyncio
async def test_run_action_skips_a_successful_result() -> None:
    engine = AutomationEngine()
    executor = RecordingExecutor()
    now = utcnow()
    ctx = CommentContext(
        workspace_id="ws",
        instagram_account_id="ig",
        instagram_business_user_id="biz",
        comment_id="c1",
        media_id=None,
        comment_text="GUIDE",
        commenter_id="u",
        commenter_username="ada",
        contact_id=None,
        execution_id="ex",
        automation_id="auto",
        webhook_event_id="ev",
        variables={"username": "ada", "first_name": ""},
    )
    action = _automation().actions[0]
    done = ActionResult(action_index=0, action_type="PUBLIC_REPLY", status=ActionResultStatus.SUCCESS, external_id="kept")
    result = await engine.run_action(action, ctx, executor, action_index=0, already_done=done)
    assert result.external_id == "kept"
    assert executor.public == []
    existing = Execution(
        id="ex",
        workspace_id="ws",
        instagram_account_id="ig",
        automation_id="auto",
        webhook_event_id="ev",
        comment_id="c1",
        status=ExecutionStatus.SUCCEEDED,
        action_results=[done],
        created_at=now,
        updated_at=now,
    )
    assert engine.should_skip_execution(existing) is True
