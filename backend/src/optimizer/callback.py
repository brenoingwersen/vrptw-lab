from loguru import logger
from ortools.sat.python import cp_model


class Callback(cp_model.CpSolverSolutionCallback):
    """
    Callback class that tracks and logs CP-SAT search progress for one solve stage.
    """

    def __init__(self, stage: str = "search"):
        """Initialize callback state for a named solve stage.

        Args:
            stage: Short label used in log messages to identify the stage.
        """
        super().__init__()
        self._stage = stage
        self._solutions_found = 0
        self._first_objective: int | None = None
        self._best_objective: int | None = None

    def on_solution_callback(self) -> None:
        """Track each improving solution for the stage summary.

        Called automatically by OR-Tools during search.
        """
        self._solutions_found += 1
        objective = int(self.objective_value)
        if self._first_objective is None:
            self._first_objective = objective
        self._best_objective = objective

    def log_summary(self) -> None:
        """Log a one-line search summary at INFO level.

        Emits a warning when no incumbent was found during the stage.
        """
        if self._solutions_found == 0:
            logger.warning(f"{self._stage} search: no improving solutions found")
            return

        logger.info(
            f"{self._stage} search: {self._solutions_found} improving solutions, "
            f"objective {self._first_objective:,} → {self._best_objective:,}"
        )
