from dataclasses import asdict

from sqlmodel import Session

from api.models import ArcRecord
from domain import RouteArc


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
