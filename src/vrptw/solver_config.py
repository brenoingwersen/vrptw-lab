"""CP-SAT solver configuration for VRPTW runs."""

from pydantic import BaseModel, Field


class SolverConfig(BaseModel):
    """CP-SAT engine settings for a solver run.

    Problem parameters (``max_trucks``, ``truck_capacity``) belong on
    ``VRPTWProblem``.

    Attributes:
        random_seed: CP-SAT random seed.
        max_time_in_seconds: Optional wall-clock solve time limit.
    """

    random_seed: int = Field(default=42)
    max_time_in_seconds: float | None = Field(default=None, gt=0)
