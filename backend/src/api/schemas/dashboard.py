from pydantic import BaseModel


class CustomerSchema(BaseModel):
    cust_no: int
    xcoord: int
    ycoord: int
    demand: int
    ready_time: int
    due_date: int
    service_time: int


class DashboardArcResponseSchema(BaseModel):
    truck_id: int
    sequence: int
    customer_from: CustomerSchema
    customer_to: CustomerSchema


class DatasetResponseSchema(BaseModel):
    name: str
    instance: str
