"""Structured logging.

Access tokens, passwords, and secrets are stripped from log events.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping, MutableMapping
from typing import Any

import structlog

from app.core.config import Settings

_SENSITIVE_FRAGMENTS = ("token", "password", "secret", "authorization", "api_key", "credential")


def _redact_sensitive(
    _: Any,
    __: str,
    event_dict: MutableMapping[str, Any],
) -> Mapping[str, Any]:
    for key in list(event_dict):
        lowered = key.lower()
        if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS):
            event_dict[key] = "***"
    return event_dict


def configure_logging(settings: Settings) -> None:
    """Configure structlog and the standard library once per process."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level, force=True)
    # httpx can include request URLs at DEBUG. Keep it quiet so tokens in
    # query strings are not written if a future caller adds them.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    renderer: structlog.types.Processor
    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact_sensitive,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
