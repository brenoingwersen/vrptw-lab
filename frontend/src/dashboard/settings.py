import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MAX_CACHED_SOLUTIONS = int(os.getenv("MAX_CACHED_SOLUTIONS", "5"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10.0"))
REFRESH_INTERVAL_MS = int(os.getenv("REFRESH_INTERVAL_MS", "30000"))
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8050"))
