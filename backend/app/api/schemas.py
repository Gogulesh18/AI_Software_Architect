"""Pydantic request/response models for the API layer."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.database.models import JobStage, JobStatus, SourceType


class CreateRepoFromUrlRequest(BaseModel):
    url: str = Field(min_length=1)


class CreateRepoFromLocalRequest(BaseModel):
    path: str = Field(min_length=1)


class RepositoryOut(BaseModel):
    id: str
    name: str
    source_type: SourceType
    created_at: datetime

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: str
    repository_id: str
    status: JobStatus
    stage: JobStage
    progress: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobWithRepositoryOut(JobOut):
    repository: RepositoryOut


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)  # [{"role": "user"|"assistant", "content": "..."}]


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
