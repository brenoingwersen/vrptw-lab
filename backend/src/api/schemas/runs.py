from datetime import datetime

from pydantic import BaseModel, ConfigDict

from domain import RunStatus


class RunRequestSchema(BaseModel):
    """
    Schema for validating the data received through the API
    to create and queue an optimization run.
    """

    model_config = ConfigDict(
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
        }
    )

    name: str
    instance: str
    max_trucks: int
    truck_capacity: int
    max_time_in_seconds: int | None = None
    random_seed: int | None = None


class RunResponseSchema(BaseModel):
    """
    Schema for the response of an optimization run.
    """

    run_id: str
    created_at: datetime
    finished_at: datetime | None
    status: RunStatus
    total_trucks: int | None
    total_distance: float | None
    runtime_seconds: float | None
    max_trucks: int
    truck_capacity: int
    max_time_in_seconds: int | None = None
    random_seed: int | None = None
