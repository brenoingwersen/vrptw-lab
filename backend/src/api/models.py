from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from domain import RunStatus


class DatasetRecord(SQLModel, table=True):
    """
    Datasets table model.

    PKs: (dataset_id)
    """

    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("name", "instance"),)

    dataset_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    instance: str

    customers: list["CustomerRecord"] = Relationship(back_populates="dataset")
    runs: list["RunRecord"] = Relationship(back_populates="dataset")


class CustomerRecord(SQLModel, table=True):
    """
    Customers table model

    PKs: (dataset_id, cust_no)
    """

    __tablename__ = "customers"

    dataset_id: str = Field(foreign_key="datasets.dataset_id", primary_key=True)
    cust_no: int = Field(primary_key=True)
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int

    dataset: DatasetRecord = Relationship(back_populates="customers")


class RunRecord(SQLModel, table=True):
    """
    Runs table model.

    PKs: (run_id)
    """

    __tablename__ = "runs"

    run_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    dataset_id: str = Field(foreign_key="datasets.dataset_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: RunStatus = Field(default=RunStatus.queued)
    max_trucks: int
    truck_capacity: int
    max_time_in_seconds: int
    random_seed: int | None = None
    total_trucks: int | None = None
    total_distance: float | None = None
    runtime_seconds: float | None = None

    dataset: DatasetRecord = Relationship(back_populates="runs")
    arcs: list["ArcRecord"] = Relationship(back_populates="run")


class ArcRecord(SQLModel, table=True):
    """
    Arcs table model.

    PKs: (run_id, cust_no_from, cust_no_to)
    """

    __tablename__ = "arcs"

    run_id: str = Field(foreign_key="runs.run_id", primary_key=True)
    truck_id: int
    sequence: int
    cust_no_from: int = Field(primary_key=True)
    cust_no_to: int = Field(primary_key=True)

    run: RunRecord = Relationship(back_populates="arcs")
