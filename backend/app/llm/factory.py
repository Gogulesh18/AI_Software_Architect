"""Selects the configured LLM provider. Only `anthropic` ships today; the
interface in app.llm.base is what a future OpenAI provider would implement."""

from app.core.config import get_settings
from app.llm.anthropic_provider import get_anthropic_provider
from app.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        return get_anthropic_provider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider!r} (only 'anthropic' is implemented)")
