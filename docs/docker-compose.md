# Docker and docker compose

### Stack example
**Example**: *dashboard (frontend) + API (backend)*

```text
┌─────────────────────────────────────────────────────────────┐
│  Your Mac (host)                                            │
│                                                             │
│  Browser → http://127.0.0.1:3000      (frontend)            │
│              │                                              │
│              │  compose ports: "3000:8050"                  │
│              ▼                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Docker network                                       │  │
│  │                                                       │  │
│  │  frontend container                                   │  │
│  │    Dash listens on 0.0.0.0:8050                       │  │
│  │         │                                             │  │
│  │         │  httpx server-side call                     │  │
│  │         ▼                                             │  │
│  │    http://api:8000                                    │  │
│  │         │                                             │  │
│  │         ▼                                             │  │
│  │  api container                     (backend)          │  │
│  │    uvicorn on 0.0.0.0:8000                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Browser can also hit API directly: http://127.0.0.1:8000   │
│              (via compose ports: "8000:8000")               │
└─────────────────────────────────────────────────────────────┘
```

**Example:** `docker-compose.yaml`

```yaml
services:
	api:
		build:
			context: backend
			dockerfile: Dockerfile
		depends_on:
			postgres:
				condition: service_healthy
		environment:
			DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-vrptw}:${POSTGRES_PASSWORD:-vrptw}@postgres:5432/${POSTGRES_DB:-vrptw}
		ports:
			- "8000:8000"
		healthcheck:
			test: 
				[
					"CMD",
					"python",
					"-c",
					"import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')",
				]
			interval: 5s
			timeout: 5s
			retries: 5
			start_period: 10s
	
	frontend:
		build:
			context: frontend
			dockerfile: Dockerfile
		depends_on:
			api:
			condition: service_healthy
		environment:
			API_BASE_URL: "http://api:8000"
			API_REQUEST_TIMEOUT: 10
		ports:
		- "3000:8050" # <browser (computer) port>:<container port>
```

**Address systems:**

| Who is calling                           | Address to use        | Port used                                                |
| ---------------------------------------- | --------------------- | -------------------------------------------------------- |
| **Browser** on machine                   | http://127.0.0.1:3000 | 3000 (left side of `ports` in the `docker-compose.yaml`) |
| **Other container** calling the frontend | http://frontend:8050  | 8050 (app's bind port)                                   |
| **Frontend** -> **Backend**              | http://api:8000       | 8000 (`uvicorn` inside API)                              |
| **Browser** -> **Backend**               | http://127.0.0.1:8000 | 8000 (left and right in the compose are the same)        |

> [!tip] 
> **Note:** The command to run the application (create an instance of `app` inside `app.py`) only needs to match the right side of the `port` mapping. 

**Mental model:**
1. `app.py` decides what address/port the process listens on inside the container (`0.0.0.0:8050`).
2. `docker-compose ports` bridges your Mac to that container port (`3000 → 8050`).
3. Docker DNS (`frontend`, `api`) lets containers talk on container ports, ignoring host ports.
4. Dockerfile starts the app; it does not publish or forward ports.