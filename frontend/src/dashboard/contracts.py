"""
Data contracts for the dashboard.

The data contracts define the data structures used in the dashboard internals and
to send and receive data from the backend.
"""

from datetime import datetime
from typing import TypedDict


class Dataset(TypedDict):
    """
    One dataset record
    """

    name: str
    instance: str


class Constraints(TypedDict):
    """
    Constraints available
    """

    max_trucks: int
    truck_capacity: int


class SolverParameters(TypedDict):
    """
    Solver parameters
    """

    max_time_in_seconds: int | None
    random_seed: int | None


class Objectives(TypedDict):
    """
    Objectives available
    """

    total_trucks: int
    total_distance: float


class RunMetadata(Objectives):
    """
    Full run metadata: id, status, creation and completion times,
    runtime and objectives.
    """

    run_id: str
    status: str
    created_at: datetime
    finished_at: datetime | None
    runtime_seconds: float | None


class RunRequest(Dataset, Constraints, SolverParameters):
    """
    Full run request payload
    """



class RunResponse(RunRequest, RunMetadata):
    """
    Response payload for a requested run from the backend
    """



class Customer(TypedDict):
    """
    One customer record
    """

    cust_no: int
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int


class Arc(TypedDict):
    """
    One route segment with resolved customer coordinates
    """

    truck_id: int
    sequence: int
    cust_from: Customer
    cust_to: Customer


class SolutionResponse(TypedDict):
    """
    A complete solution response with run details and route segments
    """

    run: RunResponse
    arcs: list[Arc]
