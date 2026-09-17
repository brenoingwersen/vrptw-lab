#!/usr/bin/env bash
set -euo pipefail

docker-compose up postgres -d
# wait for healthy, then:
(cd backend && uv run uvicorn api.main:app --reload) &
(cd frontend && uv run dashboard) &
wait