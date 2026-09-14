"""CP-SAT solver configuration for VRPTW runs.

This module holds **engine tuning** parameters: random seed, time limits, and
log verbosity. Problem semantics— how many trucks are allowed, how much each
can carry— belong on ``VRPTWProblem``, not here.

Separation of concerns:

    * ``VRPTWProblem`` — what is being optimized (data + fleet limits).
    * ``SolverConfig`` — how the CP-SAT engine behaves during the search.
    * ``VRPTWSolver`` — reads ``SolverConfig`` at construction and applies it
      before each ``CpSolver.solve`` call.
"""

from typing import Literal

from pydantic import BaseModel, Field

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS"]


class SolverConfig(BaseModel):
    """CP-SAT engine settings for a solver run.

    Keeps reproducibility and runtime controls separate from the mathematical
    problem definition. Pass an instance to ``VRPTWSolver`` to override defaults
    without changing fleet or instance data.

    Attributes:
        random_seed: CP-SAT random seed for reproducible search behavior.
        max_time_in_seconds: Optional wall-clock time limit per ``solve`` call.
            When ``None``, the solver runs until optimality or internal limits.
        log_level: Minimum log level for solver and library log output.
    """

    random_seed: int = Field(default=42)
    max_time_in_seconds: float | None = Field(default=None, gt=0)
    log_level: LogLevel = Field(default="INFO")
