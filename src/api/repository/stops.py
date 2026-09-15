from sqlmodel import Session, select

from api.models import Stop
from api.schemas.stops import NewStopSchema


class StopsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_stops(self, run_id: str) -> list[Stop]:
        statement = select(Stop).where(Stop.run_id == run_id)
        return self.db.exec(statement).all()

    def create(self, run_id: str, stops: list[NewStopSchema]) -> bool:
        """
        Create the stops in the ``stops`` table for the given run.
        """
        stops_models = [Stop(**stop.model_dump(), run_id=run_id) for stop in stops]
        self.db.add_all(stops_models)
        self.db.commit()
        return True
