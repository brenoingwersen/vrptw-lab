from sqlmodel import Session, select

from api.models import Instance


class InstancesRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_dataset_id(self, dataset_id: str) -> list[Instance]:
        statement = select(Instance).where(Instance.dataset_id == dataset_id)
        return self.db.exec(statement).all()
