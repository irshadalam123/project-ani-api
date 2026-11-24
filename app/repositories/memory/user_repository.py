"""In-memory user repository."""

from app.models.domain.user import User
from app.repositories.exceptions import DuplicateRecordError
from app.repositories.interfaces.user_repository import UserRepository
from app.repositories.memory._support import clone


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._items: dict[str, User] = {}

    async def add(self, user: User) -> User:
        if any(item.email.casefold() == user.email.casefold() for item in self._items.values()):
            raise DuplicateRecordError("email")
        self._items[user.id] = clone(user)
        return clone(user)

    async def get_by_id(self, user_id: str) -> User | None:
        found = self._items.get(user_id)
        return clone(found) if found else None

    async def get_by_email(self, email: str) -> User | None:
        for item in self._items.values():
            if item.email.casefold() == email.casefold():
                return clone(item)
        return None

    async def update(self, user: User) -> User:
        self._items[user.id] = clone(user)
        return clone(user)
