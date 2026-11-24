"""LLM request and response values.

AI replies are not part of the first automation actions. This module exists so
a later ``AI_REPLY`` action can call a provider without touching the engine.
"""

from pydantic import BaseModel


class LLMCompletion(BaseModel):
    text: str
    model: str
    provider: str
