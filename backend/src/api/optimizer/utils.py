from collections.abc import Iterator

import numpy as np

from api.optimizer.instance import ProblemInstance
from api.schemas import SolutionArcSchema


def count_trucks(selected_arcs: np.ndarray) -> int:
    """Return the number of trucks (depot-leaving arcs) in a solution.

    Each truck route starts with exactly one arc leaving the depot (node ``0``),
    so counting those arcs equals the fleet size.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

    Returns:
        Count of arcs whose origin node is the depot (index ``0``).
    """
    if selected_arcs.size == 0:
        return 0
    return int(np.sum(selected_arcs[:, 0] == 0))


def total_distance(selected_arcs: np.ndarray, instance: ProblemInstance) -> int:
    """Return total travel distance across all selected arcs.

    Uses ``VRPTWInstance.travel_time`` so distance matches the model objective.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.
        instance: Source problem instance for arc cost lookup.

    Returns:
        Sum of Euclidean distances for each arc in ``selected_arcs``.
    """
    if selected_arcs.size == 0:
        return 0
    return sum(instance.travel_time(int(i), int(j)) for i, j in selected_arcs)


def _arc_by_from(selected_arcs: np.ndarray) -> dict[int, tuple[int, int]]:
    """Build a lookup from origin node to outgoing arc."""
    return dict(zip(selected_arcs[:, 0], map(tuple, selected_arcs)))


def iter_circuits(
    selected_arcs: np.ndarray,
) -> Iterator[list[tuple[int, int]]]:
    """Iterate over truck circuits extracted from selected arcs.

    Each circuit is a depot-to-depot path: starts at an arc leaving node ``0``,
    follows selected arcs by matching ``arc[1]`` to the next arc's origin,
    and ends when the route returns to the depot.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

    Yields:
        Lists of ``(from_node, to_node)`` tuples, one list per truck route.
    """
    if selected_arcs.size == 0:
        return

    arc_lookup = _arc_by_from(selected_arcs)
    leaving_depot = selected_arcs[selected_arcs[:, 0] == 0]

    for start_arc in leaving_depot:
        circuit = [tuple(start_arc)]
        arc = start_arc
        while arc[1] != 0:
            arc = arc_lookup[arc[1]]
            circuit.append(tuple(arc))
        yield circuit


def to_route_arcs(
    selected_arcs: np.ndarray, instance: ProblemInstance
) -> list[SolutionArcSchema]:
    """
    Convert the selected arcs to a list of route arcs.
    """
    route_arcs: list[SolutionArcSchema] = []
    for truck_id, circuit in enumerate(iter_circuits(selected_arcs), start=1):
        for sequence, arc in enumerate(circuit, start=1):
            route_arcs.append(
                SolutionArcSchema(
                    truck_id=truck_id,
                    sequence=sequence,
                    cust_no_from=instance.cust_no[arc[0]],
                    cust_no_to=instance.cust_no[arc[1]],
                )
            )

    return route_arcs
