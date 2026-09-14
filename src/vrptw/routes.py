"""Pure route decomposition utilities for selected arcs."""

from collections.abc import Iterator

import numpy as np

from vrptw.instance import VRPTWInstance


def count_trucks(selected_arcs: np.ndarray) -> int:
    """Return the number of trucks (depot-leaving arcs) in a solution.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

    Return:
        Count of arcs whose origin node is the depot (index ``0``).
    """
    if selected_arcs.size == 0:
        return 0
    return int(np.sum(selected_arcs[:, 0] == 0))


def total_distance(selected_arcs: np.ndarray, instance: VRPTWInstance) -> int:
    """Return total travel distance across all selected arcs.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.
        instance: Source problem instance.

    Return:
        Sum of Euclidean distances for each arc in ``selected_arcs``.
    """
    if selected_arcs.size == 0:
        return 0
    return sum(
        instance.travel_time(int(i), int(j)) for i, j in selected_arcs
    )


def _arc_by_from(selected_arcs: np.ndarray) -> dict[int, tuple[int, int]]:
    return dict(zip(selected_arcs[:, 0], map(tuple, selected_arcs)))


def iter_circuits(
    selected_arcs: np.ndarray,
) -> Iterator[list[tuple[int, int]]]:
    """Iterate over truck circuits extracted from selected arcs.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

    Return:
        Iterator of circuits, each a list of ``(from_node, to_node)`` tuples.
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
