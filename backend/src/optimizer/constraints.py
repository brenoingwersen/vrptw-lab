from ortools.sat.python import cp_model

from optimizer.instance import ProblemInstance
from optimizer.variables import Variables


class Constraints:
    @staticmethod
    def add_constraints(
        model: cp_model.CpModel, variables: Variables, instance: ProblemInstance
    ):
        """
        Add the constraints to the model.
        """
        Constraints._constraint_circuits(model, variables)
        Constraints._constraint_max_trucks(model, variables, instance)
        Constraints._constraint_load(model, variables)
        Constraints._constraint_time_windows(model, variables, instance)

    @staticmethod
    def _constraint_circuits(model: cp_model.CpModel, variables: Variables):
        """
        Constraint the circuits.
        """
        model.add_multiple_circuit(
            [node_from, node_to, var]
            for (node_from, node_to), var in variables.iter_arcs()
        )

    @staticmethod
    def _constraint_max_trucks(
        model: cp_model.CpModel, variables: Variables, instance: ProblemInstance
    ):
        """
        Constraint the maximum number of trucks.
        """
        model.add(
            sum(variables.arcs_leaving_depot) <= instance.constraints_config.max_trucks
        )

    @staticmethod
    def _constraint_load(model: cp_model.CpModel, variables: Variables):
        """
        Constraint the load.
        """
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
        """
        Constraint the time windows.
        """
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
