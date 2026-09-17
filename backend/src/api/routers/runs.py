from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from loguru import logger
from sqlmodel import Session

from api.db import get_db
from api.repository import RunsRepository
from api.schemas import RunRequestSchema, RunResponseSchema
from api.service import execute_run

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/", response_model=RunResponseSchema)
async def create_run(
    db: Annotated[Session, Depends(get_db)],
    payload: RunRequestSchema,
    background_tasks: BackgroundTasks,
):
    """
    POST request endpoint to create and queue an optimization run.
    """
    repository = RunsRepository(db)
    run = repository.create(payload)
    logger.info(f"Created run {run.run_id}")

    background_tasks.add_task(execute_run, run.run_id)
    logger.info(f"Executing run {run.run_id}")
    return run
