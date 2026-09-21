import uvicorn
from fastapi import FastAPI

from api.routers import router as api_router


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
    app.include_router(api_router)


def main() -> None:
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


app = create_app()
