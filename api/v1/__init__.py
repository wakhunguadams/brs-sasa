from fastapi import APIRouter
from api.v1.endpoints import chat, health

router = APIRouter()

# Include API endpoints
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(health.router, prefix="/health", tags=["health"])