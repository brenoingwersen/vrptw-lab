"""FastAPI routes for datasets, runs, and health checks."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlmodel import Session

from api.db import get_db
from api.repository import Repository
from api.schemas import (
    DatasetSchema,
    RunCreateRequest,
    RunDetailResponse,
    SolutionResponse,
)
from api.tasks import execute_run_task

router = APIRouter()


@router.get("/datasets", response_model=list[DatasetSchema])
async def list_datasets(db: Annotated[Session, Depends(get_db)]) -> list[DatasetSchema]:
    """List all benchmark datasets available in the database."""
    return Repository(db).list_datasets()


@router.get("/runs", response_model=list[RunDetailResponse])
async def list_runs(db: Annotated[Session, Depends(get_db)]) -> list[RunDetailResponse]:
    """List all optimization runs, newest first."""
    return Repository(db).list_runs()


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_solution(
    db: Annotated[Session, Depends(get_db)], run_id: str
) -> RunDetailResponse:
    """Return run status, config, and metrics for ``run_id``.

    Does not include route arcs; use ``GET /runs/{run_id}/solution`` for that.
    """
    return Repository(db).get_run(run_id)


@router.post("/runs", response_model=RunDetailResponse)
async def create_run(
    db: Annotated[Session, Depends(get_db)],
    request: RunCreateRequest,
    background_tasks: BackgroundTasks,
) -> RunDetailResponse:
    """Create a run and enqueue a Celery solver job.

    Returns the queued run record immediately; the worker updates status and
    results asynchronously.
    """
    run = Repository(db).create_run(request)

    execute_run_task.delay(run.run_id)

    return run


@router.get("/runs/{run_id}/solution", response_model=SolutionResponse)
async def get_solution_for_run(
    db: Annotated[Session, Depends(get_db)], run_id: str
) -> SolutionResponse:
    """Return the full route solution with customer coordinates for ``run_id``."""
    return Repository(db).get_solution_for_run(run_id)


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """Check whether the API is alive."""
    return {"status": "ok"}
