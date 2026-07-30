"""Repository ingestion endpoints: create a Repository + AnalysisJob from a
git URL, an uploaded ZIP, or a local path, then enqueue the analysis job."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import (
    CreateRepoFromLocalRequest,
    CreateRepoFromUrlRequest,
    JobOut,
    RepositoryOut,
)
from app.core.config import get_settings
from app.core.exceptions import RepoIngestError
from app.database.models import AnalysisJob, Repository, SourceType
from app.database.session import get_db
from app.ingest.source import prepare_local
from app.workers.runner import enqueue

router = APIRouter(prefix="/api/repos", tags=["repos"])


def _create_job(db: Session, repository: Repository) -> AnalysisJob:
    db.add(repository)
    db.flush()  # populate repository.id (Python-side default applies on flush, not construction)
    job = AnalysisJob(repository_id=repository.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    enqueue(job.id)
    return job


@router.post("/url", response_model=JobOut)
async def create_from_url(payload: CreateRepoFromUrlRequest, db: Session = Depends(get_db)) -> AnalysisJob:
    name = payload.url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git") or payload.url
    repository = Repository(name=name, source_type=SourceType.GIT_URL, source_ref=payload.url)
    return _create_job(db, repository)


@router.post("/local", response_model=JobOut)
async def create_from_local(payload: CreateRepoFromLocalRequest, db: Session = Depends(get_db)) -> AnalysisJob:
    # Local paths are cheap to validate synchronously (unlike a git clone),
    # so reject an obviously bad path with 400 instead of creating a job
    # that's guaranteed to fail once the background pipeline picks it up.
    prepare_local(payload.path)

    name = Path(payload.path).name or payload.path
    repository = Repository(name=name, source_type=SourceType.LOCAL, source_ref=payload.path)
    return _create_job(db, repository)


@router.post("/zip", response_model=JobOut)
async def create_from_zip(file: UploadFile, db: Session = Depends(get_db)) -> AnalysisJob:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise RepoIngestError("Uploaded file must be a .zip archive")

    settings = get_settings()
    uploads_dir = settings.repo_workspace_path / "_uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    name = Path(file.filename).stem
    repo_id = str(uuid.uuid4())
    repository = Repository(id=repo_id, name=name, source_type=SourceType.ZIP, source_ref="")
    dest = uploads_dir / f"{repo_id}.zip"
    dest.write_bytes(await file.read())
    repository.source_ref = str(dest)

    return _create_job(db, repository)


@router.get("", response_model=list[RepositoryOut])
def list_repos(db: Session = Depends(get_db)) -> list[Repository]:
    return db.query(Repository).order_by(Repository.created_at.desc()).limit(100).all()
