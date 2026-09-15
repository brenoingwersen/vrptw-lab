from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vrptw.run_status import RunStatus


class CreateRunSchema(BaseModel):
    """
    Schema for validating the data received through the API
    to create and execute a new optimization run.
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


class NewRunSchema(CreateRunSchema):
    """
    Schema for a new run.
    """

    dataset_id: str


class UpdateRunSchema(BaseModel):
    """
    Schema for updating a run.
    """

    run_id: str
    finished_at: datetime | None = None
    status: RunStatus | None = None
    total_trucks: int | None = None
    total_distance: float | None = None
