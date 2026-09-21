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
from api.service import execute_run

router = APIRouter()


@router.get("/datasets", response_model=list[DatasetSchema])
async def list_datasets(db: Annotated[Session, Depends(get_db)]) -> list[DatasetSchema]:
    """
    Endpoint to list all available datasets
    """
    return Repository(db).list_datasets()


@router.get("/runs", response_model=list[RunDetailResponse])
async def list_runs(db: Annotated[Session, Depends(get_db)]) -> list[RunDetailResponse]:
    """
    Endpoint to list all available runs
    """
    return Repository(db).list_runs()


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_solution(
    db: Annotated[Session, Depends(get_db)], run_id: str
) -> RunDetailResponse:
    """
    Endpoint to get the solution for a given run by its ID
    """
    return Repository(db).get_run(run_id)


@router.post("/runs", response_model=RunDetailResponse)
async def create_run(
    db: Annotated[Session, Depends(get_db)],
    request: RunCreateRequest,
    background_tasks: BackgroundTasks,
) -> RunDetailResponse:
    """
    Endpoint to create a new run
    """
    run = Repository(db).create_run(request)

    # Run the executor
    background_tasks.add_task(execute_run, run.run_id)

    return run


@router.get("/runs/{run_id}/solution", response_model=SolutionResponse)
async def get_solution_for_run(
    db: Annotated[Session, Depends(get_db)], run_id: str
) -> SolutionResponse:
    """
    Endpoint to get the solution for a given run by its ID
    """
    return Repository(db).get_solution_for_run(run_id)


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """Check whether the API is alive."""
    return {"status": "ok"}
