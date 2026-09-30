import pytest
import numpy as np

from api.optimizer.validators import validate_depot_balance


def test_validate_depot_balance():
    """
    Test that the depot balance is validated correctly.
    """
    selected_arcs = np.array(
        [
            [0, 1],
            [1, 0],
            [0, 2],
            [2, 3],
            [3, 0],
        ]
    )
    validate_depot_balance(selected_arcs)

    selected_arcs_invalid = np.array(
        [
            [0, 1],
            [1, 0],
            [0, 2],
        ]
    )
    with pytest.raises(ValueError):
        validate_depot_balance(selected_arcs_invalid)
