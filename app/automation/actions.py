"""Action execution boundary used by the engine.

``PUBLIC_REPLY`` and ``PRIVATE_REPLY`` are implemented. Future actions
(buttons, email collection, AI reply, wait, tag) should be added as new
action models plus a branch in the messaging service.
"""

from typing import Protocol

from app.automation.context import CommentContext
from app.models.domain.execution import ActionResult


class ActionExecutor(Protocol):
    async def execute_public_reply(self, ctx: CommentContext, text: str) -> ActionResult: ...

    async def execute_private_reply(self, ctx: CommentContext, text: str) -> ActionResult: ...
