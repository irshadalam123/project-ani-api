"""User persistence port.

TODO(postgres): implement with a ``users`` table and a unique index on email.
"""

from abc import ABC, abstractmethod

from app.models.domain.user import User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...
