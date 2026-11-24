"""Process a stored comment event through the automation engine."""

from __future__ import annotations

from app.automation.context import CommentContext
from app.automation.engine import AutomationEngine
from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.integrations.instagram.types import NormalizedComment
from app.models.domain.automation import Action, Automation
from app.models.domain.execution import (
    ActionResult,
    ActionResultStatus,
    Execution,
    ExecutionStatus,
)
from app.models.domain.contact import Contact
from app.models.domain.instagram_account import InstagramAccount
from app.models.domain.webhook_event import WebhookEvent, WebhookEventStatus, WebhookEventType
from app.repositories.interfaces.automation_repository import AutomationRepository
from app.repositories.interfaces.execution_repository import ExecutionRepository
from app.repositories.interfaces.instagram_repository import InstagramRepository
from app.repositories.interfaces.webhook_repository import WebhookRepository
from app.services.contact_service import ContactService
from app.services.messaging_service import MessagingService
from app.utils.datetime import utcnow
from app.utils.ids import new_id
from app.workers.utils import is_transient, record_dead_letter, run_with_retry

logger = get_logger(__name__)


class CommentService:
    def __init__(
        self,
        webhooks: WebhookRepository,
        accounts: InstagramRepository,
        automations: AutomationRepository,
        executions: ExecutionRepository,
        contacts: ContactService,
        messaging: MessagingService,
        engine: AutomationEngine,
        settings: Settings,
    ) -> None:
        self._webhooks = webhooks
        self._accounts = accounts
        self._automations = automations
        self._executions = executions
        self._contacts = contacts
        self._messaging = messaging
        self._engine = engine
        self._settings = settings

    async def process_webhook_event(self, event_id: str) -> None:
        event = await self._webhooks.get_by_id(event_id)
        if event is None or event.status in {WebhookEventStatus.PROCESSED, WebhookEventStatus.IGNORED}:
            return
        event.status = WebhookEventStatus.PROCESSING
        event.attempt_count += 1
        await self._webhooks.update(event)
        try:
            if event.event_type not in {WebhookEventType.COMMENT, WebhookEventType.LIVE_COMMENT}:
                await self._ignore(event, "unsupported_event")
                return
            await self.process_comment(event.id)
        except Exception as exc:
            current = await self._webhooks.get_by_id(event_id)
            if current is not None and current.status != WebhookEventStatus.PROCESSED:
                current.status = WebhookEventStatus.FAILED
                current.error = str(exc)[:500]
                await self._webhooks.update(current)
            record_dead_letter(
                "process_webhook_event",
                {"event_id": event_id},
                str(exc),
                redis_url=self._settings.redis_url,
            )
            if is_transient(exc):
                raise

    async def process_comment(self, event_id: str) -> None:
        event = await self._webhooks.get_by_id(event_id)
        if event is None:
            return
        comment_payload = event.payload.get("comment")
        if not isinstance(comment_payload, dict):
            await self._ignore(event, "missing_comment_payload")
            return
        comment = NormalizedComment.model_validate(comment_payload)
        account = await self._resolve_account(comment)
        if account is None:
            await self._ignore(event, "instagram_account_not_found")
            return
        event.workspace_id = account.workspace_id
        event.instagram_account_id = account.id
        await self._webhooks.update(event)
        if comment.parent_id:
            await self._ignore(event, "comment_reply")
            return
        if comment.commenter_id and comment.commenter_id == account.instagram_user_id:
            await self._ignore(event, "self_comment")
            return
        contact = await self._contacts.upsert_from_comment(
            workspace_id=account.workspace_id,
            instagram_account_id=account.id,
            instagram_user_id=comment.commenter_id,
            username=comment.commenter_username,
        )
        active = await self._automations.list_active_for_account(account.workspace_id, account.id)
        matched = self._engine.select(comment.text, active)
        logger.info(
            "comment_matched",
            workspace_id=account.workspace_id,
            instagram_account_id=account.id,
            matched=len(matched),
        )
        for automation in matched:
            await self._execute_automation(event, account, comment, automation, contact)
        event = await self._webhooks.get_by_id(event_id)
        if event is None:
            return
        event.status = WebhookEventStatus.PROCESSED
        event.processed_at = utcnow()
        event.error = None
        await self._webhooks.update(event)

    async def deliver_action(self, execution_id: str, action_index: int) -> None:
        execution = await self._executions.get_by_id(execution_id)
        if execution is None:
            return
        existing = next((item for item in execution.action_results if item.action_index == action_index), None)
        if existing is not None and existing.status == ActionResultStatus.SUCCESS:
            return
        automation = await self._automations.get_by_id(execution.automation_id)
        account = await self._accounts.get_by_id(execution.instagram_account_id)
        event = await self._webhooks.get_by_id(execution.webhook_event_id)
        if automation is None or account is None or event is None:
            return
        if action_index >= len(automation.actions):
            return
        comment_payload = event.payload.get("comment")
        if not isinstance(comment_payload, dict):
            return
        comment = NormalizedComment.model_validate(comment_payload)
        ctx = self._context(execution, account, comment, automation, contact=None)
        action = automation.actions[action_index]
        result = await self._run_action(action_index, ctx, action)
        await self._executions.save_action_result(execution.id, result)

    async def _execute_automation(
        self,
        event: WebhookEvent,
        account: InstagramAccount,
        comment: NormalizedComment,
        automation: Automation,
        contact: Contact,
    ) -> None:
        now = utcnow()
        planned = [
            ActionResult(action_index=index, action_type=str(action.type), status=ActionResultStatus.PENDING)
            for index, action in enumerate(automation.actions)
        ]
        draft = Execution(
            id=new_id(),
            workspace_id=account.workspace_id,
            instagram_account_id=account.id,
            automation_id=automation.id,
            webhook_event_id=event.id,
            comment_id=comment.comment_id,
            status=ExecutionStatus.RUNNING,
            action_results=planned,
            created_at=now,
            updated_at=now,
        )
        execution, created = await self._executions.create_if_absent(draft)
        if not created and self._engine.should_skip_execution(execution):
            logger.info(
                "duplicate_execution_skipped",
                workspace_id=account.workspace_id,
                automation_id=automation.id,
                execution_id=execution.id,
            )
            return
        ctx = self._context(execution, account, comment, automation, contact=contact)
        for index, action in enumerate(automation.actions):
            previous = next((item for item in execution.action_results if item.action_index == index), None)
            if previous is not None and previous.status == ActionResultStatus.SUCCESS:
                continue
            result = await self._run_action(index, ctx, action)
            execution = await self._executions.save_action_result(execution.id, result)

    async def _run_action(self, index: int, ctx: CommentContext, action: Action) -> ActionResult:
        async def _call() -> ActionResult:
            return await self._engine.run_action(action, ctx, self._messaging, action_index=index)

        try:
            result = await run_with_retry(
                _call,
                max_attempts=self._settings.retry_max_attempts,
                base_seconds=self._settings.retry_base_seconds,
            )
        except AppException as exc:
            return ActionResult(
                action_index=index,
                action_type=str(getattr(action, "type", "UNKNOWN")),
                status=ActionResultStatus.FAILED,
                error=exc.message,
            )
        if not isinstance(result, ActionResult):
            raise RuntimeError("Action did not return a result")
        result.action_index = index
        return result

    def _context(
        self,
        execution: Execution,
        account: InstagramAccount,
        comment: NormalizedComment,
        automation: Automation,
        *,
        contact: Contact | None,
    ) -> CommentContext:
        username = (contact.username if contact and contact.username else comment.commenter_username) or ""
        first_name = contact.first_name if contact and contact.first_name else ""
        return CommentContext(
            workspace_id=account.workspace_id,
            instagram_account_id=account.id,
            instagram_business_user_id=account.instagram_user_id,
            comment_id=comment.comment_id,
            media_id=comment.media_id,
            comment_text=comment.text,
            commenter_id=comment.commenter_id,
            commenter_username=comment.commenter_username,
            contact_id=contact.id if contact else None,
            execution_id=execution.id,
            automation_id=automation.id,
            webhook_event_id=execution.webhook_event_id,
            variables={"first_name": first_name, "username": username},
        )

    async def _resolve_account(self, comment: NormalizedComment) -> InstagramAccount | None:
        if comment.business_account_id:
            found = await self._accounts.get_by_instagram_user_id(comment.business_account_id)
            if found is not None:
                return found
        accounts = await self._accounts.list_all()
        if len(accounts) == 1:
            return accounts[0]
        return None

    async def _ignore(self, event: WebhookEvent, reason: str) -> None:
        event.status = WebhookEventStatus.IGNORED
        event.error = reason
        event.processed_at = utcnow()
        await self._webhooks.update(event)
        logger.info(
            "webhook_ignored",
            workspace_id=event.workspace_id,
            instagram_account_id=event.instagram_account_id,
            reason=reason,
        )
