from sqlmodel import Session, select

from api.models import Dataset


class DatasetsRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_datasets(self, limit: int | None = None) -> list[Dataset]:
        """
        List datasets from the database.
        """
        statement = select(Dataset)
        return (
            self.db.exec(statement).all()
            if limit is None
            else self.db.exec(statement).limit(limit).all()
        )

    def get_by_id(
        self,
        *,
        dataset_id: str,
    ) -> Dataset | None:
        statement = select(Dataset).where(Dataset.dataset_id == dataset_id)
        return self.db.exec(statement).first()

    def get_by_name_and_instance(
        self,
        *,
        name: str,
        instance: str,
    ) -> Dataset | None:
        statement = select(Dataset).where(
            Dataset.name == name, Dataset.instance == instance
        )
        return self.db.exec(statement).first()
