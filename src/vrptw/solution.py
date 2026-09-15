"""Solution representation and tabular export for VRPTW routes.

This module holds the **output shape** of a solve: which arcs were selected.
It does not run the solver, validate feasibility, or compute aggregate
metrics— those live in ``solver``, ``validators``, and ``routes``.

Separation of concerns:

    * ``VRPTWSolution`` — lightweight container for selected arcs.
    * ``build_stops_df`` — human-readable per-truck stop sequences.
    * ``routes`` — truck counting, distance totals, circuit decomposition.
    * ``SolveResult`` — solver status and summary metrics around a solution.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from vrptw.instance import VRPTWInstance
from vrptw.routes import iter_circuits


@dataclass(frozen=True)
class VRPTWSolution:
    """Selected arcs from a solver run.

    A solution is fully described by the set of active directed arcs. Higher-
    level views (truck routes, stop tables, distance totals) are derived from
    this representation via ``routes`` and ``build_stops_df``.

    Attributes:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with
            ``(from_node, to_node)`` indices for each chosen arc.
    """

    selected_arcs: np.ndarray

    @classmethod
    def empty(cls) -> "VRPTWSolution":
        """Create an empty solution for infeasible or timed-out runs.

        Returns:
            A ``VRPTWSolution`` with no selected arcs.
        """
        return cls(np.empty((0, 2), dtype=np.int32))

    def to_stops(self, instance: VRPTWInstance) -> list[dict[str, Any]]:
        """
        Convert the solution to a list of stops.
        """
        rows = []
        for truck_id, circuit in enumerate(iter_circuits(self.selected_arcs), start=1):
            for sequence, arc in enumerate(circuit, start=1):
                rows.append(
                    {
                        "truck_id": truck_id,
                        "sequence": sequence,
                        "cust_no_from": instance.cust_no[arc[0]],
                        "cust_no_to": instance.cust_no[arc[1]],
                    }
                )
        return rows

    def to_stops_df(self, instance: VRPTWInstance) -> pd.DataFrame:
        """Build a per-truck stop sequence DataFrame.

        Delegates to ``build_stops_df`` using this solution's arcs.

        Args:
            instance: Source problem instance for external customer numbers.

        Returns:
            DataFrame with columns ``truck_id``, ``sequence``, ``cust_no_from``,
            and ``cust_no_to`` for each stop in every truck route.
        """
        return build_stops_df(instance, self.selected_arcs)


def build_stops_df(instance: VRPTWInstance, selected_arcs: np.ndarray) -> pd.DataFrame:
    """Build a per-truck stop sequence DataFrame from selected arcs.

    Walks each depot-to-depot circuit (see ``routes.iter_circuits``) and
    emits one row per arc with truck id, visit order, and external customer
    numbers.

    Args:
        instance: Source problem instance.
        selected_arcs: Selected route arcs from a feasible solution.

    Returns:
        DataFrame with columns ``truck_id``, ``sequence``, ``cust_no_from``,
        and ``cust_no_to``.
    """
    rows = []
    for truck_id, circuit in enumerate(iter_circuits(selected_arcs), start=1):
        for sequence, arc in enumerate(circuit, start=1):
            rows.append(
                {
                    "truck_id": truck_id,
                    "sequence": sequence,
                    "cust_no_from": instance.cust_no[arc[0]],
                    "cust_no_to": instance.cust_no[arc[1]],
                }
            )

    return pd.DataFrame(rows)
