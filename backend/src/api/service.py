from datetime import UTC, datetime

from loguru import logger
from sqlmodel import Session

from api.db import engine
from api.models import RunStatus
from api.optimizer import Solver
from api.repository import Repository
from api.schemas import OptimizationRequestSchema, OptimizationResultSchema


class RunExecutor:
    def __init__(self, db: Session):
        self.repository = Repository(db)

    def execute(self, run_id: str) -> None:
        logger.info(f"Running executor for run {run_id}.")

        logger.info(f"Changing status for run '{run_id}' to 'running'.")
        self.repository.update_run(run_id, status=RunStatus.running)

        logger.info(f"Building optimization problem for run {run_id}.")
        request: OptimizationRequestSchema = (
            self.repository.get_optimization_request_for_run(run_id)
        )

        solver = Solver(request)

        logger.info(f"Running the solver for run {run_id}")
        result: OptimizationResultSchema = solver.solve()

        logger.info(f"Solver completed for run {run_id}.")

        logger.info(f"Updating the run's metadata for run {run_id}.")
        update_payload = result.model_dump(exclude={"arcs"}) | {
            "finished_at": datetime.now(UTC)
        }
        self.repository.update_run(run_id, **update_payload)

        logger.info(f"Updating the run's solution for run {run_id}.")
        self.repository.create_arcs(run_id, result.arcs)


async def execute_run(run_id: str):
    """
    Execute the optimization
    """
    with Session(engine) as db:
        executor = RunExecutor(db)
        executor.execute(run_id)


def execute_run_sync(run_id: str) -> None:
    """
    Execute the optimization synchronously
    """
    with Session(engine) as db:
        RunExecutor(db).execute(run_id)
