from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from sqlmodel import Session

from api.db import get_db
from api.models import Run, Stop
from api.repository.runs import RunsRepository
from api.repository.stops import StopsRepository
from api.schemas.runs import CreateRunSchema
from api.service import execute_run

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/", response_model=Run)
async def create_run(
    db: Annotated[Session, Depends(get_db)],
    payload: CreateRunSchema,
    background_tasks: BackgroundTasks,
):
    """
    Create and execute a new optimization run.
    """
    repository = RunsRepository(db)
    run = repository.create(payload)
    if run is None:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset with name {payload.name} and instance {payload.instance} not found",
        )
    logger.info(f"Created run_id: {run.run_id}")

    # Execute the run in the background
    background_tasks.add_task(execute_run, run.run_id)

    return run


@router.get("/", response_model=list[Run])
def get_runs(db: Annotated[Session, Depends(get_db)], limit: int | None = None):
    """
    List all available optimization runs.
    """
    runs_repo = RunsRepository(db)
    return runs_repo.list_runs(limit)


@router.get("/{run_id}/stops", response_model=list[Stop])
def get_stops(db: Annotated[Session, Depends(get_db)], run_id: str):
    """
    List all stops for a given run.
    """
    stops_repo = StopsRepository(db)
    stops = stops_repo.list_stops(run_id)
    if stops is None:
        raise HTTPException(
            status_code=404,
            detail=f"No stops found for run {run_id}.",
        )
    return stops
