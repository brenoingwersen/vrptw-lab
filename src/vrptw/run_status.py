from enum import StrEnum

from ortools.sat.python import cp_model


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    FEASIBLE = "feasible"
    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    TIMEOUT = "timeout"

    @property
    def is_finished(self) -> bool:
        return self in [self.FEASIBLE, self.OPTIMAL, self.INFEASIBLE, self.TIMEOUT]


def from_cp_status(status: int) -> RunStatus:
    """
    Return a ``RunStatus`` enum value for the given OR-Tools CP status code.

    Args:
        status: OR-Tools CP status code.

    Returns:
        ``RunStatus`` enum value.

    Raises:
        ValueError: If the status code is invalid.
    """
    match status:
        case cp_model.FEASIBLE:
            return RunStatus.FEASIBLE
        case cp_model.OPTIMAL:
            return RunStatus.OPTIMAL
        case cp_model.INFEASIBLE:
            return RunStatus.INFEASIBLE
        case cp_model.UNKNOWN:
            return RunStatus.TIMEOUT
        case _:
            raise ValueError(f"Invalid CP status: {status}")
