"""Local ONNX embeddings via fastembed — the default (see ARCHITECTURE.md:
no second paid API key required). Model weights are downloaded once and
cached by fastembed itself on first use."""

from functools import lru_cache

from fastembed import TextEmbedding

from app.core.config import get_settings
from app.embeddings.base import EmbeddingProvider


class FastEmbedProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


@lru_cache
def get_fastembed_provider() -> FastEmbedProvider:
    settings = get_settings()
    return FastEmbedProvider(model_name=settings.embedding_model)
