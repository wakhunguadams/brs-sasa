from fastapi import APIRouter
from typing import Dict
import time

router = APIRouter()

@router.get("/")
async def health_check() -> Dict:
    """
    Health check endpoint to verify the application is running
    """
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "service": "brs-sasa-api"
    }

@router.get("/ready")
async def readiness_check() -> Dict:
    """
    Readiness check endpoint to verify the application is ready to serve requests
    """
    # Here we could add checks for database connectivity, external services, etc.
    return {
        "status": "ready",
        "timestamp": int(time.time()),
        "service": "brs-sasa-api"
    }