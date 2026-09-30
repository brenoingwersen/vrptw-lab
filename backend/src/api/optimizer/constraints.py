"""CP-SAT constraint posting for the VRPTW model.

Posts circuit, fleet-size, capacity, and time-window constraints onto a
``CpModel`` using variables from ``Variables``. Called once during ``Solver``
initialization.
"""

from ortools.sat.python import cp_model

from api.optimizer.instance import ProblemInstance
from api.optimizer.variables import Variables


class Constraints:
    """Static helpers that post VRPTW constraints onto a CP-SAT model."""

    @staticmethod
    def add_constraints(
        model: cp_model.CpModel, variables: Variables, instance: ProblemInstance
    ):
        """Post all VRPTW constraints onto the model.

        Args:
            model: CP-SAT model under construction.
            variables: Decision variables for arcs, loads, and start times.
            instance: Problem data for fleet limits and time-window bounds.
        """
        Constraints._constraint_circuits(model, variables)
        Constraints._constraint_max_trucks(model, variables, instance)
        Constraints._constraint_load(model, variables)
        Constraints._constraint_time_windows(model, variables, instance)

    @staticmethod
    def _constraint_circuits(model: cp_model.CpModel, variables: Variables):
        """Enforce depot-to-depot circuits via ``add_multiple_circuit``."""
        model.add_multiple_circuit(
            [node_from, node_to, var]
            for (node_from, node_to), var in variables.iter_arcs()
        )

    @staticmethod
    def _constraint_max_trucks(
        model: cp_model.CpModel, variables: Variables, instance: ProblemInstance
    ):
        """Cap the number of depot-leaving arcs at ``max_trucks``."""
        model.add(
            sum(variables.arcs_leaving_depot) <= instance.constraints_config.max_trucks
        )

    @staticmethod
    def _constraint_load(model: cp_model.CpModel, variables: Variables):
        """Enforce cumulative load along active arcs, with zero load at the depot."""
        model.add(variables.node_load_vars[0] == 0)

        for (
            _node_from,
            node_to,
            load_from_var,
            load_to_var,
            arc_var,
            demand,
        ) in variables.iter_load_arcs():
            if node_to == 0:
                continue

            model.add(load_to_var >= load_from_var + demand).only_enforce_if(arc_var)

    @staticmethod
    def _constraint_time_windows(
        model: cp_model.CpModel, variables: Variables, instance: ProblemInstance
    ):
        """Link service start times across active arcs respecting travel and service."""
        for (
            node_from,
            node_to,
            start_from_var,
            start_to_var,
            arc_var,
            travel_time,
        ) in variables.iter_start_time_arcs():
            if node_to == 0:
                continue

            model.add(
                start_to_var
                >= start_from_var + instance.service_time[node_from] + travel_time
            ).only_enforce_if(arc_var)
