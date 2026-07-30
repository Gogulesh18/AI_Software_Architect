"""The analysis pipeline: ingest -> parse -> graph -> analyze -> embed -> diagram -> report.

Phases 3-5 hook into `_run_pipeline_sync` as their stages land; each stage is
wrapped in its own try/except-free block (errors propagate to the top-level
handler, which marks the job failed) but stages are ordered so partial
progress is visible via job.stage/progress even before the whole run finishes.
"""

import asyncio
import dataclasses
import logging
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.database.models import (
    AnalysisJob,
    AnalysisResult,
    JobStage,
    JobStatus,
    Repository,
    SourceType,
)
from app.database.session import SessionLocal
from app.graph.builder import build_graph
from app.graph.serialize import graph_to_json
from app.graph.summary import compute_summary
from app.ingest.files import enumerate_source_files
from app.ingest.source import clone_git_repo, extract_zip, prepare_local
from app.parser.ecosystem import detect_ecosystem
from app.parser.service import parse_files

logger = logging.getLogger(__name__)


async def run_analysis_job(job_id: str) -> None:
    await asyncio.to_thread(_run_pipeline_sync, job_id)


def _run_pipeline_sync(job_id: str) -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            logger.error("Job %s not found", job_id)
            return
        repository = db.get(Repository, job.repository_id)
        if repository is None:
            logger.error("Repository %s for job %s not found", job.repository_id, job_id)
            return

        job.status = JobStatus.RUNNING
        _set_stage(db, job, JobStage.INGEST, 5)

        workspace = settings.repo_workspace_path / job_id
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            repo_root = _materialize(repository, workspace)

            _set_stage(db, job, JobStage.PARSE, 25)
            records = enumerate_source_files(
                repo_root, settings.max_files_per_repo, settings.max_file_size_bytes
            )
            parsed_files = parse_files(records)
            ecosystem = detect_ecosystem(records)

            _set_stage(db, job, JobStage.GRAPH, 55)
            graph = build_graph(parsed_files)
            summary = compute_summary(parsed_files, ecosystem)

            _set_stage(db, job, JobStage.ANALYZE, 70)
            from app.analyzer.pipeline import run_all_analyzers

            analysis = run_all_analyzers(parsed_files, graph, summary)

            _set_stage(db, job, JobStage.DIAGRAM, 85)
            from app.diagram.pipeline import build_all_diagrams

            diagrams = build_all_diagrams(parsed_files, graph, summary, analysis)

            _set_stage(db, job, JobStage.REPORT, 92)
            from app.llm.report import synthesize_report

            report_markdown = synthesize_report(repository.name, summary, analysis)

            _set_stage(db, job, JobStage.EMBED, 96)
            from app.rag.indexer import index_repository

            index_repository(job_id, parsed_files)

            result = AnalysisResult(
                job_id=job.id,
                summary=dataclasses.asdict(summary),
                architecture=analysis.architecture,
                folders=dataclasses.asdict(summary)["folder_tree"],
                dependency_graph=graph_to_json(graph),
                database_schema=analysis.database_schema,
                api_surface=analysis.api_surface,
                patterns=analysis.patterns,
                solid=analysis.solid,
                quality=analysis.quality,
                security=analysis.security,
                performance=analysis.performance,
                scores=analysis.scores,
                diagrams=diagrams,
                report_markdown=report_markdown,
            )
            db.add(result)

            job.status = JobStatus.DONE
            _set_stage(db, job, JobStage.DONE, 100)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    except Exception as exc:  # pragma: no cover - top-level safety net
        logger.exception("Analysis job %s failed", job_id)
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)[:2000]
            db.commit()
    finally:
        db.close()


def _materialize(repository: Repository, workspace: Path) -> Path:
    if repository.source_type == SourceType.GIT_URL:
        return clone_git_repo(repository.source_ref, workspace)
    if repository.source_type == SourceType.ZIP:
        return extract_zip(Path(repository.source_ref), workspace)
    return prepare_local(repository.source_ref)


def _set_stage(db, job: AnalysisJob, stage: JobStage, progress: int) -> None:
    job.stage = stage
    job.progress = progress
    db.commit()
