# Backend

REST API, VRPTW solver, and Celery worker for [vrptw-lab](../README.md).

The backend handles everything between the dashboard and the database: HTTP endpoints, background job orchestration, and the OR-Tools optimization engine. The solver is kept separate from FastAPI and Celery — it has no web or task-queue imports inside [src/api/optimizer/](src/api/optimizer/).

---

## Stack

- **FastAPI** — REST API and OpenAPI docs
- **SQLModel** — ORM and data models
- **PostgreSQL** — persistent storage
- **Celery + Redis** — async solver jobs
- **OR-Tools CP-SAT** — VRPTW optimization engine
- **Loguru** — structured logging
- **uv** — dependency and environment management

---

## API endpoints

Base URL: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/datasets` | List available benchmark instances |
| GET | `/runs` | List all optimization runs |
| POST | `/runs` | Create a run and enqueue a solver job |
| GET | `/runs/{run_id}` | Run status, config, and metrics |
| GET | `/runs/{run_id}/solution` | Full solution with route arcs and customer coordinates |

### Run lifecycle

```
queued → running → completed
                 ↘ failed
```

Creating a run via `POST /runs` saves it to the database and enqueues a Celery task. The worker picks up the job, runs the solver, and writes the result back to Postgres.

---

## Solver

The VRPTW solver uses a two-stage CP-SAT approach ([src/api/optimizer/solver.py](src/api/optimizer/solver.py)):

1. **Stage 1** — minimize the number of trucks used.
2. **Stage 2** — fix the truck count from stage 1, then minimize total travel distance.

Each stage uses Google OR-Tools constraint programming. Solutions are validated before being stored.

---

## Project structure

```
backend/src/api/
├── main.py          # FastAPI app entry point
├── routers.py       # HTTP routes
├── service.py       # Business logic
├── repository.py    # Database access
├── tasks.py         # Celery task wrapper
├── celery_app.py    # Worker configuration
├── models.py        # SQLModel tables
├── schemas.py       # Request/response models
├── db.py            # Database session setup
└── optimizer/       # VRPTW solver (OR-Tools)
    ├── solver.py
    ├── instance.py
    ├── constraints.py
    ├── variables.py
    └── ...
```

---

## Running locally

Start the required infrastructure from the repo root, then run the API:

```bash
# From repo root — Postgres, data ingest, Redis, and worker
docker compose up postgres db-init redis worker --build -d

# Start the API
cd backend && uv run backend
```

The API starts at http://localhost:8000 with hot reload enabled.

---

## Environment variables

| Variable | Default | Used by |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://vrptw:vrptw@postgres:5432/vrptw` | api, worker |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | api, worker |

When running the API outside Docker, point `DATABASE_URL` at `localhost:5432` and `CELERY_BROKER_URL` at `localhost:6379`.

---

## Dev tooling

Install dev dependencies and run the linter:

```bash
cd backend
uv sync --group dev
uv run ruff check .
```

---

## Related docs

- [Root README](../README.md) — full stack overview and Docker setup
- [Frontend README](../frontend/README.md) — dashboard that consumes this API
- [Data format](../data/README.md) — benchmark CSV schema
