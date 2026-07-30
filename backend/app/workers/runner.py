"""Job dispatch: in-process asyncio task (dev) or Celery task (prod), chosen by
settings.job_runner. Callers just call `enqueue(job_id)` and don't care which."""

import asyncio
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Keep references so fire-and-forget tasks aren't garbage collected mid-run.
_background_tasks: set[asyncio.Task] = set()


def enqueue(job_id: str) -> None:
    settings = get_settings()
    if settings.job_runner == "celery":
        from app.workers.celery_app import analyze_repository_task

        analyze_repository_task.delay(job_id)
        return

    from app.workers.pipeline import run_analysis_job

    task = asyncio.create_task(run_analysis_job(job_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    task.add_done_callback(_log_if_failed)


def _log_if_failed(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.error("Background analysis task raised: %s", exc)
