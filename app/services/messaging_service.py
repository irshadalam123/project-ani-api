"""Render reply templates and send them through the Instagram client."""

from app.automation.context import CommentContext
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.integrations.instagram.client import InstagramClient
from app.integrations.instagram.token_manager import TokenManager
from app.models.domain.execution import ActionResult, ActionResultStatus
from app.services.conversation_service import ConversationService
from app.utils.text import render_template

logger = get_logger(__name__)

_MAX_TEXT = 1000


class MessagingService:
    def __init__(
        self,
        client: InstagramClient,
        tokens: TokenManager,
        conversations: ConversationService,
    ) -> None:
        self._client = client
        self._tokens = tokens
        self._conversations = conversations

    async def execute_public_reply(self, ctx: CommentContext, text: str) -> ActionResult:
        rendered = render_template(text, ctx.variables)
        invalid = self._validate(rendered)
        if invalid is not None:
            return self._failed(ctx, "PUBLIC_REPLY", invalid, rendered)
        token = await self._tokens.get_token(ctx.instagram_account_id)
        if token is None:
            return self._failed(ctx, "PUBLIC_REPLY", "Instagram access token is missing", rendered)
        try:
            sent = await self._client.send_public_comment_reply(
                token.access_token,
                ctx.comment_id,
                rendered,
            )
        except AppException as exc:
            logger.warning(
                "public_reply_failed",
                workspace_id=ctx.workspace_id,
                instagram_account_id=ctx.instagram_account_id,
                automation_id=ctx.automation_id,
                execution_id=ctx.execution_id,
                error=exc.message,
            )
            if exc.transient:
                raise
            return self._failed(ctx, "PUBLIC_REPLY", exc.message, rendered)
        logger.info(
            "public_reply_sent",
            workspace_id=ctx.workspace_id,
            instagram_account_id=ctx.instagram_account_id,
            automation_id=ctx.automation_id,
            execution_id=ctx.execution_id,
        )
        return ActionResult(
            action_index=0,
            action_type="PUBLIC_REPLY",
            status=ActionResultStatus.SUCCESS,
            external_id=sent.message_id,
            rendered_text=rendered,
        )

    async def execute_private_reply(self, ctx: CommentContext, text: str) -> ActionResult:
        rendered = render_template(text, ctx.variables)
        invalid = self._validate(rendered)
        if invalid is not None:
            return self._failed(ctx, "PRIVATE_REPLY", invalid, rendered)
        token = await self._tokens.get_token(ctx.instagram_account_id)
        if token is None:
            return self._failed(ctx, "PRIVATE_REPLY", "Instagram access token is missing", rendered)
        try:
            sent = await self._client.send_private_reply(
                token.access_token,
                ctx.instagram_business_user_id,
                ctx.comment_id,
                rendered,
            )
        except AppException as exc:
            logger.warning(
                "private_reply_failed",
                workspace_id=ctx.workspace_id,
                instagram_account_id=ctx.instagram_account_id,
                automation_id=ctx.automation_id,
                execution_id=ctx.execution_id,
                error=exc.message,
            )
            if exc.transient:
                raise
            return self._failed(ctx, "PRIVATE_REPLY", exc.message, rendered)
        if ctx.contact_id is not None:
            await self._conversations.record_outbound(
                workspace_id=ctx.workspace_id,
                instagram_account_id=ctx.instagram_account_id,
                contact_id=ctx.contact_id,
                text=rendered,
                external_message_id=sent.message_id,
            )
        logger.info(
            "private_reply_sent",
            workspace_id=ctx.workspace_id,
            instagram_account_id=ctx.instagram_account_id,
            automation_id=ctx.automation_id,
            execution_id=ctx.execution_id,
        )
        return ActionResult(
            action_index=0,
            action_type="PRIVATE_REPLY",
            status=ActionResultStatus.SUCCESS,
            external_id=sent.message_id,
            rendered_text=rendered,
        )

    def _validate(self, rendered: str) -> str | None:
        if not rendered.strip():
            return "Message text is empty"
        if len(rendered) > _MAX_TEXT:
            return "Message text exceeds 1000 characters"
        return None

    def _failed(self, ctx: CommentContext, action_type: str, error: str, rendered: str) -> ActionResult:
        logger.warning(
            "message_rejected",
            workspace_id=ctx.workspace_id,
            automation_id=ctx.automation_id,
            execution_id=ctx.execution_id,
            action_type=action_type,
            error=error,
        )
        return ActionResult(
            action_index=0,
            action_type=action_type,
            status=ActionResultStatus.FAILED,
            error=error,
            rendered_text=rendered,
        )
