"""Solver run outcome types."""

from dataclasses import dataclass

from vrptw.solution import VRPTWSolution


@dataclass(frozen=True)
class SolveResult:
    """Outcome of a solver run.

    ``solution`` is always present; on infeasible or timeout runs it contains
    empty arcs. Metric fields may be ``None`` when not applicable.

    Attributes:
        status: OR-Tools solver status code.
        status_name: Human-readable solver status name.
        solution: Extracted route structure from the solve.
        n_trucks: Number of trucks used, or ``None`` when infeasible.
        total_distance: Total route distance, or ``None`` when not computed.
        runtime_seconds: Wall-clock solve time in seconds.
    """

    status: int
    status_name: str
    solution: VRPTWSolution
    n_trucks: int | None = None
    total_distance: int | None = None
    runtime_seconds: float | None = None
