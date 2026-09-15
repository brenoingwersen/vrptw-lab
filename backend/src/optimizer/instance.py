import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain import OptimizationRequest


class ConstraintsConfig(BaseModel):
    """
    Configuration for the constraints for the optimization problem.
    """

    max_trucks: int = Field(..., gt=0)
    truck_capacity: int = Field(..., gt=0)


class SolverConfig(BaseModel):
    """
    Configuration for the solver.
    """

    max_time_in_seconds: int | None = None
    random_seed: int | None = None


class ProblemInstance(BaseModel):
    """
    VRPTW problem instance defining all the optimization problem
    including constraints and solver configuration.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    solver_config: SolverConfig
    constraints_config: ConstraintsConfig

    cust_no: np.ndarray = Field(
        ..., description="The number of the customer. 1 = depot."
    )
    xcoord: np.ndarray = Field(..., description="The x-coordinate of the customer.")
    ycoord: np.ndarray = Field(..., description="The y-coordinate of the customer.")
    demand: np.ndarray = Field(..., description="The demand of the customer. 0 = depot")
    ready_time: np.ndarray = Field(
        ..., description="The earliest date the customer can be visited."
    )
    due_date: np.ndarray = Field(
        ..., description="The latest date the customer must be visited."
    )
    service_time: np.ndarray = Field(
        ..., description="The service time of the customer."
    )

    @model_validator(mode="after")
    def validate_shapes_and_types(self):
        """Validate that all fields are 1D arrays of equal length.

        Raises:
            ValueError: If any field is not 1D or lengths differ.
        """
        fields = [
            self.cust_no,
            self.xcoord,
            self.ycoord,
            self.demand,
            self.ready_time,
            self.due_date,
            self.service_time,
        ]

        n = len(self.cust_no)
        for arr in fields:
            if arr.ndim != 1 or len(arr) != n:
                raise ValueError(
                    f"All fields must be 1D numpy arrays of equal length {n}."
                )
        return self

    @property
    def n_nodes(self) -> int:
        """Return the number of nodes in the instance.

        Returns:
            Length of ``cust_no``.
        """
        return len(self.cust_no)

    def travel_time(self, node_from: int, node_to: int) -> int:
        """Return Euclidean travel time between two nodes.

        Travel time equals integer Euclidean distance. This helper keeps
        distance geometry in the data layer so route utilities and the
        solver share one definition of arc cost.

        Args:
            node_from: Origin node index.
            node_to: Destination node index.

        Returns:
            Integer Euclidean distance between the nodes.
        """
        dx = self.xcoord[node_from] - self.xcoord[node_to]
        dy = self.ycoord[node_from] - self.ycoord[node_to]
        return int(np.hypot(dx, dy))

    @classmethod
    def from_request(cls, request: OptimizationRequest) -> "ProblemInstance":
        """
        Create a problem instance from an optimization request DTO.
        """
        return cls(
            solver_config=SolverConfig(
                max_time_in_seconds=request.max_time_in_seconds,
                random_seed=request.random_seed,
            ),
            constraints_config=ConstraintsConfig(
                max_trucks=request.max_trucks,
                truck_capacity=request.truck_capacity,
            ),
            cust_no=np.array([row.cust_no for row in request.customers]),
            xcoord=np.array([row.xcoord for row in request.customers]),
            ycoord=np.array([row.ycoord for row in request.customers]),
            demand=np.array([row.demand for row in request.customers]),
            ready_time=np.array([row.ready_time for row in request.customers]),
            due_date=np.array([row.due_date for row in request.customers]),
            service_time=np.array([row.service_time for row in request.customers]),
        )
