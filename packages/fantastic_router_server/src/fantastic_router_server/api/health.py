"""
Health check endpoints for Fantastic Router Server
Simple health monitoring and status endpoints
"""

from fastapi import APIRouter
from ..edition import VERSION, EDITION

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Fantastic Router",
        "version": VERSION,
        "edition": EDITION,
        "message": "LLM-powered intent router for web applications",
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "pong"}


@router.get("/version")
async def version():
    """Version information"""
    return {
        "version": VERSION,
        "edition": EDITION,
        "name": "Fantastic Router"
    }
