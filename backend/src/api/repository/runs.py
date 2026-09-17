from dataclasses import asdict
from datetime import datetime

from sqlmodel import Session, select

from api.mappers import to_plain_run_response, to_run
from api.models import RunRecord, DatasetRecord
from api.repository.datasets import DatasetsRepository
from api.schemas.runs import PlainRunResponseSchema, RunRequestSchema
from domain import Dataset, Run, RunStatus


class RunsRepository:
    """
    Repository class that provides CRUD operations for the ``runs`` table.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get(self, run_id: str) -> RunRecord | None:
        """
        Get a run record from the database.
        """
        statement = select(RunRecord).where(RunRecord.run_id == run_id)
        return self.db.exec(statement).first()

    def list_runs(self, limit: int | None = None) -> list[PlainRunResponseSchema]:
        """
        List runs from the database.
        """
        statement = (
            select(RunRecord, DatasetRecord)
            .join(DatasetRecord, RunRecord.dataset_id == DatasetRecord.dataset_id)
            .order_by(RunRecord.created_at.desc())
        )

        if limit is not None:
            statement = statement.limit(limit)

        rows = self.db.exec(statement).all()

        return [
            to_plain_run_response(run_record, dataset_record)
            for run_record, dataset_record in rows
        ]

    def get(self, run_id: str) -> Run | None:
        """
        Get a run from the database.
        """
        run_record = self._get(run_id)
        return to_run(run_record) if run_record else None

    def create(self, new_run: RunRequestSchema) -> Run | None:
        """
        Create a queued run in the database.
        """
        dataset = DatasetsRepository(self.db).get_by_name_and_instance(
            name=new_run.name, instance=new_run.instance
        )
        if dataset is None:
            return None

        run_dict = new_run.model_dump() | asdict(dataset)
        run_record = RunRecord(**run_dict)

        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)

        return to_run(run_record)

    def update(
        self,
        run_id: str,
        status: RunStatus | None = None,
        finished_at: datetime | None = None,
        total_trucks: int | None = None,
        total_distance: float | None = None,
        runtime_seconds: float | None = None,
    ) -> Run:
        """
        Update a run in the database.

        Raises:
            ValueError: If the run with the given ``run_id`` is not found.
        """
        run_record = self._get(run_id)

        if run_record is None:
            raise ValueError(f"Run with ID {run_id} not found")

        if status is not None:
            run_record.status = status
        if finished_at is not None:
            run_record.finished_at = finished_at
        if total_trucks is not None:
            run_record.total_trucks = total_trucks
        if total_distance is not None:
            run_record.total_distance = total_distance
        if runtime_seconds is not None:
            run_record.runtime_seconds = runtime_seconds

        self.db.commit()
        self.db.refresh(run_record)
        return to_run(run_record)

    def get_run_dataset(self, run_id: str) -> Dataset | None:
        run_record = self._get(run_id)
        if run_record is None:
            return None

        dataset_record = self.db.exec(
            select(DatasetRecord).where(
                DatasetRecord.dataset_id == run_record.dataset_id
            )
        ).first()
        if dataset_record is None:
            return None

        return Dataset(
            dataset_id=dataset_record.dataset_id,
            name=dataset_record.name,
            instance=dataset_record.instance,
        )
