from datetime import datetime

from sqlmodel import Session, select

from api.models import Run
from api.repository.datasets import DatasetsRepository
from api.schemas.runs import CreateRunSchema
from vrptw.run_status import RunStatus


class RunsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_runs(self, limit: int | None = None) -> list[Run]:
        """
        List runs from the database.
        """
        statement = select(Run)
        return (
            self.db.exec(statement).all()
            if limit is None
            else self.db.exec(statement).limit(limit).all()
        )

    def get(self, run_id: str) -> Run | None:
        """
        Get a run from the database.
        """
        statement = select(Run).where(Run.run_id == run_id)
        return self.db.exec(statement).first()

    def create(self, new_run: CreateRunSchema) -> Run | None:
        """
        Create a new run in the database.
        """
        dataset = DatasetsRepository(self.db).get_by_name_and_instance(
            name=new_run.name, instance=new_run.instance
        )
        if dataset is None:
            return None

        run_dict = new_run.model_dump() | {"dataset_id": dataset.dataset_id}
        run = Run(**run_dict)

        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update(
        self,
        run_id: str,
        status: RunStatus | None = None,
        finished_at: datetime | None = None,
        total_trucks: int | None = None,
        total_distance: float | None = None,
    ) -> Run:
        """
        Update a run in the database.

        Raises:
            ValueError: If the run with the given ``run_id`` is not found.
        """
        run = self.get(run_id)

        if run is None:
            raise ValueError(f"Run with ID {run_id} not found")

        if status is not None:
            run.status = status
        if finished_at is not None:
            run.finished_at = finished_at
        if total_trucks is not None:
            run.total_trucks = total_trucks
        if total_distance is not None:
            run.total_distance = total_distance

        self.db.commit()
        self.db.refresh(run)
        return run
