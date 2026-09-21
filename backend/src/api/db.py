import os
from collections.abc import Generator

from sqlmodel import Session, create_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://vrptw:vrptw@localhost:5432/vrptw",
)

# echo = True tells SQLAlchemy to log every
# SQL statement through python's logging module.
engine = create_engine(DATABASE_URL, echo=False)


def get_db() -> Generator[Session]:
    """
    Get a session connected to the database.
    """
    with Session(engine) as session:
        yield session
