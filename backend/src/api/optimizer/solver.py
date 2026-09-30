"""Two-stage CP-SAT solver for VRPTW instances.

Builds a model from ``ProblemInstance``, posts constraints via ``Constraints``,
creates decision variables via ``Variables``, and runs a two-stage optimization:
minimize trucks, then minimize distance with the fleet size fixed.
"""

from time import perf_counter

from loguru import logger
from ortools.sat.python import cp_model

from api.models import RunStatus
from api.optimizer.callback import Callback
from api.optimizer.constraints import Constraints
from api.optimizer.instance import ProblemInstance
from api.optimizer.utils import count_trucks, to_route_arcs, total_distance
from api.optimizer.validators import validate_solution
from api.optimizer.variables import Variables
from api.schemas import OptimizationRequestSchema, OptimizationResultSchema

_STATUS_LABELS = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
    cp_model.UNKNOWN: "UNKNOWN",
}


def _status_label(status: int) -> str:
    """Return a human-readable CP-SAT status label."""
    return _STATUS_LABELS.get(status, str(status))


class Solver:
    """Two-stage CP-SAT solver for VRPTW instances.

    Builds the model via ``Variables`` and ``Constraints``, runs stage 1
    (minimize trucks) then stage 2 (minimize distance with fixed fleet).
    """

    def __init__(self, request: OptimizationRequestSchema):
        """Build the CP-SAT model from an optimization request.

        Args:
            request: Run constraints, solver settings, and customer data.
        """
        self.instance = ProblemInstance.from_request(request)
        self.model = cp_model.CpModel()

        self.variables = Variables(self.instance, self.model)

        Constraints.add_constraints(self.model, self.variables, self.instance)

        self._configure_solver()
        self._cp_status: int = cp_model.UNKNOWN

    @property
    def is_feasible(self) -> bool:
        """Return whether the last solve finished with a feasible or optimal status."""
        return self._cp_status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    def _configure_solver(self) -> None:
        """Create and configure the CP-SAT solver instance."""
        cp_solver = cp_model.CpSolver()

        max_time_in_seconds = self.instance.solver_config.max_time_in_seconds
        if max_time_in_seconds is not None:
            cp_solver.parameters.max_time_in_seconds = max_time_in_seconds

        random_seed = self.instance.solver_config.random_seed
        if random_seed is not None:
            cp_solver.parameters.random_seed = random_seed

        self.cp_solver = cp_solver

    def _add_truck_minimization_objective(self) -> None:
        """Set the objective to minimize the number of depot-leaving arcs."""
        self.model.clear_objective()
        self.model.minimize(sum(self.variables.arcs_leaving_depot))

    def _add_distance_minimization_objective(self) -> None:
        """Set the objective to minimize total travel distance."""
        distances = self.variables.arc_distance
        self.model.clear_objective()
        self.model.minimize(
            sum(d * v for d, v in zip(distances, self.variables.arc_vars, strict=True))
        )

    def _solve_stage1_minimize_trucks(self) -> OptimizationResultSchema:
        """Run stage 1: minimize the number of trucks used.

        Returns:
            Partial result with truck count and runtime; arcs may be empty if
            infeasible.
        """
        self._add_truck_minimization_objective()
        callback = Callback("stage 1")

        logger.info("Stage 1: minimizing truck count")
        start_time = perf_counter()
        self._cp_status = self.cp_solver.solve(self.model, callback)
        runtime_seconds = perf_counter() - start_time
        callback.log_summary()

        return self._build_optimization_response(runtime_seconds)

    def _fix_truck_count(self, total_trucks: int) -> None:
        """Cap depot-leaving arcs at the fleet size found in stage 1."""
        self.model.add(sum(self.variables.arcs_leaving_depot) <= total_trucks)

    def _solve_stage2_minimize_distance(
        self, stage1_response: OptimizationResultSchema
    ) -> OptimizationResultSchema:
        """Run stage 2: minimize distance with truck count fixed from stage 1.

        Args:
            stage1_response: Result from stage 1, used for truck count and hints.

        Returns:
            Final optimization result including validated route arcs.
        """
        self._set_solution_as_hint()
        self._fix_truck_count(stage1_response.total_trucks)
        callback = Callback("stage 2")

        logger.info(
            f"Stage 2: minimizing distance (trucks fixed at {stage1_response.total_trucks})"
        )
        start_time = perf_counter()
        self._cp_status = self.cp_solver.solve(self.model, callback)
        runtime_seconds = perf_counter() - start_time + stage1_response.runtime_seconds
        callback.log_summary()

        return self._build_optimization_response(runtime_seconds)

    def _build_optimization_response(
        self, runtime_seconds: float
    ) -> OptimizationResultSchema:
        """Build a result DTO from the current solver state.

        Validates selected arcs when feasible; returns a failed status otherwise.
        """
        if self.is_feasible:
            selected_arcs = self.variables.get_selected_arcs(self.cp_solver)
            validate_solution(selected_arcs, self.instance)

            return OptimizationResultSchema(
                status=RunStatus.completed,
                arcs=to_route_arcs(selected_arcs, self.instance),
                total_trucks=count_trucks(selected_arcs),
                total_distance=total_distance(selected_arcs, self.instance),
                runtime_seconds=runtime_seconds,
            )

        return OptimizationResultSchema(
            status=RunStatus.failed,
            arcs=[],
            total_trucks=None,
            total_distance=None,
            runtime_seconds=runtime_seconds,
        )

    def solve(self) -> OptimizationResultSchema:
        """Run the full two-stage VRPTW optimization.

        Returns:
            Final result after stage 2, or a failed result if stage 1 is
            infeasible.
        """
        logger.info(f"Starting two-stage VRPTW solve (nodes={self.instance.n_nodes})")
        stage1_response = self._solve_stage1_minimize_trucks()

        if not self.is_feasible:
            logger.info(
                f"Solve failed after stage 1: status={_status_label(self._cp_status)}, "
                f"runtime={stage1_response.runtime_seconds:.2f}s"
            )
            return stage1_response

        stage2_response = self._solve_stage2_minimize_distance(stage1_response)

        logger.info(
            f"Solve complete: status={_status_label(self._cp_status)}, "
            f"trucks={stage2_response.total_trucks}, "
            f"distance={stage2_response.total_distance}, "
            f"runtime={stage2_response.runtime_seconds:.2f}s"
        )
        return stage2_response

    def _set_solution_as_hint(self) -> None:
        """Apply warm-start hints from the stage 1 solution to decision variables."""
        for i, v in enumerate(self.model.proto.variables):
            v_ = self.model.get_int_var_from_proto_index(i)
            if v.name != v_.name:
                raise ValueError(f"Variable name mismatch: {v.name} != {v_.name}")

            self.model.add_hint(v_, self.cp_solver.value(v_))
