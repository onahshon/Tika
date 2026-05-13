from fastapi import APIRouter

from backend.app.api.v1.router import router as v1_router
from backend.app.core.config import settings

api_router = APIRouter()
api_router.include_router(v1_router, prefix=settings.api_v1_prefix)


@api_router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
