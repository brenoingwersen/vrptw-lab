"""VRPTW problem definition: instance data plus fleet parameters."""

from pydantic import BaseModel, Field

from vrptw.instance import VRPTWInstance


class VRPTWProblem(BaseModel):
    """Complete VRPTW problem: node data and fleet constraints.

    Attributes:
        instance: Node-level problem data.
        truck_capacity: Maximum load per truck.
        max_trucks: Upper bound on fleet size.
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

        Return:
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
