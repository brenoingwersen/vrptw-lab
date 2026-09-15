import os
from collections.abc import Generator

from sqlmodel import Session, create_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://vrptw:vrptw@localhost:5432/vrptw",
)

engine = create_engine(DATABASE_URL, echo=True)


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session
