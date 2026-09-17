from fastapi import FastAPI

from api.routers.runs import router as runs_router
from api.routers.dashboard import router as dashboard_router


def create_app() -> FastAPI:
    """
    App factory for the Optimization API.
    """
    app = FastAPI(
        title="VRPTW Lab API",
        version="0.1.0",
        docs_url="/docs",
    )

    setup_routers(app)

    return app


def setup_routers(app: FastAPI):
    app.include_router(runs_router)
    app.include_router(dashboard_router)


app = create_app()
