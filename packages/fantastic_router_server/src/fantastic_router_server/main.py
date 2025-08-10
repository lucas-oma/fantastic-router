"""
Fantastic Router Server - FastAPI Application
LLM-powered intent router for web applications
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Fantastic Router Server...")
    print("✅ Fantastic Router Server started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Fantastic Router Server...")
    print("✅ Fantastic Router Server shutdown complete!")


# Create FastAPI app
app = FastAPI(
    title="Fantastic Router API",
    description="LLM-powered intent router for web applications",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(router, prefix="/api/v1", tags=["routing"])
