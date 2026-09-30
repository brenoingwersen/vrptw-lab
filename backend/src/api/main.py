"""FastAPI application entry point and Uvicorn runner."""

import uvicorn
from fastapi import FastAPI

from api.routers import router as api_router


def create_app() -> FastAPI:
    """Create and configure the VRPTW Lab API application.

    Returns:
        Configured FastAPI instance with API routes mounted.
    """
    app = FastAPI(
        title="VRPTW Lab API",
        version="0.1.0",
        docs_url="/docs",
    )

    setup_routers(app)

    return app


def setup_routers(app: FastAPI) -> None:
    """Mount the API router on the application.

    Args:
        app: FastAPI instance to configure.
    """
    app.include_router(api_router)


def main() -> None:
    """Run the API with Uvicorn and hot reload enabled."""
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


app = create_app()
