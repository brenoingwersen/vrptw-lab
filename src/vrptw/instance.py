"""VRPTW problem instance definition."""

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator


class VRPTWInstance(BaseModel):
    """Vehicle routing problem instance with time-window fields.

    Node index ``0`` is the depot; ``cust_no`` holds external customer identifiers.

    Attributes:
        cust_no: Customer numbers (``1`` = depot).
        xcoord: X-coordinates of each node.
        ycoord: Y-coordinates of each node.
        demand: Customer demand (``0`` at the depot).
        ready_time: Earliest service start time per node.
        due_date: Latest service start time per node.
        service_time: Service duration per node.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> "VRPTWInstance":
        """Create an instance from a pandas DataFrame.

        Args:
            df: DataFrame with columns matching the instance field names.

        Return:
            A validated ``VRPTWInstance``.
        """
        return cls(
            cust_no=df["cust_no"].to_numpy(dtype=np.int32),
            xcoord=df["xcoord"].to_numpy(dtype=np.int32),
            ycoord=df["ycoord"].to_numpy(dtype=np.int32),
            demand=df["demand"].to_numpy(dtype=np.int32),
            ready_time=df["ready_time"].to_numpy(dtype=np.int32),
            due_date=df["due_date"].to_numpy(dtype=np.int32),
            service_time=df["service_time"].to_numpy(dtype=np.int32),
        )

    @property
    def n_nodes(self) -> int:
        """Return the number of nodes in the instance.

        Return:
            Length of ``cust_no``.
        """
        return len(self.cust_no)

    def travel_time(self, node_from: int, node_to: int) -> int:
        """Return Euclidean travel time between two nodes.

        Args:
            node_from: Origin node index.
            node_to: Destination node index.

        Return:
            Integer Euclidean distance between the nodes.
        """
        dx = self.xcoord[node_from] - self.xcoord[node_to]
        dy = self.ycoord[node_from] - self.ycoord[node_to]
        return int(np.hypot(dx, dy))
