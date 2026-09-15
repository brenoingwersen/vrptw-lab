"""CP-SAT solver for VRPTW with two-stage lexicographic optimization.

This module orchestrates the full solve pipeline: model construction,
constraint posting, objective switching, and result packaging. It delegates
variable creation to ``VRPTWVariables``, route metrics to ``routes``, and
feasibility checks to ``validators``.

Two-stage lexicographic solve:

    Stage 1 — minimize the number of trucks (depot-leaving arcs) subject to
    capacity, fleet size, circuit, and time-window constraints.
    Stage 2 — fix the stage-1 truck count, warm-start from stage 1, and
    minimize total route distance.

Separation of concerns:

    * ``VRPTWProblem`` — what to optimize (data + fleet limits).
    * ``VRPTWVariables`` — decision variables and arc indexing.
    * ``VRPTWSolver`` — constraints, objectives, and solve orchestration.
    * ``SolveResult`` / ``VRPTWSolution`` — outcomes after a run completes.
    * ``routes`` / ``validators`` — post-solve analysis on selected arcs.
"""

import time

from loguru import logger
from ortools.sat.python import cp_model

from vrptw.callback import VRPTWCallback
from vrptw.instance import VRPTWInstance
from vrptw.log import (
    configure_logging,
    log_section,
    log_solve_complete,
    log_stage_complete,
)
from vrptw.problem import VRPTWProblem
from vrptw.result import SolveResult
from vrptw.routes import count_trucks, total_distance
from vrptw.solution import VRPTWSolution
from vrptw.solver_config import SolverConfig
from vrptw.validators import validate_solution
from vrptw.variables import VRPTWVariables


class VRPTWSolver:
    """CP-SAT model builder and two-stage solve orchestrator.

    Owns the OR-Tools ``CpModel`` and ``CpSolver`` lifecycle: variables are
    created at construction, constraints are added once, and ``solve`` runs
    the lexicographic two-stage search. This class does **not** format output
    tables or re-validate routes beyond calling ``validators`` before
    returning a result.

    Attributes:
        problem: Complete VRPTW problem definition.
        config: CP-SAT engine configuration (seed, time limit, logging).
        model: OR-Tools CP-SAT model with variables and constraints.
        cp_solver: Configured ``CpSolver`` instance reused across stages.
        status: Solver status code from the last ``solve`` call, or ``None``.
    """

    def __init__(
        self,
        problem: VRPTWProblem,
        config: SolverConfig | None = None,
    ):
        """Initialize the solver and build the CP-SAT model.

        Validates the problem, configures logging, creates variables, and
        posts all constraints. Objectives are set per stage, not here.

        Args:
            problem: VRPTW problem to solve.
            config: CP-SAT engine configuration. Defaults to ``SolverConfig()``.
        """
        problem.validate()
        self.problem = problem
        self.config = config or SolverConfig()
        configure_logging(self.config.log_level)

        self.model = cp_model.CpModel()
        self._variables = VRPTWVariables(problem, self.model)
        self._add_constraints()
        logger.info(
            "Model constraints added: "
            f"circuit, max_trucks={self.problem.max_trucks}, load, time_windows"
        )

        self.cp_solver = cp_model.CpSolver()
        random_seed = self.config.random_seed
        if random_seed is not None:
            self.cp_solver.parameters.random_seed = random_seed
        self.status = None

    @property
    def instance(self) -> VRPTWInstance:
        """Return the node-level problem instance.

        Returns:
            The ``VRPTWInstance`` embedded in ``problem``.
        """
        return self.problem.instance

    @property
    def is_feasible(self) -> bool:
        """Return whether the last solve found a feasible or optimal solution.

        Returns:
            ``True`` when ``status`` is ``OPTIMAL`` or ``FEASIBLE``.
        """
        return self.status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    @property
    def status_name(self) -> str | None:
        """Return the human-readable name of the last solver status.

        Returns:
            Status name string, or ``None`` if no solve has run yet.
        """
        if self.status is None:
            return None
        return self.cp_solver.status_name(self.status)

    @property
    def variables(self) -> VRPTWVariables:
        """Return the CP-SAT variable container for this model.

        Returns:
            The ``VRPTWVariables`` instance created at construction.
        """
        return self._variables

    def _add_constraints(self) -> None:
        """Add circuit, fleet, load, and time-window constraints to ``model``."""
        logger.debug("Adding constraints to the model...")
        self._add_circuit_constraint()
        self._add_max_trucks_constraint()
        self._add_load_constraint()
        self._add_time_window_constraints()

    def _add_circuit_constraint(self) -> None:
        """Ensure each customer is visited exactly once across truck circuits.

        Uses OR-Tools ``add_multiple_circuit`` so the solution may contain
        several disjoint depot-to-depot routes (one per truck).

        Example single route: ``0 -> 1 -> 2 -> 3 -> 0``.

        Example two-truck solution::

            0 -> 1 -> 2 -> 0
            0 -> 3 -> 0
        """
        logger.debug(
            "Constraint: ensure that each node is visited (multiple circuits allowed)."
        )
        self.model.add_multiple_circuit(
            [node_from, node_to, var]
            for (node_from, node_to), var in self.variables.iter_arcs()
        )

    def _add_max_trucks_constraint(self) -> None:
        """Limit the number of trucks to ``problem.max_trucks``.

        Each truck corresponds to one depot-leaving arc, so this caps the
        sum of ``arcs_leaving_depot``.
        """
        logger.debug(
            f"Constraint: limit the number of trucks to {self.problem.max_trucks}."
        )
        self.model.add(
            sum(self.variables.arcs_leaving_depot) <= self.problem.max_trucks
        )

    def _add_load_constraint(self) -> None:
        """Enforce cumulative load limits along each truck route.

        Load increases by customer demand when an arc is selected. The depot
        starts at zero load. Returning-to-depot arcs are skipped because
        load is tracked only for customer visits.
        """
        logger.debug("Constraint: limit the load on each truck route.")
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
        """Enforce precedence and time windows along each selected arc.

        Service at the destination cannot start before service finishes at
        the origin plus travel time. Node start-time variables are already
        bounded by each node's ``ready_time`` and ``due_date``.
        """
        logger.debug("Constraint: enforce time window constraints for each node.")
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
        logger.debug("Objective: minimize the number of trucks used")
        self.model.clear_objective()
        self.model.minimize(sum(self.variables.arcs_leaving_depot))

    def _add_distance_minimization_objective(self) -> None:
        """Set stage-2 objective: minimize total distance traveled."""
        logger.debug("Objective: minimize total distance traveled")
        distances = self.variables.arc_distance
        self.model.clear_objective()
        self.model.minimize(
            sum(d * v for d, v in zip(distances, self.variables.arc_vars, strict=True))
        )

    def _fix_truck_count(self, n_trucks: int) -> None:
        """Fix the number of trucks to the stage-1 optimum for stage 2.

        Args:
            n_trucks: Truck count from the stage-1 optimal solution.
        """
        logger.debug(f"Constraint: fix the number of trucks to {n_trucks}.")
        self.model.add(sum(self.variables.arcs_leaving_depot) == n_trucks)

    def _set_solution_as_hint(self) -> None:
        """Set the current CP-SAT solution as hints for a subsequent solve.

        Call only after a feasible stage-1 run so stage 2 starts near a
        good incumbent.

        Raises:
            ValueError: If a proto variable name does not match its model variable.
        """
        logger.debug("Setting the current solution as hint for the problem...")
        for i, v in enumerate(self.model.proto.variables):
            v_ = self.model.get_int_var_from_proto_index(i)
            if v.name != v_.name:
                raise ValueError(f"Variable name mismatch: {v.name} != {v_.name}")

            self.model.add_hint(v_, self.cp_solver.value(v_))

    def _configure_time_limit(self) -> None:
        """Apply the configured time limit to ``cp_solver``, if any."""
        if self.config.max_time_in_seconds is not None:
            self.cp_solver.parameters.max_time_in_seconds = (
                self.config.max_time_in_seconds
            )

    def _build_solve_result(self, runtime_seconds: float) -> SolveResult:
        """Package the last solve into a ``SolveResult``.

        On feasible runs, extracts selected arcs, validates them, and
        computes truck count and total distance via ``routes``.

        Args:
            runtime_seconds: Wall-clock solve duration for the current stage.

        Returns:
            ``SolveResult`` with a populated or empty ``solution`` depending on
            ``is_feasible``.
        """
        status_name = self.status_name or "UNKNOWN"
        if self.is_feasible:
            selected_arcs = self.variables.get_selected_arcs(self.cp_solver)
            validate_solution(selected_arcs, self.problem)
            solution = VRPTWSolution(selected_arcs)
            n_trucks = count_trucks(selected_arcs)
            dist = total_distance(selected_arcs, self.instance)
            return SolveResult(
                status=self.status,
                status_name=status_name,
                solution=solution,
                n_trucks=n_trucks,
                total_distance=dist,
                runtime_seconds=runtime_seconds,
            )

        logger.error(f"Stage finished with status: {status_name}")
        return SolveResult(
            status=self.status,
            status_name=status_name,
            solution=VRPTWSolution.empty(),
            runtime_seconds=runtime_seconds,
        )

    def _solve_stage1_minimize_trucks(self) -> SolveResult:
        """Run stage 1: minimize truck count subject to all constraints.

        Returns:
            ``SolveResult`` from the stage-1 solve.
        """
        self._configure_time_limit()
        log_section("Stage 1: Minimize trucks")
        self._add_truck_minimization_objective()
        start = time.monotonic()
        callback = VRPTWCallback(stage="Stage 1")
        self.status = self.cp_solver.solve(self.model, callback)
        runtime_seconds = time.monotonic() - start
        result = self._build_solve_result(runtime_seconds)
        callback.log_summary()
        log_stage_complete(
            "Stage 1",
            result.status_name,
            runtime_seconds,
            trucks=result.n_trucks,
        )
        return result

    def _solve_stage2_minimize_distance(self) -> SolveResult:
        """Run stage 2: minimize distance with fixed truck count and hints.

        Assumes stage 1 already ran and left a feasible solution in
        ``cp_solver``.

        Returns:
            ``SolveResult`` from the stage-2 solve.
        """
        n_trucks = count_trucks(self.variables.get_selected_arcs(self.cp_solver))
        self._fix_truck_count(n_trucks)
        self._set_solution_as_hint()
        self._add_distance_minimization_objective()
        self._configure_time_limit()
        log_section("Stage 2: Minimize distance")
        start = time.monotonic()
        callback = VRPTWCallback(stage="Stage 2")
        self.status = self.cp_solver.solve(self.model, callback)
        runtime_seconds = time.monotonic() - start
        result = self._build_solve_result(runtime_seconds)
        callback.log_summary()
        log_stage_complete(
            "Stage 2",
            result.status_name,
            runtime_seconds,
            distance=result.total_distance,
        )
        return result

    def solve(self) -> SolveResult:
        """Run the full two-stage lexicographic solve.

        Stage 1 minimizes trucks; stage 2 minimizes distance while keeping
        the stage-1 fleet size. If stage 1 is infeasible, stage 2 is
        skipped and the stage-1 result is returned with empty arcs.

        Returns:
            ``SolveResult`` with combined runtime, final status, solution,
            truck count, and total distance.
        """
        log_section("Solving VRPTW problem")
        stage1 = self._solve_stage1_minimize_trucks()
        if not self.is_feasible:
            return stage1
        stage2 = self._solve_stage2_minimize_distance()
        final_result = SolveResult(
            status=stage2.status,
            status_name=stage2.status_name,
            solution=stage2.solution,
            n_trucks=stage2.n_trucks,
            total_distance=stage2.total_distance,
            runtime_seconds=(stage1.runtime_seconds or 0)
            + (stage2.runtime_seconds or 0),
        )
        log_solve_complete(final_result)
        return final_result
