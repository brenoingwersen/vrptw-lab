import pytest
import numpy as np
from api.optimizer.utils import (
    _arc_by_from,
    iter_circuits,
    to_route_arcs,
    count_trucks,
    total_distance,
)
from api.schemas import SolutionArcSchema
from api.optimizer.instance import ProblemInstance, SolverConfig, ConstraintsConfig


_SELECTED_ARCS = np.array(
    [
        [0, 1],
        [1, 0],
        [0, 2],
        [2, 3],
        [3, 0],
    ]
)

_EXPECTED_CIRCUITS = [[(0, 1), (1, 0)], [(0, 2), (2, 3), (3, 0)]]

_SOLUTION_ARCS = [
    SolutionArcSchema(truck_id=1, sequence=1, cust_no_from=1, cust_no_to=2),
    SolutionArcSchema(truck_id=1, sequence=2, cust_no_from=2, cust_no_to=1),
    SolutionArcSchema(truck_id=2, sequence=1, cust_no_from=1, cust_no_to=3),
    SolutionArcSchema(truck_id=2, sequence=2, cust_no_from=3, cust_no_to=4),
    SolutionArcSchema(truck_id=2, sequence=3, cust_no_from=4, cust_no_to=1),
]

_INSTANCE = ProblemInstance(
    solver_config=SolverConfig(max_time_in_seconds=100, random_seed=42),
    constraints_config=ConstraintsConfig(max_trucks=2, truck_capacity=100),
    cust_no=np.array([1, 2, 3, 4]),
    xcoord=np.array([0, 1, 2, 3]),
    ycoord=np.array([0, 1, 2, 3]),
    demand=np.empty(4),
    ready_time=np.empty(4),
    due_date=np.empty(4),
    service_time=np.empty(4),
)


@pytest.mark.parametrize(
    ["selected_arcs", "expected_count"],
    [
        (_SELECTED_ARCS, 2),
        (np.empty(0), 0),
    ],
)
def test_count_trucks(selected_arcs: np.ndarray, expected_count: int):
    assert count_trucks(selected_arcs) == expected_count


@pytest.mark.parametrize(
    ["selected_arcs", "expected_distance"],
    [
        (_SELECTED_ARCS, 9),
        (np.empty(0), 0),
    ],
)
def test_total_distance(selected_arcs: np.ndarray, expected_distance: int):
    assert total_distance(selected_arcs, _INSTANCE) == pytest.approx(expected_distance)


def test_arc_from_by():
    arc_by_from = _arc_by_from(_SELECTED_ARCS)
    assert arc_by_from == {
        0: (0, 1),
        1: (1, 0),
        0: (0, 2),
        2: (2, 3),
        3: (3, 0),
    }


@pytest.mark.parametrize(
    ["selected_arcs", "expected_circuits"],
    [
        (_SELECTED_ARCS, _EXPECTED_CIRCUITS),
        (np.empty(0), []),
    ],
)
def test_iter_circuits(
    selected_arcs: np.ndarray, expected_circuits: list[list[tuple[int, int]]]
):
    assert list(iter_circuits(selected_arcs)) == expected_circuits


def test_to_route_arcs():
    assert to_route_arcs(_SELECTED_ARCS, _INSTANCE) == _SOLUTION_ARCS
