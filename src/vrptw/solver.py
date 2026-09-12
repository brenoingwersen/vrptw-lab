"""CP-SAT solver for fleet minimization with capacity constraints.

Stage 1 minimizes trucks (fleet + capacity). Stage 2 (distance minimization)
and time-window constraints are planned extension points.
"""

import time

import numpy as np
from loguru import logger
from ortools.sat.python import cp_model

from vrptw.callback import VRPTWCallback
from vrptw.instance import VRPTWInstance
from vrptw.result import SolveResult
from vrptw.solution import VRPTWSolution


class VRPTWSolver:
    """CP-SAT model builder and solve orchestrator.

    v1 solves capacity constraints and fleet (truck) minimization only.
    Time windows and distance objectives are extension points for later stages.

    Attributes:
        instance: Source problem instance.
        max_trucks: Upper bound on the number of trucks.
        truck_capacity: Maximum load per truck.
        model: OR-Tools CP-SAT model.
        cp_solver: Configured ``CpSolver`` instance.
        status: Solver status code from the last ``solve`` call, or ``None``.
    """

    def __init__(
        self,
        instance: VRPTWInstance,
        max_trucks: int = 20,
        truck_capacity: int = 200,
    ):
        """Initialize the solver and build the CP-SAT model.

        Args:
            instance: Problem instance to solve.
            max_trucks: Maximum number of trucks allowed.
            truck_capacity: Per-truck capacity limit.
        """
        self.instance = instance
        self.max_trucks = max_trucks
        self.truck_capacity = truck_capacity

        self.model = cp_model.CpModel()

        self._build_problem()

        self.cp_solver = cp_model.CpSolver()
        self.cp_solver.parameters.random_seed = 42
        self.status = None

    @property
    def is_feasible(self) -> bool:
        """Return whether the last solve found a feasible or optimal solution.

        Return:
            ``True`` when ``status`` is ``OPTIMAL`` or ``FEASIBLE``.
        """
        return self.status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    @property
    def status_name(self) -> str | None:
        """Return the human-readable name of the last solver status.

        Return:
            Status name string, or ``None`` if no solve has run yet.
        """
        if self.status is None:
            return None
        return self.cp_solver.status_name(self.status)

    @property
    def arcs_leaving_depot_vars(self) -> np.ndarray:
        """Return boolean arc variables for arcs leaving the depot.

        Return:
            1D array of arc decision variables whose origin is node ``0``.
        """
        arcs = self.instance.arcs
        mask_leaving_depot = arcs[:, 0] == 0
        return self.arc_vars[mask_leaving_depot]

    def _build_problem(self) -> None:
        """Build the CP-SAT model variables and constraints."""
        logger.info("Building the VRPTW problem...")
        self._add_variables()
        self._add_constraints()

    def _add_variables(self) -> None:
        """Add arc and node-load decision variables to ``model``."""
        logger.info("Adding the decision variables to the model...")
        self.arc_vars = np.array(
            [self.model.new_bool_var(f"arc_{n}") for n in self.instance.arcs]
        )
        self.node_load_vars = np.array(
            [
                self.model.new_int_var(0, self.truck_capacity, f"load_{idx}")
                for idx in range(self.instance.n_nodes)
            ]
        )
        logger.info(f"Arc variables: {self.arc_vars.shape}")
        logger.info(f"Node load variables: {self.node_load_vars.shape}")

    def _add_constraints(self) -> None:
        """Add circuit, fleet, and load constraints to ``model``."""
        logger.info("Adding constraints to the model...")
        self._add_circuit_constraint()
        self._add_max_trucks_constraint()
        self._add_load_constraint()
        # Future: self._add_time_window_constraints()

    def _add_circuit_constraint(self) -> None:
        """Ensure each node is visited, allowing multiple circuits (trucks).

        A single-circuit example: ``0 -> 1 -> 2 -> 3 -> 0``.

        A multi-circuit example::

            0 -> 1 -> 2 -> 0
            0 -> 3 -> 0
        """
        logger.info(
            "Constraint: ensure that each node is visited (multiple circuits allowed)."
        )
        self.model.add_multiple_circuit(
            [node_from, node_to, var]
            for (node_from, node_to), var in zip(self.instance.arcs, self.arc_vars)
        )

    def _add_max_trucks_constraint(self) -> None:
        """Limit the number of trucks to ``max_trucks``."""
        logger.info(f"Constraint: limit the number of trucks to {self.max_trucks}.")
        self.model.add(sum(self.arcs_leaving_depot_vars) <= self.max_trucks)

    def _add_load_constraint(self) -> None:
        """Enforce cumulative load limits along each truck route."""
        logger.info("Constraint: limit the load on each truck route.")

        arcs = self.instance.arcs
        load_from_vars = self.node_load_vars[arcs[:, 0]]
        load_to_vars = self.node_load_vars[arcs[:, 1]]
        arc_vars = self.arc_vars
        demand_to = self.instance.demand[arcs[:, 1]]

        self.model.add(self.node_load_vars[0] == 0)

        for node_to, load_from_var, load_to_var, arc_var, demand in zip(
            arcs[:, 1], load_from_vars, load_to_vars, arc_vars, demand_to
        ):
            if node_to == 0:
                continue

            self.model.add(load_to_var >= load_from_var + demand).only_enforce_if(
                arc_var
            )

    def _add_truck_minimization_objective(self) -> None:
        """Set stage-1 objective: minimize the number of trucks used."""
        logger.info("Objective: minimize the number of trucks used")
        self.model.clear_objective()
        self.model.minimize(sum(self.arcs_leaving_depot_vars))

    def _add_distance_minimization_objective(self) -> None:
        """Set stage-2 objective: minimize total distance traveled.

        Intended implementation::

            distances = self.instance.arc_distance
            self.model.clear_objective()
            self.model.minimize(
                sum(d * v for d, v in zip(distances, self.arc_vars))
            )

        Requires a feasible stage-1 solution; call ``_set_solution_as_hint`` before
        re-solving to warm-start the search.

        Raises:
            NotImplementedError: Stage 2 is not implemented in v1.
        """
        raise NotImplementedError("Stage 2 distance objective not implemented in v1.")

    def _set_solution_as_hint(self) -> None:
        """Set the current CP-SAT solution as hints for a subsequent solve.

        Call only after a feasible stage-1 run.

        Raises:
            ValueError: If a proto variable name does not match its model variable.
        """
        logger.info("Setting the current solution as hint for the problem...")
        for i, v in enumerate(self.model.proto.variables):
            v_ = self.model.get_int_var_from_proto_index(i)
            if v.name != v_.name:
                raise ValueError(f"Variable name mismatch: {v.name} != {v_.name}")

            self.model.add_hint(v_, self.cp_solver.value(v_))

    def _configure_time_limit(self, max_time_in_seconds: float | None) -> None:
        """Apply an optional time limit to ``cp_solver``.

        Args:
            max_time_in_seconds: Wall-clock limit in seconds, or ``None`` for no limit.
        """
        if max_time_in_seconds is not None:
            self.cp_solver.parameters.max_time_in_seconds = max_time_in_seconds

    def _build_solve_result(self, runtime_seconds: float) -> SolveResult:
        """Package the last solve into a ``SolveResult``.

        Args:
            runtime_seconds: Wall-clock solve duration.

        Return:
            ``SolveResult`` with a populated or empty ``solution`` depending on
            ``is_feasible``.
        """
        status_name = self.status_name or "UNKNOWN"
        if self.is_feasible:
            solution = VRPTWSolution.from_cp_solver(
                self.instance, self.cp_solver, self.arc_vars
            )
            logger.success(f"Solver finished with status: {status_name}")
            return SolveResult(
                status=self.status,
                status_name=status_name,
                solution=solution,
                n_trucks=solution.n_trucks,
                runtime_seconds=runtime_seconds,
            )

        logger.error(f"Solver finished with status: {status_name}")
        return SolveResult(
            status=self.status,
            status_name=status_name,
            solution=VRPTWSolution.empty(self.instance),
            runtime_seconds=runtime_seconds,
        )

    def _solve_stage1_minimize_trucks(
        self, max_time_in_seconds: float | None = None
    ) -> SolveResult:
        """Run stage 1: minimize truck count subject to capacity and fleet limits.

        Args:
            max_time_in_seconds: Optional wall-clock time limit.

        Return:
            ``SolveResult`` from the stage-1 solve.
        """
        self._configure_time_limit(max_time_in_seconds)
        logger.info("Stage 1: minimizing trucks...")
        self._add_truck_minimization_objective()
        callback = VRPTWCallback()
        start = time.monotonic()
        self.status = self.cp_solver.solve(self.model, callback)
        runtime_seconds = time.monotonic() - start
        return self._build_solve_result(runtime_seconds)

    def _solve_stage2_minimize_distance(
        self, max_time_in_seconds: float | None = None
    ) -> SolveResult:
        """Run stage 2: re-solve with distance objective and hints from stage 1.

        Intended flow::

            stage1 = self._solve_stage1_minimize_trucks(max_time_in_seconds)
            if not self.is_feasible:
                return stage1
            self._set_solution_as_hint()
            self._add_distance_minimization_objective()
            # optionally fix truck count from stage 1
            self.status = self.cp_solver.solve(self.model)
            return self._build_solve_result(runtime_seconds)

        Args:
            max_time_in_seconds: Optional wall-clock time limit.

        Raises:
            NotImplementedError: Stage 2 is not implemented in v1.
        """
        raise NotImplementedError("Stage 2 not implemented in v1.")

    def solve(self, max_time_in_seconds: float | None = None) -> SolveResult:
        """Run stage 1 (minimize trucks).

        Args:
            max_time_in_seconds: Optional wall-clock time limit.

        Return:
            ``SolveResult`` with status, runtime, and solution (empty arcs on
            infeasible or timeout).
        """
        logger.info("Solving the VRPTW problem...")
        return self._solve_stage1_minimize_trucks(max_time_in_seconds)
