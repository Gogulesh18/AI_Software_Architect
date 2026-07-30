"""Selects the configured embedding provider."""

from app.core.config import get_settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.fastembed_provider import get_fastembed_provider


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "fastembed":
        return get_fastembed_provider()
    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {settings.embedding_provider!r} (only 'fastembed' is implemented)")
