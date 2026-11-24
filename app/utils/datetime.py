"""Timezone-aware datetime helpers."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current time in UTC."""
    return datetime.now(UTC)
