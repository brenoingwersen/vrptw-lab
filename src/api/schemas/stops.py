from pydantic import BaseModel


class NewStopSchema(BaseModel):
    truck_id: int
    sequence: int
    cust_no_from: int
    cust_no_to: int
