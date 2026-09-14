"""CP-SAT solver callbacks for the VRPTW model.

Callbacks hook into OR-Tools search events. This module observes improving
incumbent solutions and logs objective progress— it does **not** alter the
model, post constraints, or build results.

Separation of concerns:

    * ``VRPTWCallback`` — search telemetry during ``CpSolver.solve``.
    * ``log`` — structured stage headers and completion summaries.
    * ``VRPTWSolver`` — creates a callback per stage and calls ``log_summary``
      after each solve.
"""

from loguru import logger
from ortools.sat.python import cp_model


class VRPTWCallback(cp_model.CpSolverSolutionCallback):
    """Track and log CP-SAT search progress for one solve stage.

    OR-Tools invokes ``on_solution_callback`` whenever the solver finds a
    new incumbent. This class counts those events and records the first and
    best objective values seen, which helps compare stage-1 (truck count)
    and stage-2 (distance) search behavior in logs.

    Attributes:
        _stage: Label prefixed in log messages (e.g. ``"Stage 1"``).
        _solutions_found: Number of improving incumbents discovered.
        _first_objective: Objective value of the first incumbent, if any.
        _best_objective: Best (lowest) objective value seen so far.
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
        """Record each improving solution at DEBUG level.

        Called automatically by OR-Tools during search.
        """
        self._solutions_found += 1
        objective = int(self.objective_value)
        if self._first_objective is None:
            self._first_objective = objective
        self._best_objective = objective
        logger.debug(f"[{self._stage}] objective improved: {objective:,}")

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
