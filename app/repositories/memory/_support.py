"""Helpers shared by in-memory repositories."""

from __future__ import annotations

import asyncio
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def clone(model: T) -> T:
    return model.model_copy(deep=True)


class MemoryLock:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock
