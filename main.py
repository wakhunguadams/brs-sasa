import sys
from pathlib import Path

# Add the project root to the path to ensure imports work correctly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from core.config import settings, validate_settings
from api.v1 import router as api_v1_router
from core.logger import setup_logger

# Setup logger
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events
    """
    # Startup
    logger.info("Starting BRS-SASA application...")

    # Validate settings on startup
    try:
        validate_settings()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down BRS-SASA application...")

app = FastAPI(
    title="BRS-SASA: AI-Powered Conversational Platform",
    description="An intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to BRS-SASA: AI-Powered Conversational Platform for Business Registration Service (BRS) of Kenya",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/info")
async def info():
    """Return application information and configuration (without sensitive data)"""
    return {
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
        "version": "1.0.0",
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "vector_db_type": settings.VECTOR_DB_TYPE,
        "timestamp": __import__('time').time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )