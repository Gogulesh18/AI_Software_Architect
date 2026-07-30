"""Celery entrypoint for prod mode (docker-compose.yml runs this module as a worker).

Not exercised in local dev (JOB_RUNNER=inprocess doesn't import this module),
so it isn't covered by the local test suite — it re-dispatches to the same
`run_analysis_job` pipeline used in dev, just synchronously inside a worker
process instead of an asyncio task.
"""

import asyncio

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_software_architect",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


@celery_app.task(name="analyze_repository")
def analyze_repository_task(job_id: str) -> None:
    from app.workers.pipeline import run_analysis_job

    asyncio.run(run_analysis_job(job_id))
