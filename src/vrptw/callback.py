"""CP-SAT solver callbacks for the VRPTW model."""

from loguru import logger
from ortools.sat.python import cp_model


class VRPTWCallback(cp_model.CpSolverSolutionCallback):
    """Log intermediate solutions during CP-SAT search."""

    def __init__(self):
        super().__init__()

    def on_solution_callback(self):
        """Log the objective value when a new solution is found."""
        logger.info(f"Solution found with objective: {self.objective_value:,}")
