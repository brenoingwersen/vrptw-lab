"""Pydantic schemas for API request and response contracts.

Schemas define data exchanged between the HTTP layer, ``Repository``,
``Solver``, and the frontend. They are not ORM models; see ``models.py`` for
database tables.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.models import RunStatus


class DatasetSchema(BaseModel):
    """One benchmark dataset (name and instance identifier)."""

    model_config = ConfigDict(from_attributes=True)
    name: str
    instance: str


class RunRequestMetadata(BaseModel):
    """Solver constraints and parameters shared by create and optimize requests."""

    # Constraints
    max_trucks: int = Field(..., gt=0)
    truck_capacity: int = Field(..., gt=0)

    # Solver parameters
    max_time_in_seconds: int | None = Field(default=None, gt=0)
    random_seed: int | None = None


class RunCreateRequest(RunRequestMetadata):
    """Payload for creating a new optimization run."""

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
    """Solver status, runtime, and objective values for a completed run."""

    status: RunStatus
    total_trucks: int | None
    total_distance: float | None
    runtime_seconds: float | None


class RunDetailResponse(RunCreateRequest, RunResultMetadata):
    """Run metadata returned by list, create, and detail endpoints."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str
    created_at: datetime | None
    finished_at: datetime | None


class CustomerSchema(BaseModel):
    """One customer node with coordinates, demand, and time window."""

    model_config = ConfigDict(from_attributes=True)

    cust_no: int
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int


class SolutionArcSchema(BaseModel):
    """One route segment with truck, sequence, and customer endpoints."""

    model_config = ConfigDict(from_attributes=True)

    truck_id: int
    sequence: int
    cust_no_from: int
    cust_no_to: int


class ArcSchema(BaseModel):
    """One route segment with resolved customer coordinates."""

    model_config = ConfigDict(from_attributes=True)

    truck_id: int
    sequence: int
    cust_from: CustomerSchema
    cust_to: CustomerSchema


class SolutionResponse(BaseModel):
    """Full solution for a run: metadata plus route arcs with coordinates."""

    model_config = ConfigDict(from_attributes=True)

    run: RunDetailResponse
    arcs: list[ArcSchema]


class OptimizationRequestSchema(RunRequestMetadata):
    """Input passed from ``Repository`` to ``Solver`` for one run."""

    model_config = ConfigDict(from_attributes=True)

    customers: list[CustomerSchema]


class OptimizationResultSchema(RunResultMetadata):
    """Output returned by ``Solver`` before persistence."""

    model_config = ConfigDict(from_attributes=True)
    arcs: list[SolutionArcSchema]
