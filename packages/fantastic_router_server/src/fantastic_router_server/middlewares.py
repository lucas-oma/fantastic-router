"""
FastAPI middleware for API key validation
Handles authentication at the server level
"""

import os
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .api.auth import api_key_validator

class APIKeyMiddleware:
    """Middleware to handle API key validation"""
    
    def __init__(self, app, require_auth: bool = True, skip_paths: list = None):
        self.app = app
        self.require_auth = require_auth
        self.skip_paths = skip_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/health",
            "/favicon.ico"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip authentication for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            await self.app(scope, receive, send)
            return
        
        # Check for API key in headers
        api_key = request.headers.get("authorization")
        
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # Remove "Bearer " prefix
            
            # Validate API key
            user_info = api_key_validator.validate_api_key(api_key)
            
            if user_info:
                # Add user info to request state
                request.state.user = user_info
                request.state.api_key = api_key
                
                # Check rate limit
                if not api_key_validator.check_rate_limit(user_info["api_key_id"]):
                    response = JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Rate limit exceeded"}
                    )
                    await response(scope, receive, send)
                    return
                
                await self.app(scope, receive, send)
                return
        
        # If we require auth and no valid API key was provided
        if self.require_auth:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "API key required. If you are testing our scripts, you can set FR_API_KEY environment variable: export FR_API_KEY=your_api_key_here"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return
        
        # If auth is optional, continue without user info
        request.state.user = None
        request.state.api_key = None
        await self.app(scope, receive, send)

from fastapi import Depends

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from request state (set by middleware)"""
    return getattr(request.state, 'user', None)

def get_current_api_key(request: Request) -> Optional[str]:
    """Get current API key from request state (set by middleware)"""
    return getattr(request.state, 'api_key', None)

# FastAPI dependency functions
def get_current_user_dependency() -> Optional[Dict[str, Any]]:
    """FastAPI dependency to get current user from request state"""
    
    # Get the current request from context
    request = Request(scope={}, receive=None)
    return get_current_user(request)

def get_current_api_key_dependency() -> Optional[str]:
    """FastAPI dependency to get current API key from request state"""
    
    # Get the current request from context
    request = Request(scope={}, receive=None)
    return get_current_api_key(request) 