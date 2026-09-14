"""DataFrame output for VRPTW solutions."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from vrptw.instance import VRPTWInstance
from vrptw.routes import iter_circuits


@dataclass(frozen=True)
class VRPTWSolution:
    """Selected arcs from a solver run.

    Attributes:
        selected_arcs: 2D array of ``(from_node, to_node)`` indices for chosen arcs.
    """

    selected_arcs: np.ndarray

    @classmethod
    def empty(cls) -> "VRPTWSolution":
        """Create an empty solution for infeasible or timed-out runs.

        Return:
            A ``VRPTWSolution`` with no selected arcs.
        """
        return cls(np.empty((0, 2), dtype=np.int32))

    def to_stops_df(self, instance: VRPTWInstance) -> pd.DataFrame:
        """Build a per-truck stop sequence DataFrame.

        Args:
            instance: Source problem instance.

        Return:
            DataFrame with columns ``truck_id``, ``sequence``, ``cust_no_from``
            and ``cust_no_to`` for each stop in every truck route.
        """
        return build_stops_df(instance, self.selected_arcs)


def build_stops_df(
    instance: VRPTWInstance, selected_arcs: np.ndarray
) -> pd.DataFrame:
    """Build a per-truck stop sequence DataFrame.

    Args:
        instance: Source problem instance.
        selected_arcs: Selected route arcs.

    Return:
        DataFrame with columns ``truck_id``, ``sequence``, ``cust_no_from``
        and ``cust_no_to`` for each stop in every truck route.
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
