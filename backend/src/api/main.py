from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from api.routers.runs import router as runs_router


def create_app() -> FastAPI:
    """
    App factory for the Optimization API.
    """
    app = FastAPI(
        title="VRPTW Lab API",
        version="0.1.0",
        docs_url="/docs",
    )

    @app.get("/")
    async def root():
        return RedirectResponse(url="/docs")

    setup_routers(app)

    return app


def setup_routers(app: FastAPI):
    app.include_router(runs_router)


app = create_app()
