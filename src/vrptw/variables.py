from collections.abc import Iterator

import numpy as np
from loguru import logger
from ortools.sat.python import cp_model

from vrptw.problem import VRPTWProblem


class VRPTWVariables:
    """CP-SAT variables container for the VRPTW problem."""

    def __init__(
        self,
        problem: VRPTWProblem,
        model: cp_model.CpModel,
    ):
        instance = problem.instance
        self._instance = instance
        self._node_idx = np.arange(instance.n_nodes, dtype=np.int32)
        self._arcs = self._create_arcs(instance.n_nodes)

        logger.info("Creating the model variables...")
        logger.info("Creating the arc variables...")
        self._arc_vars = np.array(
            [model.new_bool_var(f"arc_{i}_{j}") for i, j in self._arcs],
            dtype=object,
        )
        logger.info("Creating the node load variables...")
        self._node_load_vars = np.array(
            [
                model.new_int_var(0, problem.truck_capacity, f"load_{idx}")
                for idx in self._node_idx
            ]
        )
        logger.info("Creating the node start time variables...")
        self._node_start_time_vars = np.array(
            [
                model.new_int_var(
                    instance.ready_time[idx],
                    instance.due_date[idx],
                    f"service_start_time_{idx}",
                )
                for idx in self._node_idx
            ]
        )

    @property
    def arcs(self) -> np.ndarray:
        """Return the arcs."""
        return self._arcs

    @staticmethod
    def _create_arcs(n_nodes: int) -> np.ndarray:
        """
        Create the arcs for the VRPTW problem
        and filter out self-loops.

        Args:
            n_nodes: The number of nodes in the problem.

        Returns:
            A 2D array of shape (n_arcs, 2) containing the arcs.
        """
        node_idx = np.arange(n_nodes, dtype=np.int32)

        arc_from = np.repeat(node_idx, n_nodes)
        arc_to = np.tile(node_idx, n_nodes)

        mask = arc_from != arc_to

        return np.column_stack((arc_from[mask], arc_to[mask]))

    @property
    def arc_vars(self) -> np.ndarray:
        """Return the arc decision variables."""
        return self._arc_vars

    @property
    def node_load_vars(self) -> np.ndarray:
        """Return the node load decision variables."""
        return self._node_load_vars

    @property
    def node_start_time_vars(self) -> np.ndarray:
        """Return the node start time decision variables."""
        return self._node_start_time_vars

    @property
    def arcs_leaving_depot(self) -> np.ndarray:
        """Return the arc variables leaving the depot."""
        return self._arc_vars[self._arcs[:, 0] == self._node_idx[0]]

    @property
    def arc_distance(self) -> np.ndarray:
        """Return Euclidean distance for each arc, aligned with ``arcs``."""
        from_idx = self._arcs[:, 0]
        to_idx = self._arcs[:, 1]
        return np.array(
            [
                self._instance.travel_time(int(i), int(j))
                for i, j in zip(from_idx, to_idx)
            ],
            dtype=np.int32,
        )

    @property
    def arc_travel_time(self) -> np.ndarray:
        """Return travel time for each arc, aligned with ``arcs``."""
        return self.arc_distance

    def iter_arcs(
        self,
    ) -> Iterator[tuple[tuple[int, int], cp_model.IntVar]]:
        """Iterate over the arc decision variables.

        Return:
            Iterator of tuples of ``(from, to)`` ``node_idx`` pairs and
            ``cp_model.IntVar`` decision variables.
        """
        for arc, v in zip(self.arcs, self.arc_vars):
            yield (int(arc[0]), int(arc[1])), v

    def get_selected_arcs(self, cp_solver: cp_model.CpSolver) -> np.ndarray:
        """Return the selected arcs from the solver results."""
        mask = np.array([cp_solver.value(v) for v in self.arc_vars], dtype=bool)
        if not np.any(mask):
            return np.empty((0, 2), dtype=np.int32)
        return self.arcs[mask].copy()

    def iter_load_arcs(
        self,
    ) -> Iterator[
        tuple[int, int, cp_model.IntVar, cp_model.IntVar, cp_model.IntVar, int]
    ]:
        """Iterate over arcs with load-related variables and demand.

        Return:
            Iterator of ``(node_from, node_to, load_from, load_to, arc_var, demand)``.
        """
        for (node_from, node_to), arc_var in self.iter_arcs():
            yield (
                node_from,
                node_to,
                self.node_load_vars[node_from],
                self.node_load_vars[node_to],
                arc_var,
                int(self._instance.demand[node_to]),
            )

    def iter_start_time_arcs(
        self,
    ) -> Iterator[
        tuple[int, int, cp_model.IntVar, cp_model.IntVar, cp_model.IntVar, int]
    ]:
        """Iterate over arcs with start-time variables and travel time.

        Return:
            Iterator of ``(node_from, node_to, start_from, start_to, arc_var, travel_time)``.
        """
        travel_times = self.arc_travel_time
        for idx, ((node_from, node_to), arc_var) in enumerate(self.iter_arcs()):
            yield (
                node_from,
                node_to,
                self.node_start_time_vars[node_from],
                self.node_start_time_vars[node_to],
                arc_var,
                int(travel_times[idx]),
            )
