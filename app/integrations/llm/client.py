"""LLM client boundary.

No provider is called unless an API key is configured, and the automation
engine does not call this client yet.
"""

from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings
from app.integrations.llm.types import LLMCompletion


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> LLMCompletion: ...


class MockLLMClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def complete(self, prompt: str) -> LLMCompletion:
        return LLMCompletion(
            text="",
            model=self._settings.llm_model or "mock",
            provider=self._settings.llm_provider or "mock",
        )


class UnconfiguredLLMClient(LLMClient):
    async def complete(self, prompt: str) -> LLMCompletion:
        raise RuntimeError("LLM_API_KEY is not configured")


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.mock_external_services or not settings.llm_api_key.strip():
        return MockLLMClient(settings)
    # TODO(llm): map LLM_PROVIDER to a concrete HTTP client. httpx is imported
    # so the dependency is available when that provider is added.
    _ = httpx
    return UnconfiguredLLMClient()
