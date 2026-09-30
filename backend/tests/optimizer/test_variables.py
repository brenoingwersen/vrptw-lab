import pytest
import numpy as np
from api.optimizer.variables import Variables


@pytest.mark.parametrize(
    ["n_nodes", "expected_arcs"],
    [
        pytest.param(3, np.array([[0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]])),
        pytest.param(0, np.empty((0, 2))),
    ],
)
def test_create_arcs(n_nodes: int, expected_arcs: np.ndarray):
    assert np.array_equal(Variables._create_arcs(n_nodes), expected_arcs)
