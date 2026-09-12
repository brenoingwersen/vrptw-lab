"""Route extraction and validation from CP-SAT solutions."""

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

from vrptw.instance import VRPTWInstance


class VRPTWSolution:
    """Route structure extracted from a CP-SAT solve.

    Built via ``from_cp_solver`` after a feasible run, or ``empty`` on failure.

    Attributes:
        instance: Source problem instance.
        selected_arcs: 2D array of ``(from_node, to_node)`` indices for chosen arcs.
        cust_no: Customer numbers aligned with node indices in ``instance``.
    """

    def __init__(self, instance: VRPTWInstance, selected_arcs: np.ndarray):
        """Initialize a solution and validate depot arc balance.

        Args:
            instance: Source problem instance.
            selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

        Raises:
            ValueError: If depot leaving and returning arc counts differ.
        """
        self.instance = instance
        self.validate_selected_arcs(selected_arcs)
        self.selected_arcs = selected_arcs
        self.cust_no = instance.cust_no

    @classmethod
    def from_cp_solver(
        cls,
        instance: VRPTWInstance,
        cp_solver: cp_model.CpSolver,
        arc_vars: np.ndarray,
    ) -> "VRPTWSolution":
        """Build a solution from a completed CP-SAT solve.

        Args:
            instance: Source problem instance.
            cp_solver: Solver with a feasible or optimal assignment.
            arc_vars: Boolean arc decision variables aligned with ``instance.arcs``.

        Return:
            A ``VRPTWSolution`` with arcs whose variables are true in ``cp_solver``.
        """
        mask = np.array([cp_solver.value(v) for v in arc_vars], dtype=bool)
        selected_arcs = instance.arcs[mask].copy()
        return cls(instance, selected_arcs)

    @classmethod
    def empty(cls, instance: VRPTWInstance) -> "VRPTWSolution":
        """Create an empty solution for infeasible or timed-out runs.

        Args:
            instance: Source problem instance.

        Return:
            A ``VRPTWSolution`` with no selected arcs.
        """
        return cls(instance, np.empty((0, 2), dtype=np.int32))

    @property
    def n_trucks(self) -> int:
        """Return the number of trucks (depot-leaving arcs) in the solution.

        Return:
            Count of arcs whose origin node is the depot (index ``0``).
        """
        return int(np.sum(self.selected_arcs[:, 0] == 0))

    @staticmethod
    def validate_selected_arcs(selected_arcs: np.ndarray) -> None:
        """Validate that depot leaving and returning arc counts match.

        Args:
            selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

        Raises:
            ValueError: If the number of arcs leaving the depot differs from
                the number returning to it.
        """
        leaving_depot_arcs = selected_arcs[selected_arcs[:, 0] == 0]
        returning_depot_arcs = selected_arcs[selected_arcs[:, 1] == 0]
        if len(leaving_depot_arcs) != len(returning_depot_arcs):
            raise ValueError(
                "The selected arcs have different amounts of arcs leaving and returning to the depot."
            )

    def build_stops_df(self) -> pd.DataFrame:
        """Build a per-truck stop sequence DataFrame.

        Return:
            DataFrame with columns ``truck_id``, ``sequence``, ``cust_no_from``,
            and ``cust_no_to`` for each arc in every route.
        """
        leaving_depot_arcs = self.selected_arcs[self.selected_arcs[:, 0] == 0]

        arc_by_from = dict(
            zip(self.selected_arcs[:, 0], map(tuple, self.selected_arcs))
        )

        rows = []
        for truck_id, (from_node, to_node) in enumerate(leaving_depot_arcs, start=1):
            sequence = 1
            while True:
                rows.append(
                    {
                        "truck_id": truck_id,
                        "sequence": sequence,
                        "cust_no_from": self.cust_no[from_node],
                        "cust_no_to": self.cust_no[to_node],
                    }
                )
                if to_node == 0:
                    break
                from_node, to_node = arc_by_from[to_node]
                sequence += 1

        return pd.DataFrame(rows)
