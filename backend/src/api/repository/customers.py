from sqlmodel import Session, select

from api.models import CustomerRecord


class CustomersRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_dataset_id(self, dataset_id: str) -> list[CustomerRecord]:
        statement = select(CustomerRecord).where(
            CustomerRecord.dataset_id == dataset_id
        )
        return self.db.exec(statement).all()
