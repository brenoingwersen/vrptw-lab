# vrptw-lab
A platform for solving, benchmarking, and analyzing Vehicle Routing Problems, starting with the Solomon VRPTW benchmark.

## Running locally
### Option 1: Docker compose
Simply let docker compose handle the initialization:
```bash
docker-compose up --build
```

### Option 2: Build each service alone
**1. Backend (PostgreSQL DB):**
Create the DB and add the benchmark data using the `db-init` service:
```bash
docker-compose up postgres db-init --build -d
```

**2. Deploying the API:**
```bash
cd backend && uv run backend
```

**3. Deploying the frontend (dashboard):**
```bash
cd frontend && uv run frontend
```