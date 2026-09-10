# VRPTW Project Plan

## Project Overview

This project is a local, full-stack optimization application for solving Vehicle Routing Problems with Time Windows (VRPTW).

The project is intentionally designed as a complete application rather than only an optimization-modeling exercise. The project combines an optimization engine with an API, asynchronous job
execution, persistent results, a dashboard, and observability.

The initial problem data is based on Solomon VRPTW benchmark instances, but the architecture should allow custom datasets to be introduced later.

### Stack
- **Python / `uv`** — environment and dependency management
- **FastAPI** — optimization API and Swagger/OpenAPI UI
- **OR-Tools / CP-SAT** — VRPTW optimization engine
- **PostgreSQL** — persistence
- **Celery + Redis/broker** — asynchronous optimization jobs
- **Plotly + Dash** — results dashboard
- **Prometheus + Grafana** — instrumentation and monitoring
- **Docker Compose** — orchestration of the entire application

The application should be runnable locally using Docker for infrastructure components and `uv` for Python environment/dependency management.

### Main Goals

The project should demonstrate a complete workflow:

```text
Input Instance
      |
      v
   API Request
      |
      v
   Queue / Job
      |
      v
  VRPTW Solver
      |
      +------------------+
      |                  |
      v                  v
   Run Metadata       Solution
      |                  |
      +--------+---------+
               |
               v
          PostgreSQL
               |
               v
        Dashboard / API
               |
               v
       Analysis / Visualization
```

### Docker compose
Everything must be orchestrated from a single `docker-compose.yml` file.

The Compose environment should include all required application and infrastructure services, such as:
- FastAPI
- Celery worker
- PostgreSQL
- Redis/broker
- Dash
- Prometheus
- Grafana

A developer should be able to start the complete application stack locally through the single Compose entry point.

Avoid requiring separate orchestration mechanisms for different parts of the application.

### Persistence
PostgreSQL stores:
- Datasets / instances — VRPTW input data
- Runs — individual solver executions and their configuration/status
- Metrics — objective, runtime, vehicle usage, distance, solver statistics, etc.
- Routes — the solution produced by each run

Prefer simple relational structures that are easy to query and inspect.

Avoid deeply nested data structures or storing core analytical data as opaque
JSON.

### Optimization
The solver should be independent from FastAPI, Celery, Dash, and PostgreSQL.

It should operate on explicit VRPTW domain structures and return a structured solution containing routes and relevant metrics.

The model should be tested independently with small instances covering feasibility, capacity, time windows, depot behavior, and multiple vehicles.

### API & Jobs
A typical workflow is:
```text
POST /runs
    ↓
create run
    ↓
enqueue Celery job
    ↓
worker executes OR-Tools
    ↓
persist metrics + routes
    ↓
run becomes OPTIMAL / FEASIBLE / INFEASIBLE / UNKNOWN (timeout)
```

PostgreSQL is the source of truth for run state and results.

### Dashboard
Dash should query persisted data and provide:
- Run listing/filtering/sorting
- Run comparison
- Metric visualizations
- Individual run inspection
- Route/solution visualization

The dashboard should analyze results, not execute optimization logic.

### Architectural principles
- **Keep it simple**. This is a complete **local project**, not a distributed production platform.
- **Separate concerns**. Domain, optimization, API, persistence, workers, and dashboard should remain reasonably independent.
- Prefer **explicit structures** over deeply nested dictionaries/JSON.
- Keep the **solver independent** from infrastructure.
- Use **PostgreSQL as the source of truth** for runs and solutions.
- **Avoid premature abstraction**. Don't introduce generic frameworks or patterns without a concrete need.
- **Prefer incremental changes** over unnecessary rewrites.
- Everything must remain **runnable locally** with **open source technology** through the single Docker Compose environment.

### Development priority
The primary objective is to demonstrate a clean, complete workflow from **VRPTW instance → optimization job → persisted solution → API/dashboard analysis**, while keeping the architecture understandable and intentionally small.

The development plan is to build from the core outward:
```text
VRPTW domain
    ↓
Input loading/validation
    ↓
CP-SAT solver + tests
    ↓
PostgreSQL
    ↓
Persistence/run orchestration
    ↓
FastAPI
    ↓
Celery + Redis
    ↓
Dash
    ↓
Prometheus + Grafana
    ↓
Docker Compose integration
```

## Definition of done
The project should eventually support the following complete workflow:
1. A VRPTW instance exists in the database.
2. An user runs `docker-compose`
3. A client submits an optimization request.
4. The API creates a run.
5. The run is queued through Celery.
6. A worker loads the instance and executes the OR-Tools solver.
7. The worker records:
   - run status
   - solver configuration
   - runtime
   - objective
   - metrics
   - routes
8. The API exposes the persisted run.
9. The dashboard lists the run.
10. The user can compare it against previous runs.
11. The user can select the run.
12. The dashboard displays:
    - run metadata
    - metrics
    - objective
    - vehicle usage
    - routes
    - route visualization
13. Prometheus collects relevant application and optimization metrics.
14. Grafana provides an operational view of the system.