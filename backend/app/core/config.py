"""Application configuration, loaded from environment variables / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-5"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # Embeddings
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Job runner
    job_runner: str = "inprocess"  # "inprocess" | "celery"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Database
    database_url: str = "sqlite:///./dev.db"

    # Vector store
    chroma_persist_dir: str = "./.data/chroma"

    # Ingestion
    repo_workspace_dir: str = "./.data/repos"
    max_files_per_repo: int = 8000
    max_file_size_bytes: int = 1_000_000

    # API
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir).resolve()

    @property
    def repo_workspace_path(self) -> Path:
        return Path(self.repo_workspace_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    settings.repo_workspace_path.mkdir(parents=True, exist_ok=True)
    return settings
