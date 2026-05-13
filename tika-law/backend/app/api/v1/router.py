from fastapi import APIRouter

from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.intake import router as intake_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(intake_router)
