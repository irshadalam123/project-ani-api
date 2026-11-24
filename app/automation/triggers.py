"""Trigger types the engine understands today.

Later triggers (AI intent, story replies, and so on) should be added here
without changing the HTTP layer.
"""

from app.models.domain.automation import TriggerType

SUPPORTED_TRIGGERS = {TriggerType.COMMENT_KEYWORD, TriggerType.ANY_COMMENT}
