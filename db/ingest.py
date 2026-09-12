"""Ingest VRPTW dataset CSV files from disk into PostgreSQL."""

import hashlib
import os
import time
from pathlib import Path

import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

REQUIRED_COLUMNS = [
    "cust_no",
    "xcoord",
    "ycoord",
    "demand",
    "ready_time",
    "due_date",
    "service_time",
]

UPSERT_DATASET = text("""
    INSERT INTO datasets (id, name, instance)
    VALUES (:id, :name, :instance)
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        instance = EXCLUDED.instance
""")

UPSERT_INSTANCE = text("""
    INSERT INTO instances (
        dataset_id, cust_no, xcoord, ycoord,
        demand, ready_time, due_date, service_time
    )
    VALUES (
        :dataset_id, :cust_no, :xcoord, :ycoord,
        :demand, :ready_time, :due_date, :service_time
    )
    ON CONFLICT (dataset_id, cust_no) DO UPDATE SET
        xcoord = EXCLUDED.xcoord,
        ycoord = EXCLUDED.ycoord,
        demand = EXCLUDED.demand,
        ready_time = EXCLUDED.ready_time,
        due_date = EXCLUDED.due_date,
        service_time = EXCLUDED.service_time
""")


def make_dataset_id(name: str, instance: str) -> str:
    """Return a unique identifier hash for a dataset name and instance pair.

    Args:
        name: Dataset family name (e.g. ``solomon``).
        instance: Instance identifier within the dataset.

    Return:
        SHA-256 hex digest of ``name`` and ``instance``.
    """
    return hashlib.sha256(f"{name}:{instance}".encode()).hexdigest()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names to snake_case.

    Args:
        df: Input DataFrame whose columns will be renamed in place.

    Return:
        The same ``df`` with normalized column names.
    """
    df.columns = [
        col.strip().lower().replace(" ", "_").replace(".", "") for col in df.columns
    ]
    return df


def discover_csvs(data_dir: Path):
    """Recursively discover CSV files grouped by dataset directory.

    Args:
        data_dir: Root directory containing one subdirectory per dataset.

    Yields:
        A ``(name, instance, csv_path)`` tuple where ``name`` is the dataset
        directory name, ``instance`` is the CSV stem, and ``csv_path`` is the
        file path.
    """
    for dataset_dir in sorted(data_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        name = dataset_dir.name
        for csv_path in sorted(dataset_dir.rglob("*.csv")):
            yield name, csv_path.stem, csv_path


def create_engine_with_retry(url: str, retries: int = 10, delay: float = 2.0):
    """Create a SQLAlchemy engine, retrying until the database is reachable.

    Args:
        url: SQLAlchemy database URL.
        retries: Maximum number of connection attempts.
        delay: Seconds to wait between attempts.

    Return:
        A connected SQLAlchemy engine.

    Raises:
        OperationalError: If all ``retries`` attempts fail.
    """
    logger.info(
        f"Creating database engine for url={url} with retries={retries} and delay={delay}"
    )
    engine = create_engine(url)
    for attempt in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
    return engine


def ingest_csv(conn, name: str, instance: str, csv_path: Path) -> int:
    """Load a dataset instance CSV file into the database.

    Args:
        conn: Active database connection or transaction.
        name: Dataset family name.
        instance: Instance identifier within the dataset.
        csv_path: Path to the CSV file.

    Return:
        Number of customer rows upserted into the ``instances`` table.

    Raises:
        ValueError: If ``csv_path`` is missing required columns.
    """
    ds_id = make_dataset_id(name, instance)
    conn.execute(UPSERT_DATASET, {"id": ds_id, "name": name, "instance": instance})

    df = normalize_columns(pd.read_csv(csv_path))
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path}: missing columns {sorted(missing)}")

    rows = []
    for record in df[REQUIRED_COLUMNS].to_dict(orient="records"):
        cust_no = int(record["cust_no"])
        rows.append(
            {
                "dataset_id": ds_id,
                "cust_no": cust_no,
                "xcoord": int(record["xcoord"]),
                "ycoord": int(record["ycoord"]),
                "demand": int(record["demand"]),
                "ready_time": int(record["ready_time"]),
                "due_date": int(record["due_date"]),
                "service_time": int(record["service_time"]),
            }
        )

    conn.execute(UPSERT_INSTANCE, rows)
    return len(rows)


def main() -> None:
    """Ingest all CSV files under ``DATA_DIR`` into PostgreSQL."""
    database_url = os.environ["DATABASE_URL"]
    engine = create_engine_with_retry(database_url)
    total_datasets = 0
    total_rows = 0

    with engine.begin() as conn:
        for name, instance, csv_path in discover_csvs(DATA_DIR):
            row_count = ingest_csv(conn, name, instance, csv_path)
            total_datasets += 1
            total_rows += row_count
            logger.info(f"ingested {name}/{instance}: {row_count} customers")

    logger.info(f"done: {total_datasets} datasets, {total_rows} customer rows")


if __name__ == "__main__":
    main()
