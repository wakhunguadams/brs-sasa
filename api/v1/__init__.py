from fastapi import APIRouter
from api.v1.endpoints import chat, health, documents

router = APIRouter()

# Include API endpoints
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])