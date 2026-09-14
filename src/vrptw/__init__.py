"""Public API for the VRPTW (Vehicle Routing Problem with Time Windows) package.

This package solves VRPTW instances with Google OR-Tools CP-SAT using a
two-stage lexicographic objective: first minimize fleet size, then minimize
total route distance while keeping the fleet count fixed.

Architecture overview:

    VRPTWInstance  →  raw node data (coordinates, demand, time windows)
    VRPTWProblem   →  instance + fleet parameters (capacity, max trucks)
    VRPTWSolver    →  builds the CP-SAT model, runs the two-stage solve
    SolveResult    →  status, metrics, and extracted routes
    VRPTWSolution  →  selected arcs and tabular export helpers

Supporting modules stay deliberately narrow:

    ``variables``   — decision variables only; no constraints or objectives
    ``routes``      — pure route geometry on selected arcs; no solver state
    ``validators``  — post-solve feasibility checks; no model building
    ``solver_config`` — engine tuning; problem parameters live on ``VRPTWProblem``
    ``callback``    — search-progress hooks for CP-SAT
    ``log``           — structured logging for solver stages
"""

from vrptw.callback import VRPTWCallback
from vrptw.instance import VRPTWInstance
from vrptw.problem import VRPTWProblem
from vrptw.result import SolveResult
from vrptw.solution import VRPTWSolution, build_stops_df
from vrptw.solver import VRPTWSolver
from vrptw.solver_config import SolverConfig
from vrptw.validators import validate_solution

__all__ = [
    "SolveResult",
    "SolverConfig",
    "VRPTWCallback",
    "VRPTWInstance",
    "VRPTWProblem",
    "VRPTWSolution",
    "VRPTWSolver",
    "build_stops_df",
    "validate_solution",
]
