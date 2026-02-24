from fastapi import APIRouter
from api.v1.endpoints import chat, health, feedback

router = APIRouter()

# Include API endpoints
router.include_router(chat.router, prefix="/chat")
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])