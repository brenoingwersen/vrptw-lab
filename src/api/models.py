from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from vrptw.run_status import RunStatus


class Dataset(SQLModel, table=True):
    """
    Datasets table model.

    PKs: (dataset_id)
    """

    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("name", "instance"),)

    dataset_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    instance: str

    instances: list["Instance"] = Relationship(back_populates="dataset")
    runs: list["Run"] = Relationship(back_populates="dataset")


class Instance(SQLModel, table=True):
    """
    Instances table model.

    PKs: (dataset_id, cust_no)
    """

    __tablename__ = "instances"

    dataset_id: str = Field(foreign_key="datasets.dataset_id", primary_key=True)
    cust_no: int = Field(primary_key=True)
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int

    dataset: Dataset = Relationship(back_populates="instances")


class Run(SQLModel, table=True):
    """
    Runs table model.

    PKs: (run_id)
    """

    __tablename__ = "runs"

    run_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    dataset_id: str = Field(foreign_key="datasets.dataset_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: RunStatus = Field(default=RunStatus.PENDING)
    max_trucks: int
    truck_capacity: int
    max_time_in_seconds: int
    random_seed: int | None = None
    total_trucks: int | None = None
    total_distance: float | None = None

    dataset: Dataset = Relationship(back_populates="runs")
    stops: list["Stop"] = Relationship(back_populates="run")


class Stop(SQLModel, table=True):
    """
    Stops table model.

    PKs: (run_id, cust_no_from, cust_no_to)
    """

    __tablename__ = "stops"

    run_id: str = Field(foreign_key="runs.run_id", primary_key=True)
    truck_id: int
    sequence: int
    cust_no_from: int = Field(primary_key=True)
    cust_no_to: int = Field(primary_key=True)

    run: Run = Relationship(back_populates="stops")
