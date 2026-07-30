"""Job status, analysis results, diagrams, RAG chat, and export."""

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.api.schemas import ChatRequest, ChatResponse, JobOut
from app.core.exceptions import InvalidJobStateError, JobNotFoundError
from app.database.models import AnalysisJob, AnalysisResult, JobStatus
from app.database.session import get_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _get_job(db: Session, job_id: str) -> AnalysisJob:
    job = db.get(AnalysisJob, job_id)
    if job is None:
        raise JobNotFoundError(f"Job not found: {job_id}")
    return job


def _get_done_job(db: Session, job_id: str) -> tuple[AnalysisJob, AnalysisResult]:
    job = _get_job(db, job_id)
    if job.status != JobStatus.DONE or job.result is None:
        raise InvalidJobStateError(f"Job {job_id} has no results yet (status={job.status.value})")
    return job, job.result


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> AnalysisJob:
    return _get_job(db, job_id)


@router.get("/{job_id}/result")
def get_result(job_id: str, db: Session = Depends(get_db)) -> dict:
    _job, r = _get_done_job(db, job_id)
    return {
        "summary": r.summary,
        "architecture": r.architecture,
        "folders": r.folders,
        "database_schema": r.database_schema,
        "api_surface": r.api_surface,
        "patterns": r.patterns,
        "solid": r.solid,
        "quality": r.quality,
        "security": r.security,
        "performance": r.performance,
        "scores": r.scores,
    }


@router.get("/{job_id}/diagrams")
def list_diagrams(job_id: str, db: Session = Depends(get_db)) -> dict:
    _job, result = _get_done_job(db, job_id)
    return {"types": sorted((result.diagrams or {}).keys())}


@router.get("/{job_id}/diagrams/{diagram_type}")
def get_diagram(job_id: str, diagram_type: str, db: Session = Depends(get_db)) -> dict:
    _job, result = _get_done_job(db, job_id)
    diagrams = result.diagrams or {}
    if diagram_type not in diagrams:
        raise InvalidJobStateError(f"No diagram of type '{diagram_type}' for this job")
    return diagrams[diagram_type]


@router.get("/{job_id}/report", response_class=PlainTextResponse)
def get_report_markdown(job_id: str, db: Session = Depends(get_db)) -> str:
    _job, result = _get_done_job(db, job_id)
    return result.report_markdown or ""


@router.get("/{job_id}/source")
def get_source(job_id: str, file: str, db: Session = Depends(get_db)) -> dict:
    _get_done_job(db, job_id)

    from app.rag.source import get_source_chunks

    return {"file": file, "chunks": get_source_chunks(job_id, file)}


@router.post("/{job_id}/chat", response_model=ChatResponse)
def chat(job_id: str, payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    job, _result = _get_done_job(db, job_id)

    from app.rag.chat import answer_question

    answer, sources = answer_question(job_id, job.repository.name, payload.message, payload.history)
    return ChatResponse(answer=answer, sources=sources)


@router.get("/{job_id}/export/{fmt}")
def export(job_id: str, fmt: str, db: Session = Depends(get_db)) -> Response:
    job, result = _get_done_job(db, job_id)

    from app.export.service import export_result

    content, media_type, filename = export_result(job.repository.name, result, fmt)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
