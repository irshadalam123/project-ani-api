"""Short-lived OAuth state.

State is stored server-side so the callback can be tied to a user and workspace.
A later Redis implementation can replace this class without changing the service.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.utils.datetime import utcnow
from app.utils.ids import new_id


@dataclass(slots=True)
class OAuthState:
    state: str
    user_id: str
    workspace_id: str
    expires_at: datetime


class OAuthStateStore(ABC):
    @abstractmethod
    async def issue(self, user_id: str, workspace_id: str) -> str: ...

    @abstractmethod
    async def consume(self, state: str) -> OAuthState | None: ...


class InMemoryOAuthStateStore(OAuthStateStore):
    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl = ttl_seconds
        self._items: dict[str, tuple[str, str, datetime]] = {}

    async def issue(self, user_id: str, workspace_id: str) -> str:
        state = new_id()
        self._items[state] = (user_id, workspace_id, utcnow() + timedelta(seconds=self._ttl))
        return state

    async def consume(self, state: str) -> OAuthState | None:
        item = self._items.pop(state, None)
        if item is None:
            return None
        user_id, workspace_id, expires_at = item
        if expires_at < utcnow():
            return None
        return OAuthState(state=state, user_id=user_id, workspace_id=workspace_id, expires_at=expires_at)
