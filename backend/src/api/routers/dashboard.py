from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger
from sqlmodel import Session

from api.db import get_db
from api.repository import RunsRepository, ArcsRepository, DatasetsRepository
from api.schemas import (
    PlainRunResponseSchema,
    DashboardArcResponseSchema,
    DatasetResponseSchema,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/datasets/", response_model=list[DatasetResponseSchema])
def get_datasets(db: Annotated[Session, Depends(get_db)]):
    """
    GET request endpoint to list all available datasets.
    """
    repository = DatasetsRepository(db)
    return repository.list_datasets()


@router.get("/runs/", response_model=list[PlainRunResponseSchema])
def get_runs(db: Annotated[Session, Depends(get_db)], limit: int | None = None):
    """
    GET request endpoint to list all available optimization runs.
    """
    repository = RunsRepository(db)
    return repository.list_runs(limit)


@router.get("/runs/{run_id}/arcs/", response_model=list[DashboardArcResponseSchema])
def get_run_arcs(db: Annotated[Session, Depends(get_db)], run_id: str):
    """
    GET request endpoint to list all arcs for a given run.
    """
    repository = ArcsRepository(db)
    return repository.get_run_dashboard_arcs(run_id)
