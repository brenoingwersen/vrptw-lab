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
    """
    Connects and fetch data from the database to the API.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_run_record(self, run_id: str) -> RunRecord:
        run_record = self.db.exec(
            select(RunRecord).where(RunRecord.run_id == run_id)
        ).first()

        if not run_record:
            raise HTTPException(status_code=404, detail="Run not found")

        return run_record

    def list_datasets(self) -> list[DatasetSchema]:
        """
        Return all available datasets from the database.
        """
        return [
            DatasetSchema.model_validate(record)
            for record in self.db.exec(select(DatasetRecord)).all()
        ]

    def list_runs(self) -> list[RunDetailResponse]:
        """
        Return all available runs from the database.
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
        """
        Create a new run record in the database
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
        """
        Get a run record from the database
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
        """
        Update a run record in the database
        """
        record = self._get_run_record(run_id)
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_customers_for_run(self, run_id: str) -> list[CustomerSchema]:
        """
        Get the customers for a given run by its ``run_id``.
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
        """
        Get the optimization request for a given run by its ``run_id``.
        """
        run = self.get_run(run_id)

        customers = self.get_customers_for_run(run_id)

        return OptimizationRequestSchema(
            **run.model_dump(),
            customers=customers,
        )

    def get_arcs_for_run(self, run_id: str) -> list[ArcSchema]:
        """
        Get the arcs for a given run by its ``run_id``.
        """
        arcs = self.db.exec(select(ArcRecord).where(ArcRecord.run_id == run_id)).all()

        return [ArcSchema.model_validate(arc) for arc in arcs]

    def get_solution_for_run(self, run_id: str) -> SolutionResponse:
        """
        Build the solution for a given run by its ``run_id``.
        """
        run = self.get_run(run_id).model_dump()

        arcs = [a.model_dump() for a in self.get_arcs_for_run(run_id)]
        if len(arcs) == 0:
            raise HTTPException(
                status_code=404, detail="No arcs found for the given run"
            )

        return SolutionResponse.model_validate({"run": run, "arcs": arcs})

    def create_arcs(self, run_id: str, arcs: list[SolutionArcSchema]) -> None:
        """
        Store the solution arcs for a given run by its ``run_id``.
        """
        arcs_records = [ArcRecord(run_id=run_id, **arc.model_dump()) for arc in arcs]
        self.db.add_all(arcs_records)
        self.db.commit()

    def list_runs_with_solutions(
        self, limit: int | None = None
    ) -> list[SolutionResponse]:
        """
        List all runs with their solutions
        """
