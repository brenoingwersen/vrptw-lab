"""CP-SAT solver for fleet minimization with capacity constraints.

Stage 1 minimizes trucks (fleet + capacity). Stage 2 (distance minimization)
and time-window constraints are planned extension points.
"""

import time

from loguru import logger
from ortools.sat.python import cp_model

from vrptw.callback import VRPTWCallback
from vrptw.instance import VRPTWInstance
from vrptw.problem import VRPTWProblem
from vrptw.result import SolveResult
from vrptw.routes import count_trucks
from vrptw.solution import VRPTWSolution
from vrptw.solver_config import SolverConfig
from vrptw.validators import validate_solution
from vrptw.variables import VRPTWVariables


class VRPTWSolver:
    """CP-SAT model builder and solve orchestrator.

    v1 solves capacity constraints and fleet (truck) minimization only.
    Time windows and distance objectives are extension points for later stages.

    Attributes:
        problem: VRPTW problem definition.
        config: CP-SAT engine configuration.
        model: OR-Tools CP-SAT model.
        cp_solver: Configured ``CpSolver`` instance.
        status: Solver status code from the last ``solve`` call, or ``None``.
    """

    def __init__(
        self,
        problem: VRPTWProblem,
        config: SolverConfig | None = None,
    ):
        """Initialize the solver and build the CP-SAT model.

        Args:
            problem: VRPTW problem to solve.
            config: CP-SAT engine configuration.
        """
        problem.validate()
        self.problem = problem
        self.config = config or SolverConfig()

        self.model = cp_model.CpModel()
        self._variables = VRPTWVariables(problem, self.model)
        self._add_constraints()

        self.cp_solver = cp_model.CpSolver()
        self.cp_solver.parameters.random_seed = self.config.random_seed
        self.status = None

    @property
    def instance(self) -> VRPTWInstance:
        """Return the node-level problem instance."""
        return self.problem.instance

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
    def variables(self) -> VRPTWVariables:
        """Return the variables of the solver."""
        return self._variables

    def _add_constraints(self) -> None:
        """Add circuit, fleet, and load constraints to ``model``."""
        logger.info("Adding constraints to the model...")
        self._add_circuit_constraint()
        self._add_max_trucks_constraint()
        self._add_load_constraint()
        self._add_time_window_constraints()

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
            for (node_from, node_to), var in self.variables.iter_arcs()
        )

    def _add_max_trucks_constraint(self) -> None:
        """Limit the number of trucks to ``problem.max_trucks``."""
        logger.info(
            f"Constraint: limit the number of trucks to {self.problem.max_trucks}."
        )
        self.model.add(
            sum(self.variables.arcs_leaving_depot) <= self.problem.max_trucks
        )

    def _add_load_constraint(self) -> None:
        """Enforce cumulative load limits along each truck route."""
        logger.info("Constraint: limit the load on each truck route.")
        self.model.add(self.variables.node_load_vars[0] == 0)

        for (
            _node_from,
            node_to,
            load_from_var,
            load_to_var,
            arc_var,
            demand,
        ) in self.variables.iter_load_arcs():
            if node_to == 0:
                continue

            self.model.add(load_to_var >= load_from_var + demand).only_enforce_if(
                arc_var
            )

    def _add_time_window_constraints(self) -> None:
        """Enforce time window constraints for each node."""
        logger.info("Constraint: enforce time window constraints for each node.")
        for (
            node_from,
            node_to,
            start_from_var,
            start_to_var,
            arc_var,
            travel_time,
        ) in self.variables.iter_start_time_arcs():
            if node_to == 0:
                continue

            self.model.add(
                start_to_var
                >= start_from_var + self.instance.service_time[node_from] + travel_time
            ).only_enforce_if(arc_var)

    def _add_truck_minimization_objective(self) -> None:
        """Set stage-1 objective: minimize the number of trucks used."""
        logger.info("Objective: minimize the number of trucks used")
        self.model.clear_objective()
        self.model.minimize(sum(self.variables.arcs_leaving_depot))

    def _add_distance_minimization_objective(self) -> None:
        """Set stage-2 objective: minimize total distance traveled.

        Intended implementation::

            distances = self.variables.arc_distance
            self.model.clear_objective()
            self.model.minimize(
                sum(d * v for d, v in zip(distances, self.variables.arc_vars))
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

    def _configure_time_limit(self) -> None:
        """Apply the configured time limit to ``cp_solver``."""
        if self.config.max_time_in_seconds is not None:
            self.cp_solver.parameters.max_time_in_seconds = (
                self.config.max_time_in_seconds
            )

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
            selected_arcs = self.variables.get_selected_arcs(self.cp_solver)
            validate_solution(selected_arcs, self.problem)
            solution = VRPTWSolution(selected_arcs)
            n_trucks = count_trucks(selected_arcs)
            logger.success(f"Solver finished with status: {status_name}")
            return SolveResult(
                status=self.status,
                status_name=status_name,
                solution=solution,
                n_trucks=n_trucks,
                runtime_seconds=runtime_seconds,
            )

        logger.error(f"Solver finished with status: {status_name}")
        return SolveResult(
            status=self.status,
            status_name=status_name,
            solution=VRPTWSolution.empty(),
            runtime_seconds=runtime_seconds,
        )

    def _solve_stage1_minimize_trucks(self) -> SolveResult:
        """Run stage 1: minimize truck count subject to capacity and fleet limits.

        Return:
            ``SolveResult`` from the stage-1 solve.
        """
        self._configure_time_limit()
        logger.info("Stage 1: minimizing trucks...")
        self._add_truck_minimization_objective()
        start = time.monotonic()
        self.status = self.cp_solver.solve(self.model, VRPTWCallback())
        runtime_seconds = time.monotonic() - start
        return self._build_solve_result(runtime_seconds)

    def _solve_stage2_minimize_distance(self) -> SolveResult:
        """Run stage 2: re-solve with distance objective and hints from stage 1.

        Intended flow::

            stage1 = self._solve_stage1_minimize_trucks()
            if not self.is_feasible:
                return stage1
            self._set_solution_as_hint()
            self._add_distance_minimization_objective()
            # optionally fix truck count from stage 1
            self.status = self.cp_solver.solve(self.model)
            return self._build_solve_result(runtime_seconds)

        Raises:
            NotImplementedError: Stage 2 is not implemented in v1.
        """
        raise NotImplementedError("Stage 2 not implemented in v1.")

    def solve(self) -> SolveResult:
        """Run stage 1 (minimize trucks).

        Return:
            ``SolveResult`` with status, runtime, and solution (empty arcs on
            infeasible or timeout).
        """
        logger.info("Solving the VRPTW problem...")
        return self._solve_stage1_minimize_trucks()
