"""CP-SAT decision variables for the VRPTW model.

This module creates and indexes OR-Tools variables. It does **not** add
constraints, set objectives, or run the solver— those responsibilities belong
to ``VRPTWSolver``.

Separation of concerns:

    * ``VRPTWVariables`` — variable creation, arc indexing, and solution extraction.
    * ``VRPTWSolver`` — constraint posting and two-stage optimization.
    * ``routes`` — pure functions over selected arcs after a solve.

The three variable families mirror the VRPTW structure:

    * **Arc booleans** — which directed edges are used in the solution.
    * **Node loads** — cumulative demand when a truck arrives at each node.
    * **Start times** — when service begins at each node (bounded by time windows).
"""

from collections.abc import Iterator

import numpy as np
from loguru import logger
from ortools.sat.python import cp_model

from vrptw.problem import VRPTWProblem


class VRPTWVariables:
    """Container for all CP-SAT decision variables in a VRPTW model.

    Builds arc, load, and start-time variables from a ``VRPTWProblem`` and
    exposes iterators that pair variables with the data needed to post
    constraints. Keeping variable creation isolated makes the solver's
    constraint methods read as declarative recipes rather than low-level
    OR-Tools boilerplate.

    Attributes:
        arcs: Directed edges ``(from, to)`` with self-loops removed.
        arc_vars: Boolean variable per arc indicating selection.
        node_load_vars: Integer load variable per node, capped by truck capacity.
        node_start_time_vars: Integer service-start variable per node, bounded
            by that node's time window.
        arcs_leaving_depot: Boolean arc variables whose origin is the depot.
        arc_distance: Precomputed Euclidean distance per arc, aligned with ``arcs``.
        arc_travel_time: Alias of ``arc_distance`` (travel time = distance here).
    """

    def __init__(
        self,
        problem: VRPTWProblem,
        model: cp_model.CpModel,
    ):
        """Create all decision variables for a VRPTW CP-SAT model.

        Args:
            problem: Complete problem definition (instance + fleet parameters).
            model: Empty or partially built CP-SAT model to receive variables.
        """
        instance = problem.instance
        self._instance = instance
        self._node_idx = np.arange(instance.n_nodes, dtype=np.int32)
        self._arcs = self._create_arcs(instance.n_nodes)

        logger.debug("Creating the model variables...")
        logger.debug("Creating the arc variables...")
        self._arc_vars = np.array(
            [model.new_bool_var(f"arc_{i}_{j}") for i, j in self._arcs],
            dtype=object,
        )
        logger.debug("Creating the node load variables...")
        self._node_load_vars = np.array(
            [
                model.new_int_var(0, problem.truck_capacity, f"load_{idx}")
                for idx in self._node_idx
            ]
        )
        logger.debug("Creating the node start time variables...")
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
        logger.info(
            f"Model variables created: nodes={instance.n_nodes}, "
            f"arcs={len(self._arcs)}"
        )

    @property
    def arcs(self) -> np.ndarray:
        """Return the arc index pairs ``(from, to)``.

        Returns:
            2D array of shape ``(n_arcs, 2)`` with depot at index ``0``.
        """
        return self._arcs

    @staticmethod
    def _create_arcs(n_nodes: int) -> np.ndarray:
        """Build all directed arcs and remove self-loops.

        Args:
            n_nodes: Number of nodes in the instance.

        Returns:
            2D array of shape ``(n_arcs, 2)`` containing ``(from, to)`` pairs.
        """
        node_idx = np.arange(n_nodes, dtype=np.int32)

        arc_from = np.repeat(node_idx, n_nodes)
        arc_to = np.tile(node_idx, n_nodes)

        mask = arc_from != arc_to

        return np.column_stack((arc_from[mask], arc_to[mask]))

    @property
    def arc_vars(self) -> np.ndarray:
        """Return the arc decision variables.

        Returns:
            1D array of ``cp_model.IntVar`` booleans, aligned with ``arcs``.
        """
        return self._arc_vars

    @property
    def node_load_vars(self) -> np.ndarray:
        """Return the per-node cumulative load variables.

        Returns:
            1D array indexed by node, with ``load[0] == 0`` at the depot.
        """
        return self._node_load_vars

    @property
    def node_start_time_vars(self) -> np.ndarray:
        """Return the per-node service start-time variables.

        Returns:
            1D array indexed by node, each bounded by ``ready_time`` and
            ``due_date`` from the instance.
        """
        return self._node_start_time_vars

    @property
    def arcs_leaving_depot(self) -> np.ndarray:
        """Return arc variables whose origin is the depot.

        The count of active depot-leaving arcs equals the number of trucks
        used in a feasible solution.

        Returns:
            1D array of boolean arc variables leaving node ``0``.
        """
        return self._arc_vars[self._arcs[:, 0] == self._node_idx[0]]

    @property
    def arc_distance(self) -> np.ndarray:
        """Return Euclidean distance for each arc, aligned with ``arcs``.

        Returns:
            1D integer array of arc distances in the same order as ``arcs``.
        """
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
        """Return travel time for each arc, aligned with ``arcs``.

        In this model travel time equals Euclidean distance.

        Returns:
            1D integer array parallel to ``arcs``.
        """
        return self.arc_distance

    def iter_arcs(
        self,
    ) -> Iterator[tuple[tuple[int, int], cp_model.IntVar]]:
        """Iterate over arc index pairs and their decision variables.

        Yields:
            Tuples of ``((from, to), arc_var)`` for constraint posting.
        """
        for arc, v in zip(self.arcs, self.arc_vars):
            yield (int(arc[0]), int(arc[1])), v

    def get_selected_arcs(self, cp_solver: cp_model.CpSolver) -> np.ndarray:
        """Extract the arcs selected in a solver solution.

        Args:
            cp_solver: Solver instance that has finished a successful run.

        Returns:
            2D array of shape ``(n_selected, 2)`` with chosen ``(from, to)``
            pairs, or an empty array when no arc is active.
        """
        mask = np.array([cp_solver.value(v) for v in self.arc_vars], dtype=bool)
        if not np.any(mask):
            return np.empty((0, 2), dtype=np.int32)
        return self.arcs[mask].copy()

    def iter_load_arcs(
        self,
    ) -> Iterator[
        tuple[int, int, cp_model.IntVar, cp_model.IntVar, cp_model.IntVar, int]
    ]:
        """Iterate over arcs with the variables needed for load constraints.

        Each yield bundles origin, destination, load at both endpoints, the
        arc boolean, and the destination demand— everything required to post
        ``load[to] >= load[from] + demand`` when the arc is active.

        Yields:
            Tuples ``(node_from, node_to, load_from, load_to, arc_var, demand)``.
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
        """Iterate over arcs with the variables needed for time-window constraints.

        Each yield bundles service start times at both endpoints, the arc
        boolean, and travel time— everything required to enforce
        ``start[to] >= start[from] + service[from] + travel`` when the arc
        is active.

        Yields:
            Tuples ``(node_from, node_to, start_from, start_to, arc_var, travel_time)``.
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
