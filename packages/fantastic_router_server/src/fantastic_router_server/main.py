"""
Fantastic Router Server - FastAPI Application
LLM-powered intent router for web applications
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .edition import EDITION, VERSION
from .api.routes import router as api_router
from .api.health import router as health_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"🚀 Starting Fantastic Router Server v{VERSION} ({EDITION})")
    
    # Startup
    try:
        # Initialize dependency container (happens automatically on first request)
        logger.info("✅ Dependencies will be initialized on first request")
        yield
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Fantastic Router Server")


# Create FastAPI app
app = FastAPI(
    title="Fantastic Router",
    description="LLM-powered intent router for web applications",
    version=VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware in production
if os.getenv("APP_ENV") == "production":
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "localhost").split(",")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )


# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(api_router, prefix="/api/v1", tags=["Planning"])


# Additional endpoints for backward compatibility
@app.get("/about")
async def about():
    """About endpoint for backward compatibility"""
    return {
        "name": "Fantastic Router",
        "edition": EDITION,
        "version": VERSION,
        "description": "LLM-powered intent router for web applications"
    }


# No legacy endpoints - use /api/v1/plan instead!


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_ENV") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
