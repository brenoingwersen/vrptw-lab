from datetime import UTC, datetime

import pandas as pd
from loguru import logger
from sqlmodel import Session

from api.db import engine
from api.repository.instances import InstancesRepository
from api.repository.runs import RunsRepository
from api.repository.stops import StopsRepository
from api.schemas.stops import NewStopSchema
from vrptw.instance import VRPTWInstance
from vrptw.problem import VRPTWProblem
from vrptw.run_status import RunStatus, from_cp_status
from vrptw.solver import VRPTWSolver
from vrptw.solver_config import SolverConfig


class RunExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.runs_repository = RunsRepository(db)
        self.instances_repository = InstancesRepository(db)
        self.stops_repository = StopsRepository(db)

    def execute(self, run_id: str) -> None:
        """
        Execute a run.
        """
        self.runs_repository.update(run_id, status=RunStatus.RUNNING)

        run = self.runs_repository.get(run_id)

        instance = self.instances_repository.get_by_dataset_id(run.dataset_id)
        df = pd.DataFrame.from_records([row.model_dump() for row in instance])

        instance = VRPTWInstance.from_df(df)

        problem = VRPTWProblem(
            instance=instance,
            max_trucks=run.max_trucks,
            truck_capacity=run.truck_capacity,
        )
        config = SolverConfig(
            max_time_in_seconds=run.max_time_in_seconds, random_seed=run.random_seed
        )
        solver = VRPTWSolver(problem, config)
        result = solver.solve()

        run_status: RunStatus = from_cp_status(result.status)
        logger.info(f"Run {run_id} finished with status: {run_status.value}")

        self.runs_repository.update(
            run_id,
            status=run_status.value,
            finished_at=datetime.now(UTC),
            total_trucks=result.n_trucks,
            total_distance=result.total_distance,
        )

        stops_list = result.solution.to_stops(instance)
        stops = [NewStopSchema(**stop) for stop in stops_list]
        self.stops_repository.create(run_id, stops)
        logger.info(f"Stops for run {run_id} created. Total stops: {len(stops):,}.")


async def execute_run(run_id: str) -> None:
    with Session(engine) as db:
        executor = RunExecutor(db)
        executor.execute(run_id)
