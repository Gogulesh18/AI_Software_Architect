"""Anthropic Claude provider — the default per ARCHITECTURE.md."""

from functools import lru_cache

import anthropic

from app.core.config import get_settings
from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str):
        self._api_key = api_key
        self._model = model
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        return self.chat(system, [{"role": "user", "content": user}], max_tokens)

    def chat(self, system: str, messages: list[dict[str, str]], max_tokens: int = 1000) -> str:
        if self._client is None:
            raise RuntimeError("Anthropic provider used without an API key — check is_available first")
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,  # type: ignore[arg-type]  # plain dicts match MessageParam's shape at runtime; the SDK's TypedDict stub is just stricter
        )
        return "".join(block.text for block in response.content if block.type == "text")


@lru_cache
def get_anthropic_provider() -> AnthropicProvider:
    settings = get_settings()
    return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)
