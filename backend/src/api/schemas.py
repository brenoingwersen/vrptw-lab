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
    # Constraints
    max_trucks: int = Field(..., gt=0)
    truck_capacity: int = Field(..., gt=0)

    # Solver parameters
    max_time_in_seconds: int | None = Field(default=None, gt=0)
    random_seed: int | None = None


class RunCreateRequest(RunRequestMetadata):
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
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    created_at: datetime | None
    finished_at: datetime | None


class CustomerSchema(BaseModel):
    """
    A full customer record
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
    model_config = ConfigDict(from_attributes=True)

    truck_id: int
    sequence: int
    cust_no_from: int
    cust_no_to: int


class ArcSchema(BaseModel):
    """
    One route segment with resolved customer coordinates
    """

    model_config = ConfigDict(from_attributes=True)

    truck_id: int
    sequence: int
    cust_from: CustomerSchema
    cust_to: CustomerSchema


class SolutionResponse(BaseModel):
    """
    A complete solution response with run details and route segments
    """

    model_config = ConfigDict(from_attributes=True)

    run: RunDetailResponse
    arcs: list[ArcSchema]


class OptimizationRequestSchema(RunRequestMetadata):
    """
    A request to optimize a run
    """

    model_config = ConfigDict(from_attributes=True)

    customers: list[CustomerSchema]


class OptimizationResultSchema(RunResultMetadata):
    model_config = ConfigDict(from_attributes=True)
    arcs: list[SolutionArcSchema]
