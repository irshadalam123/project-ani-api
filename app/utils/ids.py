"""Identifier helpers."""

from uuid import uuid4


def new_id() -> str:
    """Return a random identifier that is safe to store as a string primary key."""
    return str(uuid4())
