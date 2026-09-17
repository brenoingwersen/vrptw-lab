"""
Domain models for the optimization backend.

These models are used to represent the data across the different layers of the application.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RunStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    name: str
    instance: str


@dataclass(frozen=True)
class Customer:
    cust_no: int
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int


@dataclass(frozen=True)
class Run:
    run_id: str
    dataset_id: str
    created_at: datetime
    finished_at: datetime | None
    status: RunStatus
    max_trucks: int
    truck_capacity: int
    max_time_in_seconds: int
    random_seed: int | None
    total_trucks: int | None
    total_distance: float | None
    runtime_seconds: float | None


@dataclass(frozen=True)
class RouteArc:
    """Route arc – solver output."""

    truck_id: int
    sequence: int
    cust_no_from: int
    cust_no_to: int


@dataclass(frozen=True)
class Arc(RouteArc):
    """Persisted arc entity."""

    run_id: str


@dataclass(frozen=True)
class DashboardArc:
    truck_id: int
    sequence: int
    customer_from: Customer
    customer_to: Customer


@dataclass(frozen=True)
class OptimizationRequest:
    max_trucks: int
    truck_capacity: int
    max_time_in_seconds: int
    random_seed: int | None
    customers: list[Customer]


@dataclass(frozen=True)
class OptimizationResult:
    solver_status: int
    route_arcs: list[RouteArc]
    total_trucks: int | None
    total_distance: float | None
    runtime_seconds: float | None
