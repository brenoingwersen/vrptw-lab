"""Solver run outcome types.

This module defines the structured result returned by ``VRPTWSolver.solve``.
It captures solver status and summary metrics alongside the route data, but
does not perform validation or formatting— those happen before construction
(in ``solver`` and ``validators``) or via ``VRPTWSolution.to_stops_df``.

Separation of concerns:

    * ``SolveResult`` — immutable envelope: status, metrics, ``VRPTWSolution``.
    * ``VRPTWSolution`` — selected arcs only.
    * ``VRPTWSolver`` — produces ``SolveResult`` after each stage and at the end.
"""

from dataclasses import dataclass

from vrptw.solution import VRPTWSolution


@dataclass(frozen=True)
class SolveResult:
    """Outcome of a solver run (one stage or the combined two-stage solve).

    ``solution`` is always present. On infeasible or timeout runs it contains
    empty arcs; metric fields may be ``None`` when they were not computed.

    Attributes:
        status: OR-Tools solver status code (e.g. ``OPTIMAL``, ``FEASIBLE``).
        status_name: Human-readable solver status name.
        solution: Extracted route structure from the solve.
        n_trucks: Number of trucks used, or ``None`` when infeasible.
        total_distance: Sum of arc distances, or ``None`` when not computed.
        runtime_seconds: Wall-clock solve time in seconds for this result's scope.
    """

    status: int
    status_name: str
    solution: VRPTWSolution
    n_trucks: int | None = None
    total_distance: int | None = None
    runtime_seconds: float | None = None
