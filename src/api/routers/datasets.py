from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.db import get_db
from api.models import Dataset
from api.repository.datasets import DatasetsRepository

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=list[Dataset])
async def list_datasets(
    db: Annotated[Session, Depends(get_db)], limit: int | None = None
):
    """
    List all available datasets
    """
    repository = DatasetsRepository(db)
    return repository.list_datasets(limit)
