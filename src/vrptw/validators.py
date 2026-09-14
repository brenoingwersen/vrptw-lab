"""Post-solve validation for selected arcs."""

import numpy as np

from vrptw.instance import VRPTWInstance
from vrptw.problem import VRPTWProblem
from vrptw.routes import iter_circuits


def validate_depot_balance(selected_arcs: np.ndarray) -> None:
    """Validate that depot leaving and returning arc counts match.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

    Raises:
        ValueError: If the number of arcs leaving the depot differs from
            the number returning to it.
    """
    if selected_arcs.size == 0:
        return

    n_leaving = int(np.sum(selected_arcs[:, 0] == 0))
    n_returning = int(np.sum(selected_arcs[:, 1] == 0))
    if n_leaving != n_returning:
        raise ValueError(
            f"Depot arc imbalance: {n_leaving} departures vs {n_returning} arrivals."
        )


def validate_circuit_load(
    selected_arcs: np.ndarray,
    instance: VRPTWInstance,
    truck_capacity: int,
) -> None:
    """Validate each circuit load is within truck capacity.

    Args:
        selected_arcs: Selected route arcs.
        instance: Source problem instance.
        truck_capacity: Maximum load per truck.

    Raises:
        ValueError: If any circuit exceeds ``truck_capacity``.
    """
    for truck_id, circuit in enumerate(iter_circuits(selected_arcs), start=1):
        nodes = {arc[1] for arc in circuit if arc[1] != 0}
        load = int(instance.demand[list(nodes)].sum())
        if load > truck_capacity:
            raise ValueError(
                f"Truck {truck_id} load ({load}) exceeds "
                f"truck_capacity ({truck_capacity})."
            )


def validate_circuit_time_windows(
    selected_arcs: np.ndarray,
    instance: VRPTWInstance,
) -> None:
    """Validate time windows along each circuit.

    Args:
        selected_arcs: Selected route arcs.
        instance: Source problem instance.

    Raises:
        ValueError: If any node is served outside its time window.
    """
    for truck_id, circuit in enumerate(iter_circuits(selected_arcs), start=1):
        current_time = 0
        for node_from, node_to in circuit:
            if node_to == 0:
                continue

            arrival = (
                current_time
                + instance.service_time[node_from]
                + instance.travel_time(node_from, node_to)
            )
            start_time = max(arrival, int(instance.ready_time[node_to]))
            if start_time > int(instance.due_date[node_to]):
                raise ValueError(
                    f"Truck {truck_id}: node {node_to} start time ({start_time}) "
                    f"exceeds due_date ({int(instance.due_date[node_to])})."
                )
            current_time = start_time


def validate_solution(
    selected_arcs: np.ndarray,
    problem: VRPTWProblem,
) -> None:
    """Run all post-solve validations on selected arcs.

    Args:
        selected_arcs: Selected route arcs.
        problem: VRPTW problem definition used for the run.

    Raises:
        ValueError: If any validation check fails.
    """
    validate_depot_balance(selected_arcs)
    validate_circuit_load(
        selected_arcs, problem.instance, problem.truck_capacity
    )
    validate_circuit_time_windows(selected_arcs, problem.instance)
