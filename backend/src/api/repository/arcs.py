from dataclasses import asdict

from sqlmodel import Session, select

from api.models import ArcRecord, RunRecord, CustomerRecord
from domain import RouteArc
from domain import DashboardArc


class ArcsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, run_id: str, route_arcs: list[RouteArc]) -> bool:
        """
        Create the arcs in the ``arcs`` table for the given run.
        """
        arc_records = [
            ArcRecord(run_id=run_id, **asdict(route_arc)) for route_arc in route_arcs
        ]
        self.db.add_all(arc_records)
        self.db.commit()
        return True

    def get_run_dashboard_arcs(self, run_id: str) -> list[DashboardArc]:
        run_record = self.db.exec(
            select(RunRecord).where(RunRecord.run_id == run_id)
        ).first()

        arc_records = self.db.exec(
            select(ArcRecord).where(ArcRecord.run_id == run_id)
        ).all()

        customer_statement = select(CustomerRecord).where(
            CustomerRecord.dataset_id == run_record.dataset_id
        )

        customer_from_records = [
            self.db.exec(
                customer_statement.where(
                    CustomerRecord.cust_no == arc_record.cust_no_from
                )
            ).first()
            for arc_record in arc_records
        ]

        customer_to_records = [
            self.db.exec(
                customer_statement.where(
                    CustomerRecord.cust_no == arc_record.cust_no_to
                )
            ).first()
            for arc_record in arc_records
        ]

        return [
            DashboardArc(
                truck_id=arc_record.truck_id,
                sequence=arc_record.sequence,
                customer_from=customer_from_record,
                customer_to=customer_to_record,
            )
            for arc_record, customer_from_record, customer_to_record in zip(
                arc_records, customer_from_records, customer_to_records
            )
        ]
