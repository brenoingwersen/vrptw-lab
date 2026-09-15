"""Post-solve validation for selected arcs.

Validators re-check feasibility **independently of the CP-SAT model**. They
simulate routes from the extracted arc list and raise ``ValueError`` on
violations. This catches modeling bugs, numerical edge cases, or corrupted
solution data before results are returned or exported.

Separation of concerns:

    * ``VRPTWSolver`` — builds constraints and trusts OR-Tools, then calls
      ``validate_solution`` as a safety net on feasible runs.
    * ``validators`` — standalone checks usable in tests or notebooks.
    * ``routes`` — circuit decomposition shared by validators and export code.

Each function validates one aspect (depot balance, capacity, time windows).
``validate_solution`` runs all checks in sequence.
"""

import numpy as np

from optimizer.instance import ProblemInstance
from optimizer.utils import iter_circuits


def validate_depot_balance(selected_arcs: np.ndarray) -> None:
    """Validate that depot leaving and returning arc counts match.

    Every truck must depart from and return to the depot, so the number of
    arcs leaving node ``0`` must equal the number entering node ``0``.

    Args:
        selected_arcs: 2D array of shape ``(n_selected, 2)`` with node indices.

    Raises:
        ValueError: If departure and arrival counts at the depot differ.
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
    instance: ProblemInstance,
    truck_capacity: int,
) -> None:
    """Validate each circuit's total demand is within truck capacity.

    Sums customer demand for all non-depot nodes visited on each truck route.

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
    instance: ProblemInstance,
) -> None:
    """Validate time windows along each circuit by forward simulation.

    Tracks clock time along the route: travel plus service at each stop,
    waiting until ``ready_time`` if arriving early, and failing if service
    would start after ``due_date``.

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
    instance: ProblemInstance,
) -> None:
    """Run all post-solve validations on selected arcs.

    Args:
        selected_arcs: Selected route arcs from a solver run.
        instance: Problem instance used for capacity and instance data.

    Raises:
        ValueError: If any validation check fails.
    """
    validate_depot_balance(selected_arcs)
    validate_circuit_load(
        selected_arcs, instance, instance.constraints_config.truck_capacity
    )
    validate_circuit_time_windows(selected_arcs, instance)
