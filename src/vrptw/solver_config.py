"""CP-SAT solver configuration for VRPTW runs."""

from typing import Literal

from pydantic import BaseModel, Field

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "SUCCESS"]


class SolverConfig(BaseModel):
    """CP-SAT engine settings for a solver run.

    Problem parameters (``max_trucks``, ``truck_capacity``) belong on
    ``VRPTWProblem``.

    Attributes:
        random_seed: CP-SAT random seed.
        max_time_in_seconds: Optional wall-clock solve time limit.
        log_level: Minimum log level for solver output.
    """

    random_seed: int = Field(default=42)
    max_time_in_seconds: float | None = Field(default=None, gt=0)
    log_level: LogLevel = Field(default="INFO")
