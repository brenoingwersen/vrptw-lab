set -euo pipefail

# 1. Start infrastructure
docker-compose up postgres db-init redis worker -d

# 2. Start API
(cd backend && uv run backend --reload) &

# 3. Start dashboard
(cd frontend && uv run frontend) &

wait