from loguru import logger

from api.celery_app import celery_app
from api.service import execute_run_sync


@celery_app.task(name="api.tasks.execute_run")
def execute_run_task(run_id: str) -> None:
    logger.info(f"Celery task started for run {run_id}")
    try:
        execute_run_sync(run_id)
    except Exception:
        logger.exception(f"Celery task failed for run {run_id}")
        raise
