"""SQLAlchemy ORM models.

One AnalysisJob per analysis run of a Repository; AnalysisResult holds every
artifact the pipeline produces (summary, graph, diagrams, scores, report) as
JSON columns keyed by job. Chat is intentionally stateless (the frontend
carries conversation history in the request) so no chat tables exist yet.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class SourceType(str, enum.Enum):
    GIT_URL = "git_url"
    ZIP = "zip"
    LOCAL = "local"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobStage(str, enum.Enum):
    QUEUED = "queued"
    INGEST = "ingest"
    PARSE = "parse"
    GRAPH = "graph"
    ANALYZE = "analyze"
    EMBED = "embed"
    DIAGRAM = "diagram"
    REPORT = "report"
    DONE = "done"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    source_ref: Mapped[str] = mapped_column(Text)  # URL, uploaded zip path, or local path
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    jobs: Mapped[list["AnalysisJob"]] = relationship(back_populates="repository")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id"))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.QUEUED)
    stage: Mapped[JobStage] = mapped_column(Enum(JobStage), default=JobStage.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    repository: Mapped["Repository"] = relationship(back_populates="jobs")
    result: Mapped["AnalysisResult | None"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("analysis_jobs.id"), unique=True)

    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    architecture: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    folders: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dependency_graph: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    database_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    api_surface: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    patterns: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    solid: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quality: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    security: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    performance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    diagrams: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    job: Mapped["AnalysisJob"] = relationship(back_populates="result")
