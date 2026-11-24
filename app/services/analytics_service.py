"""Workspace analytics derived from stored events and executions."""

from dataclasses import dataclass

from app.models.domain.execution import ActionResultStatus, Execution
from app.models.domain.webhook_event import WebhookEventType
from app.repositories.interfaces.execution_repository import ExecutionRepository
from app.repositories.interfaces.webhook_repository import WebhookRepository


@dataclass(slots=True)
class AnalyticsOverview:
    comments_received: int
    comments_matched: int
    automations_triggered: int
    public_replies_sent: int
    private_replies_sent: int
    messages_sent: int
    failed_messages: int
    link_clicks: int
    leads: int


class AnalyticsService:
    def __init__(self, webhooks: WebhookRepository, executions: ExecutionRepository) -> None:
        self._webhooks = webhooks
        self._executions = executions

    async def overview(self, workspace_id: str) -> AnalyticsOverview:
        events = await self._webhooks.list_by_workspace(workspace_id)
        comments_received = sum(
            1 for event in events if event.event_type in {WebhookEventType.COMMENT, WebhookEventType.LIVE_COMMENT}
        )
        executions = await self._all_executions(workspace_id)
        matched_comments = {item.comment_id for item in executions}
        public_sent = 0
        private_sent = 0
        failed = 0
        for execution in executions:
            for result in execution.action_results:
                if result.status == ActionResultStatus.SUCCESS and result.action_type == "PUBLIC_REPLY":
                    public_sent += 1
                elif result.status == ActionResultStatus.SUCCESS and result.action_type == "PRIVATE_REPLY":
                    private_sent += 1
                elif result.status == ActionResultStatus.FAILED:
                    failed += 1
        return AnalyticsOverview(
            comments_received=comments_received,
            comments_matched=len(matched_comments),
            automations_triggered=len(executions),
            public_replies_sent=public_sent,
            private_replies_sent=private_sent,
            messages_sent=public_sent + private_sent,
            failed_messages=failed,
            link_clicks=0,
            leads=0,
        )

    async def _all_executions(self, workspace_id: str) -> list[Execution]:
        page = 1
        collected = []
        while True:
            items, total = await self._executions.list_by_workspace(
                workspace_id,
                page=page,
                page_size=100,
            )
            collected.extend(items)
            if page * 100 >= total or not items:
                return collected
            page += 1
