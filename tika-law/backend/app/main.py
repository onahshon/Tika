from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.config import settings

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI-powered lead qualification for Israeli employment-law attorneys.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    if FRONTEND_DIR.exists():
        app.mount("/widget", StaticFiles(directory=FRONTEND_DIR), name="widget")

        @app.get("/widget-test", include_in_schema=False)
        def widget_test() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "test.html")

    return app


app = create_app()
