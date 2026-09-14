"""Complete VRPTW problem definition: instance data plus fleet parameters.

This module sits between raw node data and the solver. It composes a
``VRPTWInstance`` with fleet-level constraints without duplicating node fields
or touching CP-SAT model code.

Separation of concerns:

    * ``VRPTWInstance`` — node geometry, demand, and time windows only.
    * ``VRPTWProblem`` — fleet parameters and cross-field validation.
    * ``SolverConfig`` — engine tuning (seed, time limit, log level).
    * ``VRPTWSolver`` — model building, constraints, and optimization.
"""

from pydantic import BaseModel, Field

from vrptw.instance import VRPTWInstance


class VRPTWProblem(BaseModel):
    """A solvable VRPTW problem: node data plus fleet constraints.

    Bundles an instance with operational limits (capacity and fleet size).
    Problem-level validation lives here— for example, ensuring no single
    customer demand exceeds truck capacity— so the solver can assume
    consistent inputs.

    Attributes:
        instance: Node-level problem data.
        truck_capacity: Maximum cumulative load per truck route.
        max_trucks: Upper bound on the number of trucks that may leave the depot.
    """

    instance: VRPTWInstance
    truck_capacity: int = Field(default=200, gt=0)
    max_trucks: int = Field(default=20, gt=0)

    @classmethod
    def from_instance(
        cls,
        instance: VRPTWInstance,
        *,
        truck_capacity: int = 200,
        max_trucks: int = 20,
    ) -> "VRPTWProblem":
        """Build a problem from an instance and fleet parameters.

        Args:
            instance: Node-level problem data.
            truck_capacity: Maximum load per truck.
            max_trucks: Upper bound on fleet size.

        Returns:
            A validated ``VRPTWProblem``.
        """
        return cls(
            instance=instance,
            truck_capacity=truck_capacity,
            max_trucks=max_trucks,
        )

    def validate(self) -> None:
        """Ensure problem parameters are compatible with instance demand.

        Raises:
            ValueError: If any customer demand exceeds ``truck_capacity``.
        """
        max_demand = int(self.instance.demand.max())
        if max_demand > self.truck_capacity:
            raise ValueError(
                f"Maximum demand ({max_demand}) exceeds "
                f"truck_capacity ({self.truck_capacity})."
            )
