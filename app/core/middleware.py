"""Request ID and security headers.

These are raw ASGI middleware classes so FastAPI background tasks still run
after the response. BaseHTTPMiddleware is avoided for that reason.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

import structlog

_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")

_SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-xss-protection", b"0"),
    (b"cache-control", b"no-store"),
)


class RequestIdMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        incoming = headers.get("x-request-id", "")
        request_id = incoming if _REQUEST_ID.match(incoming) else str(uuid4())
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        workspace_id = headers.get("x-workspace-id")
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        if workspace_id:
            structlog.contextvars.bind_contextvars(workspace_id=workspace_id)

        async def send_with_id(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            structlog.contextvars.clear_contextvars()


class SecurityHeadersMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend(_SECURITY_HEADERS)
                message["headers"] = response_headers
            await send(message)

        await self.app(scope, receive, send_with_security)
