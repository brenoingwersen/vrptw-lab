# Frontend

Plotly Dash dashboard for [vrptw-lab](../README.md).

The dashboard is a read-only web UI. It talks to the backend API over HTTP — it does not run the solver or connect to the database directly.

---

## Stack

- **Dash** — web application framework
- **dash-bootstrap-components** — layout and styling
- **dash-ag-grid** — interactive runs table
- **Plotly** — route map visualization
- **httpx** — HTTP client for the API
- **uv** — dependency and environment management

---

## Features

| UI section | What it shows |
|---|---|
| **New run form** | Pick a dataset and instance, set max trucks, capacity, solver timeout, and random seed |
| **KPI row** | Total runs and counts by status (queued, running, failed) |
| **Runs table** | List and select runs (AG Grid) |
| **Solution panel** | Run metrics and an interactive route map |

The dashboard auto-refreshes every 30 seconds to pick up status changes from background solver jobs.

### Source layout

| Component | File |
|---|---|
| New run form | [src/dashboard/components/new_run_form.py](src/dashboard/components/new_run_form.py) |
| KPI row | [src/dashboard/components/kpi_row.py](src/dashboard/components/kpi_row.py) |
| Runs table | [src/dashboard/components/runs_table.py](src/dashboard/components/runs_table.py) |
| Solution summary | [src/dashboard/components/solution_summary_card.py](src/dashboard/components/solution_summary_card.py) |
| Route map | [src/dashboard/plot.py](src/dashboard/plot.py) |

---

## Running locally

The API and worker must be running first. See the [root README](../README.md) for the full setup.

```bash
# Infra + API + worker (from repo root)
docker compose up postgres db-init redis worker --build -d
cd backend && uv run backend

# Dashboard (separate terminal)
cd frontend && uv run frontend
```

| Environment | Dashboard URL |
|---|---|
| Local (`uv run frontend`) | http://localhost:8050 |
| Docker Compose | http://localhost:3000 |

When running locally, set `API_BASE_URL=http://localhost:8000` so the dashboard can reach the API.

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | Backend API URL |
| `REQUEST_TIMEOUT` | `10` | HTTP request timeout (seconds) |
| `REFRESH_INTERVAL_MS` | `30000` | Auto-refresh interval (milliseconds) |
| `DEBUG` | `false` | Enable Dash debug mode |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8050` | Bind port |

In Docker Compose, `API_BASE_URL` is set to `http://api:8000` automatically.

---

## Project structure

```
frontend/src/dashboard/
├── app.py           # Entry point
├── layout.py        # Page structure
├── api_client.py    # HTTP client for the API
├── settings.py      # Environment configuration
├── contracts.py     # Shared data types
├── plot.py          # Route map rendering
├── callbacks/       # Dash interactivity
│   ├── new_run_form.py
│   ├── kpi_row.py
│   ├── runs_table.py
│   ├── solution_panel.py
│   └── refresh.py
└── components/      # UI building blocks
    ├── new_run_form.py
    ├── kpi_row.py
    ├── runs_table.py
    └── solution_summary_card.py
```

---

## Related docs

- [Root README](../README.md) — full stack overview and Docker setup
- [Backend README](../backend/README.md) — API endpoints and solver
- [Data format](../data/README.md) — benchmark CSV schema
