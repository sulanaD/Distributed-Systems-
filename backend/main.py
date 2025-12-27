"""
FastAPI Banking System with Distributed Features
Combines tax calculator with banking, Redis caching, and Kafka event streaming
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import logging
import time

from config import settings
from database import init_db
from cache.redis_client import init_redis, close_redis
from kafka.producer import init_kafka, close_kafka
from routers import auth, accounts, transfers, tax
from monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    errors_total
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown"""
    logger.info("Starting FastAPI Banking System...")
    
    # Initialize database
    await init_db()
    logger.info("✓ Database initialized")
    
    # Initialize Redis
    await init_redis()
    logger.info("✓ Redis connected")
    
    # Initialize Kafka
    await init_kafka()
    logger.info("✓ Kafka connected")
    
    logger.info("🚀 All systems ready!")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down...")
    await close_redis()
    await close_kafka()
    logger.info("✓ Cleanup complete")

# Create FastAPI app
app = FastAPI(
    title="Distributed Banking System",
    description="Banking system with tax calculator, Redis caching, and Kafka event streaming",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    except Exception as e:
        # Record error
        errors_total.labels(
            error_type=type(e).__name__,
            endpoint=request.url.path
        ).inc()
        raise

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(transfers.router, prefix="/api/transfers", tags=["Transfers"])
app.include_router(tax.router, prefix="/api/tax", tags=["Tax Calculator"])

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "banking-api",
        "version": "2.0.0"
    }

# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Expose Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Distributed Banking System API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
