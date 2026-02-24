import sys
from pathlib import Path

# Add the project root to the path to ensure imports work correctly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from core.config import settings, validate_settings
from api.v1 import router as api_v1_router
from core.logger import setup_logger
from core.database import init_db
from core.workflow import brs_workflow

# Setup logger
logger = setup_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'brs_sasa_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'brs_sasa_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)
LLM_CALLS = Counter(
    'brs_sasa_llm_calls_total',
    'Total LLM API calls',
    ['provider', 'status']
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events
    """
    # Startup
    logger.info("Starting BRS-SASA application...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

    # Initialize workflow
    try:
        await brs_workflow.initialize()
        logger.info("Workflow initialized successfully")
    except Exception as e:
        logger.error(f"Workflow initialization failed: {str(e)}")
        raise

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
    try:
        await brs_workflow.close()
        logger.info("Workflow closed successfully")
    except Exception as e:
        logger.error(f"Error closing workflow: {str(e)}")

app = FastAPI(
    title="BRS-SASA: AI-Powered Conversational Platform",
    description="An intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information and Prometheus metrics"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request started: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {duration:.2f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - "
            f"Error: {str(e)} - Duration: {duration:.2f}s"
        )
        
        # Update error metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        
        raise

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

@app.get("/health/live")
async def liveness():
    """Liveness probe - checks if application is running"""
    return {
        "status": "alive",
        "timestamp": __import__('time').time()
    }

@app.get("/health/ready")
async def readiness():
    """Readiness probe - checks if application is ready to serve traffic"""
    checks = {}
    all_healthy = True
    
    # Check database
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        db.execute(__import__('sqlalchemy').text("SELECT 1"))
        db.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        all_healthy = False
    
    # Check ChromaDB
    try:
        from core.knowledge_base import knowledge_base
        if knowledge_base.initialized:
            checks["chromadb"] = "healthy"
        else:
            checks["chromadb"] = "not_initialized"
            all_healthy = False
    except Exception as e:
        checks["chromadb"] = f"unhealthy: {str(e)}"
        all_healthy = False
    
    # Check workflow
    try:
        if brs_workflow.workflow is not None:
            checks["workflow"] = "healthy"
        else:
            checks["workflow"] = "not_initialized"
            all_healthy = False
    except Exception as e:
        checks["workflow"] = f"unhealthy: {str(e)}"
        all_healthy = False
    
    status_code = 200 if all_healthy else 503
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": __import__('time').time()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )