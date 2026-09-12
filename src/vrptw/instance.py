"""VRPTW problem instance definition and derived arc data."""

from functools import cached_property

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


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

    @property
    def node_idx(self) -> np.ndarray:
        """Return contiguous node indices from depot to last customer.

        Indices run from ``0`` to ``n_nodes - 1``, where ``0`` is the depot.

        Return:
            1D ``int32`` array of shape ``(n_nodes,)``.
        """
        return np.arange(self.n_nodes, dtype=np.int32)

    @cached_property
    def arcs(self) -> np.ndarray:
        """Return all directed arcs excluding self-loops.

        Return:
            2D ``int32`` array of shape ``(n_arcs, 2)`` with ``(from, to)``
            ``node_idx`` pairs.
        """
        arc_from = np.repeat(self.node_idx, self.n_nodes)
        arc_to = np.tile(self.node_idx, self.n_nodes)

        # Remove self-arcs
        mask = arc_from != arc_to
        return np.column_stack((arc_from[mask], arc_to[mask]))

    @computed_field
    @cached_property
    def arc_distance(self) -> np.ndarray:
        """Return Euclidean distance for each arc.

        Return:
            1D ``int32`` array of shape ``(n_arcs,)`` aligned with ``arcs``.
        """
        dx = self.xcoord[self.arcs[:, 0]] - self.xcoord[self.arcs[:, 1]]
        dy = self.ycoord[self.arcs[:, 0]] - self.ycoord[self.arcs[:, 1]]
        return np.hypot(dx, dy).astype(np.int32)
