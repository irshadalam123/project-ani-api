"""Token storage abstraction.

``InMemoryTokenManager`` keeps tokens in the API process. Replace it later
with an encrypted PostgreSQL implementation. Tokens are never logged.
"""

from abc import ABC, abstractmethod

from app.integrations.instagram.types import StoredToken


class TokenManager(ABC):
    @abstractmethod
    async def store_token(self, account_id: str, token: StoredToken) -> None: ...

    @abstractmethod
    async def get_token(self, account_id: str) -> StoredToken | None: ...

    @abstractmethod
    async def delete_token(self, account_id: str) -> None: ...


class InMemoryTokenManager(TokenManager):
    def __init__(self) -> None:
        self._tokens: dict[str, StoredToken] = {}

    async def store_token(self, account_id: str, token: StoredToken) -> None:
        self._tokens[account_id] = token.model_copy(deep=True)

    async def get_token(self, account_id: str) -> StoredToken | None:
        found = self._tokens.get(account_id)
        return found.model_copy(deep=True) if found else None

    async def delete_token(self, account_id: str) -> None:
        self._tokens.pop(account_id, None)


class EncryptedPostgreSQLTokenManager(TokenManager):
    """Placeholder for the future encrypted token store.

    TODO(postgres): persist tokens in a dedicated table encrypted with an
    application key that is not the access token. Do not add the raw token to
    the instagram_accounts table or to logs.
    """

    async def store_token(self, account_id: str, token: StoredToken) -> None:
        raise NotImplementedError("PostgreSQL token storage is not enabled")

    async def get_token(self, account_id: str) -> StoredToken | None:
        raise NotImplementedError("PostgreSQL token storage is not enabled")

    async def delete_token(self, account_id: str) -> None:
        raise NotImplementedError("PostgreSQL token storage is not enabled")
