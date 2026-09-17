from dataclasses import asdict

from ortools.sat.python import cp_model

from api.models import CustomerRecord, DatasetRecord, RunRecord
from api.schemas.runs import PlainRunResponseSchema, RunResponseSchema
from domain import Customer, Dataset, Run, RunStatus


def to_run(run_record: RunRecord) -> Run:
    return Run(
        run_id=run_record.run_id,
        dataset_id=run_record.dataset_id,
        created_at=run_record.created_at,
        finished_at=run_record.finished_at,
        status=run_record.status,
        max_trucks=run_record.max_trucks,
        truck_capacity=run_record.truck_capacity,
        total_trucks=run_record.total_trucks,
        total_distance=run_record.total_distance,
        max_time_in_seconds=run_record.max_time_in_seconds,
        random_seed=run_record.random_seed,
        runtime_seconds=run_record.runtime_seconds,
    )


def to_customer(customer_record: CustomerRecord) -> Customer:
    return Customer(
        cust_no=customer_record.cust_no,
        xcoord=customer_record.xcoord,
        ycoord=customer_record.ycoord,
        demand=customer_record.demand,
        ready_time=customer_record.ready_time,
        due_date=customer_record.due_date,
        service_time=customer_record.service_time,
    )


def to_dataset(dataset_record: DatasetRecord) -> Dataset:
    return Dataset(
        dataset_id=dataset_record.dataset_id,
        name=dataset_record.name,
        instance=dataset_record.instance,
    )


def to_plain_run_response(
    run_record: RunRecord, dataset_record: DatasetRecord
) -> PlainRunResponseSchema:
    return PlainRunResponseSchema(
        run_id=run_record.run_id,
        name=dataset_record.name,
        instance=dataset_record.instance,
        created_at=run_record.created_at,
        finished_at=run_record.finished_at,
        status=run_record.status,
    )


def run_to_run_response(run: Run) -> RunResponseSchema:
    return RunResponseSchema(**asdict(run))


def solver_status_to_run_status(solver_status: int) -> RunStatus:
    if solver_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return RunStatus.completed
    return RunStatus.failed
