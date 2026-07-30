"""Provider-agnostic embedding interface — local fastembed today, swappable
for OpenAI/Voyage embeddings later (see ARCHITECTURE.md)."""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_one(self, text: str) -> list[float]: ...
