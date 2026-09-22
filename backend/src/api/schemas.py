"""Schemas for the API endpoints.

Schemas define the data contracts between the API and the services connected to it
which include: ``Optimizer``, database and frontend.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.models import RunStatus


class DatasetSchema(BaseModel):
    """
    One dataset record
    """

    model_config = ConfigDict(from_attributes=True)
    name: str
    instance: str


class RunRequestMetadata(BaseModel):
    """
    Schema for the request metadata.
    """

    # Constraints
    max_trucks: int = Field(..., gt=0)
    truck_capacity: int = Field(..., gt=0)

    # Solver parameters
    max_time_in_seconds: int | None = Field(default=None, gt=0)
    random_seed: int | None = None


class RunCreateRequest(RunRequestMetadata):
    """
    Schema for requesting a new optimization run.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "solomon",
                    "instance": "C101",
                    "max_trucks": 20,
                    "truck_capacity": 200,
                    "max_time_in_seconds": 60,
                    "random_seed": 42,
                }
            ]
        },
    )
    name: str
    instance: str


class RunResultMetadata(BaseModel):
    """
    Solver status, runtime and objective values
    """

    status: RunStatus
    total_trucks: int | None
    total_distance: float | None
    runtime_seconds: float | None


class RunDetailResponse(RunCreateRequest, RunResultMetadata):
    """
    Schema for returning the run details
    """

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    created_at: datetime | None
    finished_at: datetime | None


class CustomerSchema(BaseModel):
    """
    Customer schema
    """

    model_config = ConfigDict(from_attributes=True)

    cust_no: int
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int


class SolutionArcSchema(BaseModel):
    """
    Schema for a route segment with ``truck_id``,
    ``sequence``, ``cust_no_from`` and ``cust_no_to`` fields.
    """

    model_config = ConfigDict(from_attributes=True)

    truck_id: int
    sequence: int
    cust_no_from: int
    cust_no_to: int


class ArcSchema(BaseModel):
    """
    Schema for a route segment with the resolved customer coordinates
    and other features.
    """

    model_config = ConfigDict(from_attributes=True)

    truck_id: int
    sequence: int
    cust_from: CustomerSchema
    cust_to: CustomerSchema


class SolutionResponse(BaseModel):
    """
    Schema for the optimization result returned by the solver
    """

    model_config = ConfigDict(from_attributes=True)

    run: RunDetailResponse
    arcs: list[ArcSchema]


class OptimizationRequestSchema(RunRequestMetadata):
    """
    Schema for the optimization request sent to the solver
    """

    model_config = ConfigDict(from_attributes=True)

    customers: list[CustomerSchema]


class OptimizationResultSchema(RunResultMetadata):
    """
    Schema for the optimization result returned by the solver
    """

    model_config = ConfigDict(from_attributes=True)
    arcs: list[SolutionArcSchema]
