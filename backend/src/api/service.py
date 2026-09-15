from datetime import UTC, datetime

# from loguru import logger
from sqlmodel import Session

from api.db import engine
from api.mappers import solver_status_to_run_status
from api.repository.arcs import ArcsRepository
from api.repository.customers import CustomersRepository
from api.repository.runs import RunsRepository
from domain import OptimizationRequest, OptimizationResult, RunStatus
from optimizer.solver import Solver


class RunExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.runs_repository = RunsRepository(db)
        self.customers_repository = CustomersRepository(db)
        self.arcs_repository = ArcsRepository(db)

    def execute(self, run_id: str) -> None:
        run = self.runs_repository.update(run_id, status=RunStatus.running)

        customers = self.customers_repository.get_by_dataset_id(run.dataset_id)

        request = OptimizationRequest(
            max_trucks=run.max_trucks,
            truck_capacity=run.truck_capacity,
            max_time_in_seconds=run.max_time_in_seconds,
            random_seed=run.random_seed,
            customers=customers,
        )

        solver = Solver(request)
        result: OptimizationResult = solver.solve()

        self.runs_repository.update(
            run_id,
            status=solver_status_to_run_status(result.solver_status),
            finished_at=datetime.now(UTC),
            total_trucks=result.total_trucks,
            total_distance=result.total_distance,
            runtime_seconds=result.runtime_seconds,
        )

        self.arcs_repository.create(run_id, result.route_arcs)


async def execute_run(run_id: str) -> None:
    with Session(engine) as db:
        executor = RunExecutor(db)
        executor.execute(run_id)
