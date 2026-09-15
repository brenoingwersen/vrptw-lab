from sqlmodel import Session, select

from api.mappers import to_dataset
from api.models import DatasetRecord
from domain import Dataset


class DatasetsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_datasets(self, limit: int | None = None) -> list[Dataset]:
        """
        List datasets from the database.
        """
        statement = select(DatasetRecord)
        dataset_records = (
            self.db.exec(statement).all()
            if limit is None
            else self.db.exec(statement).limit(limit).all()
        )
        return [to_dataset(dataset_record) for dataset_record in dataset_records]

    def get_by_id(
        self,
        *,
        dataset_id: str,
    ) -> Dataset | None:
        statement = select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id)
        dataset_record = self.db.exec(statement).first()
        return to_dataset(dataset_record) if dataset_record else None

    def get_by_name_and_instance(
        self,
        *,
        name: str,
        instance: str,
    ) -> Dataset | None:
        statement = select(DatasetRecord).where(
            DatasetRecord.name == name, DatasetRecord.instance == instance
        )
        dataset_record = self.db.exec(statement).first()
        return to_dataset(dataset_record) if dataset_record else None
