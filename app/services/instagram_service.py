"""Connect and disconnect Instagram professional accounts.

Meta HTTP details stay in the Instagram client. This service stores account
metadata and hands the token to TokenManager.
"""

from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.integrations.instagram.client import InstagramClient
from app.integrations.instagram.exceptions import InstagramPermanentError
from app.integrations.instagram.oauth_state import OAuthStateStore
from app.integrations.instagram.token_manager import TokenManager
from app.integrations.instagram.types import StoredToken
from app.models.domain.instagram_account import InstagramAccount
from app.repositories.interfaces.instagram_repository import InstagramRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id

logger = get_logger(__name__)


@dataclass(slots=True)
class ConnectLink:
    authorization_url: str
    state: str


class InstagramService:
    def __init__(
        self,
        accounts: InstagramRepository,
        client: InstagramClient,
        tokens: TokenManager,
        states: OAuthStateStore,
        settings: Settings,
    ) -> None:
        self._accounts = accounts
        self._client = client
        self._tokens = tokens
        self._states = states
        self._settings = settings

    async def connect_link(self, user_id: str, workspace_id: str) -> ConnectLink:
        state = await self._states.issue(user_id, workspace_id)
        url = await self._client.get_authorization_url(state)
        return ConnectLink(authorization_url=url, state=state)

    async def handle_callback(self, code: str | None, state: str | None, error: str | None) -> InstagramAccount:
        if error:
            raise ValidationException(f"Instagram authorization was denied: {error}", code="INSTAGRAM_OAUTH_DENIED")
        if not code or not state:
            raise ValidationException("Instagram callback is missing code or state", code="INSTAGRAM_OAUTH_INVALID")
        saved = await self._states.consume(state)
        if saved is None:
            raise ValidationException("Instagram OAuth state is invalid or expired", code="INSTAGRAM_OAUTH_STATE")
        short = await self._client.exchange_code_for_token(code)
        long_lived = await self._client.exchange_long_lived_token(short.access_token)
        profile = await self._client.get_account(long_lived.access_token)
        instagram_user_id = profile.instagram_user_id
        if self._settings.mock_external_services:
            instagram_user_id = f"{profile.instagram_user_id}-{saved.workspace_id}"
        existing = await self._accounts.get_by_instagram_user_id(instagram_user_id)
        now = utcnow()
        if existing is not None and existing.workspace_id != saved.workspace_id:
            raise ConflictException(
                "This Instagram account is already connected to another workspace",
                code="INSTAGRAM_ACCOUNT_CONFLICT",
            )
        if existing is None:
            account = InstagramAccount(
                id=new_id(),
                workspace_id=saved.workspace_id,
                instagram_user_id=instagram_user_id,
                username=profile.username,
                name=profile.name,
                account_type=profile.account_type,
                profile_picture_url=profile.profile_picture_url,
                webhook_subscribed=False,
                scopes=short.permissions,
                connected_at=now,
                created_at=now,
                updated_at=now,
            )
            await self._accounts.add(account)
        else:
            existing.username = profile.username
            existing.name = profile.name
            existing.account_type = profile.account_type
            existing.profile_picture_url = profile.profile_picture_url
            existing.scopes = short.permissions
            existing.updated_at = now
            account = await self._accounts.update(existing)
        await self._tokens.store_token(
            account.id,
            StoredToken(
                access_token=long_lived.access_token,
                expires_in=long_lived.expires_in,
                scopes=short.permissions,
            ),
        )
        try:
            await self._client.subscribe_webhooks(long_lived.access_token, instagram_user_id)
            account.webhook_subscribed = True
            account.updated_at = utcnow()
            account = await self._accounts.update(account)
        except InstagramPermanentError as exc:
            logger.warning("instagram_webhook_subscribe_failed", instagram_account_id=account.id, error=exc.message)
        logger.info(
            "instagram_account_connected",
            workspace_id=account.workspace_id,
            instagram_account_id=account.id,
            user_id=saved.user_id,
        )
        return account

    async def list_accounts(self, workspace_id: str) -> list[InstagramAccount]:
        return await self._accounts.list_by_workspace(workspace_id)

    async def disconnect(self, workspace_id: str, account_id: str) -> None:
        account = await self._require(workspace_id, account_id)
        await self._tokens.delete_token(account.id)
        deleted = await self._accounts.delete(workspace_id, account.id)
        if not deleted:
            raise NotFoundException("Instagram account not found", code="INSTAGRAM_ACCOUNT_NOT_FOUND")

    async def get_account(self, workspace_id: str, account_id: str) -> InstagramAccount:
        return await self._require(workspace_id, account_id)

    async def _require(self, workspace_id: str, account_id: str) -> InstagramAccount:
        account = await self._accounts.get_by_id(account_id)
        if account is None or account.workspace_id != workspace_id:
            raise NotFoundException("Instagram account not found", code="INSTAGRAM_ACCOUNT_NOT_FOUND")
        return account
