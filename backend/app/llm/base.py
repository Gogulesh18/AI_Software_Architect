"""Provider-agnostic LLM interface. Concrete providers (Anthropic today,
OpenAI addable later — see ARCHITECTURE.md) implement `complete`; callers
never import a concrete provider directly, only `get_llm_provider()`."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """False when no API key is configured — callers should fall back
        to a deterministic, non-LLM code path rather than erroring."""

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        """Single-turn completion: system prompt + one user message -> text."""

    @abstractmethod
    def chat(self, system: str, messages: list[dict[str, str]], max_tokens: int = 1000) -> str:
        """Multi-turn: messages is [{"role": "user"|"assistant", "content": str}, ...]."""
