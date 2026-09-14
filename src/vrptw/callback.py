"""CP-SAT solver callbacks for the VRPTW model."""

from loguru import logger
from ortools.sat.python import cp_model


class VRPTWCallback(cp_model.CpSolverSolutionCallback):
    """Track and log CP-SAT search progress."""

    def __init__(self, stage: str = "search"):
        super().__init__()
        self._stage = stage
        self._solutions_found = 0
        self._first_objective: int | None = None
        self._best_objective: int | None = None

    def on_solution_callback(self) -> None:
        """Record each improving solution at DEBUG level."""
        self._solutions_found += 1
        objective = int(self.objective_value)
        if self._first_objective is None:
            self._first_objective = objective
        self._best_objective = objective
        logger.debug(f"[{self._stage}] objective improved: {objective:,}")

    def log_summary(self) -> None:
        """Log a one-line search summary at INFO level."""
        if self._solutions_found == 0:
            logger.warning(f"{self._stage} search: no improving solutions found")
            return

        logger.info(
            f"{self._stage} search: {self._solutions_found} improving solutions, "
            f"objective {self._first_objective:,} → {self._best_objective:,}"
        )
