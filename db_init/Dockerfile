FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir pandas sqlalchemy "psycopg[binary]" loguru

COPY db_init/ingest.py db_init/ingest.py

CMD ["python", "db_init/ingest.py"]
