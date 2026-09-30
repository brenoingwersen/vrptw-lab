"""Celery task definitions for background solver jobs."""

from loguru import logger

from api.celery_app import celery_app
from api.service import execute_run_sync


@celery_app.task(name="api.tasks.execute_run")
def execute_run_task(run_id: str) -> None:
    """Run the solver for one queued optimization run.

    Delegates to ``execute_run_sync`` and re-raises on failure so Celery can
    mark the task as failed and retry according to worker settings.

    Args:
        run_id: Primary key of the run to process.
    """
    logger.info(f"Celery task started for run {run_id}")
    try:
        execute_run_sync(run_id)
    except Exception:
        logger.exception(f"Celery task failed for run {run_id}")
        raise
