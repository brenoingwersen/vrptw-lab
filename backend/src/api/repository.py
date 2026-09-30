"""Database access layer for datasets, runs, customers, and solution arcs."""

from fastapi import HTTPException
from sqlmodel import Session, select

from api.models import ArcRecord, CustomerRecord, DatasetRecord, RunRecord
from api.schemas import (
    ArcSchema,
    CustomerSchema,
    DatasetSchema,
    OptimizationRequestSchema,
    RunCreateRequest,
    RunDetailResponse,
    SolutionArcSchema,
    SolutionResponse,
)


class Repository:
    """Connects to the database and fetches or persists API data."""

    def __init__(self, db: Session):
        """Attach a SQLModel session for the lifetime of one request or task.

        Args:
            db: Active database session.
        """
        self.db = db

    def _get_run_record(self, run_id: str) -> RunRecord:
        """Load a run row or raise 404."""
        run_record = self.db.exec(
            select(RunRecord).where(RunRecord.run_id == run_id)
        ).first()

        if not run_record:
            raise HTTPException(status_code=404, detail="Run not found")

        return run_record

    def list_datasets(self) -> list[DatasetSchema]:
        """Return all benchmark datasets stored in the database.

        Returns:
            List of dataset name and instance pairs.
        """
        return [
            DatasetSchema.model_validate(record)
            for record in self.db.exec(select(DatasetRecord)).all()
        ]

    def list_runs(self) -> list[RunDetailResponse]:
        """Return all runs with dataset metadata, newest first.

        Returns:
            Empty list when no runs exist.
        """
        records = self.db.exec(
            select(RunRecord, DatasetRecord)
            .join(DatasetRecord)
            .where(RunRecord.dataset_id == DatasetRecord.dataset_id)
        ).all()

        if len(records) == 0:
            return []

        runs = [
            RunDetailResponse.model_validate(
                run.model_dump() | {"name": dataset.name, "instance": dataset.instance}
            )
            for run, dataset in records
        ]
        return sorted(runs, key=lambda r: r.created_at, reverse=True)

    def create_run(self, request: RunCreateRequest) -> RunDetailResponse:
        """Persist a new queued run for the requested dataset.

        Args:
            request: Dataset selection, constraints, and solver parameters.

        Returns:
            The created run with ``queued`` status.

        Raises:
            HTTPException: If the dataset name and instance pair is not found.
        """
        dataset_record = self.db.exec(
            select(DatasetRecord)
            .where(DatasetRecord.name == request.name)
            .where(DatasetRecord.instance == request.instance)
        ).first()

        if not dataset_record:
            raise HTTPException(
                status_code=404, detail="Dataset not found for the requested run"
            )

        run_record = RunRecord(
            dataset_id=dataset_record.dataset_id,
            **request.model_dump(exclude={"name", "instance"}),
        )
        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)

        response = run_record.model_dump() | {
            "name": request.name,
            "instance": request.instance,
        }

        return RunDetailResponse.model_validate(response)

    def get_run(self, run_id: str) -> RunDetailResponse:
        """Return run metadata joined with dataset name and instance.

        Args:
            run_id: Primary key of the run.

        Raises:
            HTTPException: If ``run_id`` does not exist.
        """
        run_record = self._get_run_record(run_id)

        dataset_record = self.db.exec(
            select(DatasetRecord).where(
                DatasetRecord.dataset_id == run_record.dataset_id
            )
        ).first()

        return RunDetailResponse.model_validate(
            {
                **run_record.model_dump(),
                "name": dataset_record.name,
                "instance": dataset_record.instance,
            }
        )

    def update_run(self, run_id: str, **kwargs) -> RunRecord:
        """Update fields on an existing run record.

        Args:
            run_id: Primary key of the run.
            **kwargs: Column names and values to set.

        Returns:
            Refreshed run row after commit.

        Raises:
            HTTPException: If ``run_id`` does not exist.
        """
        record = self._get_run_record(run_id)
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_customers_for_run(self, run_id: str) -> list[CustomerSchema]:
        """Return all customers for the dataset linked to a run.

        Args:
            run_id: Primary key of the run.

        Returns:
            Customer rows for the run's dataset.

        Raises:
            ValueError: If the dataset has no customers.
        """
        customers = self.db.exec(
            select(CustomerRecord).where(
                CustomerRecord.dataset_id == self._get_run_record(run_id).dataset_id
            )
        ).all()

        if len(customers) == 0:
            raise ValueError("No customers available for the optimization request")

        return [CustomerSchema.model_validate(record) for record in customers]

    def get_optimization_request_for_run(
        self, run_id: str
    ) -> OptimizationRequestSchema:
        """Build the solver input DTO for a run.

        Args:
            run_id: Primary key of the run.

        Returns:
            Run constraints plus all customer nodes for the dataset.
        """
        run = self.get_run(run_id)

        customers = self.get_customers_for_run(run_id)

        return OptimizationRequestSchema(
            **run.model_dump(),
            customers=customers,
        )

    def get_arcs_for_run(self, run_id: str) -> list[ArcSchema]:
        """Return stored solution arcs with resolved customer coordinates.

        Args:
            run_id: Primary key of the run.
        """
        arcs = self.db.exec(select(ArcRecord).where(ArcRecord.run_id == run_id)).all()

        return [ArcSchema.model_validate(arc) for arc in arcs]

    def get_solution_for_run(self, run_id: str) -> SolutionResponse:
        """Return run metadata plus route arcs for ``run_id``.

        Args:
            run_id: Primary key of the run.

        Returns:
            Combined run detail and arc list.

        Raises:
            HTTPException: If the run has no stored arcs.
        """
        run = self.get_run(run_id).model_dump()

        arcs = [a.model_dump() for a in self.get_arcs_for_run(run_id)]
        if len(arcs) == 0:
            raise HTTPException(
                status_code=404, detail="No arcs found for the given run"
            )

        return SolutionResponse.model_validate({"run": run, "arcs": arcs})

    def create_arcs(self, run_id: str, arcs: list[SolutionArcSchema]) -> None:
        """Persist solver output arcs for a run.

        Args:
            run_id: Primary key of the run.
            arcs: Route segments returned by ``Solver``.
        """
        arcs_records = [ArcRecord(run_id=run_id, **arc.model_dump()) for arc in arcs]
        self.db.add_all(arcs_records)
        self.db.commit()
