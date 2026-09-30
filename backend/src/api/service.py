"""Run execution orchestration between the database and the solver.

``RunExecutor`` drives the queued → running → completed/failed lifecycle for one
run. Called synchronously from Celery via ``execute_run_sync``.
"""

from datetime import UTC, datetime

from loguru import logger
from sqlmodel import Session

from api.db import engine
from api.models import RunStatus
from api.optimizer import Solver
from api.repository import Repository
from api.schemas import OptimizationRequestSchema, OptimizationResultSchema


class RunExecutor:
    """Runs the solver for one optimization run and persists the result."""

    def __init__(self, db: Session):
        """Create an executor bound to a database session.

        Args:
            db: Active SQLModel session for the run.
        """
        self.repository = Repository(db)

    def execute(self, run_id: str) -> None:
        """Execute the full optimization pipeline for ``run_id``.

        Transitions the run to ``running``, builds the solver input, runs
        ``Solver``, then updates run metadata and stores route arcs.

        Args:
            run_id: Primary key of the queued run.
        """
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


def execute_run_sync(run_id: str) -> None:
    """Execute one optimization run synchronously in a fresh database session.

    Args:
        run_id: Primary key of the run to process.
    """
    with Session(engine) as db:
        RunExecutor(db).execute(run_id)
