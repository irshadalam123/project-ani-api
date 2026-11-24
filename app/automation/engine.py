"""Match a comment to active automations and run their actions once."""

from __future__ import annotations

from app.automation.actions import ActionExecutor
from app.automation.context import CommentContext
from app.automation.matcher import CommentMatcher
from app.models.domain.automation import (
    Action,
    Automation,
    AutomationStatus,
    PrivateReplyAction,
    PublicReplyAction,
)
from app.models.domain.execution import ActionResult, ActionResultStatus, Execution


class AutomationEngine:
    def __init__(self, matcher: CommentMatcher | None = None) -> None:
        self._matcher = matcher or CommentMatcher()

    def select(self, text: str, automations: list[Automation]) -> list[Automation]:
        selected: list[Automation] = []
        for automation in automations:
            if automation.status != AutomationStatus.ACTIVE:
                continue
            if self._matcher.matches(text, automation.trigger):
                selected.append(automation)
        return selected

    def matches(self, text: str, automation: Automation) -> bool:
        if automation.status != AutomationStatus.ACTIVE:
            return False
        return self._matcher.matches(text, automation.trigger)

    async def run_action(
        self,
        action: Action,
        ctx: CommentContext,
        executor: ActionExecutor,
        *,
        action_index: int,
        already_done: ActionResult | None = None,
    ) -> ActionResult:
        if already_done is not None and already_done.status == ActionResultStatus.SUCCESS:
            return already_done
        if isinstance(action, PublicReplyAction):
            result = await executor.execute_public_reply(ctx, action.text)
        elif isinstance(action, PrivateReplyAction):
            result = await executor.execute_private_reply(ctx, action.text)
        else:
            result = ActionResult(
                action_index=action_index,
                action_type=getattr(action, "type", "UNKNOWN"),
                status=ActionResultStatus.SKIPPED,
                error="Unsupported action",
            )
        result.action_index = action_index
        return result

    def should_skip_execution(self, existing: Execution | None) -> bool:
        """A successful run for this comment and automation is not repeated."""
        if existing is None:
            return False
        if existing.status.value == "SUCCEEDED":
            return True
        return all(item.status == ActionResultStatus.SUCCESS for item in existing.action_results) and bool(
            existing.action_results
        )
