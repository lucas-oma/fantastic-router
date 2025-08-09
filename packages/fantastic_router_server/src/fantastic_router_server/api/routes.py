"""
API Routes for Fantastic Router Server
Defines the main endpoints for routing and planning functionality
"""

import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from fantastic_router_core import FantasticRouter
from fantastic_router_core.models.actions import ActionPlan
from .deps import get_router, get_settings


# Request/Response Models
class PlanRequest(BaseModel):
    """Request model for the /plan endpoint"""
    query: str = Field(..., description="Natural language query to route", min_length=1, max_length=500)
    user_id: Optional[str] = Field(None, description="Optional user ID for personalization")
    user_role: Optional[str] = Field(None, description="User role for RBAC filtering")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context data")
    max_alternatives: int = Field(default=3, ge=0, le=10, description="Maximum number of alternative routes")


class PlanResponse(BaseModel):
    """Response model for the /plan endpoint"""
    success: bool = Field(..., description="Whether the planning was successful")
    action_plan: Optional[Dict[str, Any]] = Field(None, description="Primary action plan")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative action plans")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    components: Dict[str, str] = Field(..., description="Component health status")
    timestamp: float = Field(..., description="Response timestamp")


class ValidateRequest(BaseModel):
    """Request model for route validation"""
    route: str = Field(..., description="Route to validate")
    parameters: Optional[Dict[str, str]] = Field(default_factory=dict, description="Route parameters")


class ValidateResponse(BaseModel):
    """Response model for route validation"""
    valid: bool = Field(..., description="Whether the route is valid")
    issues: List[str] = Field(default_factory=list, description="Validation issues if any")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


# Create router
router = APIRouter()

# TODO: check why settings not used
@router.post("/plan", response_model=PlanResponse)
async def plan_route(
    request: PlanRequest,
    background_tasks: BackgroundTasks,
    fantastic_router: FantasticRouter = Depends(get_router),
    settings: Dict[str, Any] = Depends(get_settings)
):
    """
    Plan a route based on natural language query
    
    This is the main endpoint that takes a user's natural language query
    and returns structured routing information including the target URL,
    confidence scores, and alternative options.
    """
    start_time = time.time()
    
    try:
        # Plan the action using our core router
        action_plan = await fantastic_router.plan(
            query=request.query,
            user_role=request.user_role,
            session_data=request.context
        )
        
        # Calculate performance metrics
        duration_ms = (time.time() - start_time) * 1000
        
        # Convert ActionPlan to dict for JSON serialization
        action_plan_dict = {
            "action_type": action_plan.action_type.value,
            "route": action_plan.route,
            "confidence": action_plan.confidence,
            "reasoning": action_plan.reasoning,
            "parameters": [
                {
                    "name": param.name,
                    "value": param.value,
                    "type": param.type,
                    "source": param.source
                }
                for param in action_plan.parameters
            ],
            "entities": [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "table": entity.table,
                    "confidence": entity.confidence,
                    "metadata": entity.metadata
                }
                for entity in action_plan.entities
            ],
            "query_params": action_plan.query_params,
            "matched_pattern": action_plan.matched_pattern
        }
        
        # Convert alternatives
        alternatives = []
        for alt in action_plan.alternatives[:request.max_alternatives]:
            alternatives.append({
                "action_type": alt.action_type.value,
                "route": alt.route,
                "confidence": alt.confidence,
                "reasoning": alt.reasoning
            })
        
        # Performance classification
        if duration_ms < 1000:
            perf_level = "excellent"
        elif duration_ms < 3000:
            perf_level = "good"
        elif duration_ms < 5000:
            perf_level = "acceptable"
        else:
            perf_level = "slow"
        
        # Log performance in background if needed
        background_tasks.add_task(
            log_performance,
            request.query,
            duration_ms,
            action_plan.confidence,
            perf_level
        )
        
        return PlanResponse(
            success=True,
            action_plan=action_plan_dict,
            alternatives=alternatives,
            performance={
                "duration_ms": round(duration_ms, 2),
                "level": perf_level,
                "llm_calls": 1,  # From our single-call optimization
                "cache_hits": 0  # TODO: Implement caching
            },
            metadata={
                "query_length": len(request.query),
                "user_id": request.user_id,
                "user_role": request.user_role,
                "timestamp": start_time
            }
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Log error in background
        background_tasks.add_task(
            log_error,
            request.query,
            str(e),
            duration_ms
        )
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Planning failed",
                "message": str(e),
                "duration_ms": round(duration_ms, 2)
            }
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    fantastic_router: FantasticRouter = Depends(get_router)
):
    """
    Health check endpoint
    
    Returns the current status of all system components including
    LLM connectivity, database connectivity, and overall service health.
    """
    from ..edition import VERSION
    
    components = {}
    overall_status = "healthy"
    
    # Check database connectivity
    try:
        db_client = fantastic_router.db_client
        # Test connection (this should be a quick check)
        if hasattr(db_client, 'test_connection'):
            db_healthy = await db_client.test_connection()
            components["database"] = "healthy" if db_healthy else "unhealthy"
            if not db_healthy:
                overall_status = "degraded"
        else:
            components["database"] = "unknown"
    except Exception as e:
        components["database"] = f"error: {str(e)[:50]}"
        overall_status = "degraded"
    
    # Check LLM connectivity (lightweight check)
    try:
        llm_client = fantastic_router.llm_client
        # For mock clients, we know they're working
        if hasattr(llm_client, '__class__') and 'Mock' in llm_client.__class__.__name__:
            components["llm"] = "mock"
        else:
            components["llm"] = "available"
    except Exception as e:
        components["llm"] = f"error: {str(e)[:50]}"
        overall_status = "degraded"
    
    # Check configuration
    try:
        config = fantastic_router.config
        if config and isinstance(config, dict) and "domain" in config:
            components["configuration"] = "loaded"
        else:
            components["configuration"] = "default"
    except Exception as e:
        components["configuration"] = f"error: {str(e)[:50]}"
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=VERSION,
        components=components,
        timestamp=time.time()
    )


@router.post("/validate", response_model=ValidateResponse)
async def validate_route(
    request: ValidateRequest,
    fantastic_router: FantasticRouter = Depends(get_router)
):
    """
    Validate a specific route
    
    Checks if a given route pattern is valid and provides suggestions
    for improvement if needed.
    """
    try:
        route = request.route.strip()
        issues = []
        suggestions = []
        
        # Basic validation
        if not route:
            issues.append("Route cannot be empty")
        elif not route.startswith('/'):
            issues.append("Route should start with /")
            suggestions.append("Add leading slash to route")
        
        # Check for common patterns
        if '{' in route and '}' not in route:
            issues.append("Unclosed parameter bracket")
        elif '}' in route and '{' not in route:
            issues.append("Unopened parameter bracket")
        
        # Check against known patterns
        config = fantastic_router.config
        if isinstance(config, dict) and "route_patterns" in config:
            known_patterns = [p.get("pattern", "") for p in config["route_patterns"]]
            if route not in known_patterns:
                suggestions.append("Route not found in configured patterns")
                suggestions.extend([f"Similar: {p}" for p in known_patterns[:3]])
        
        valid = len(issues) == 0
        
        return ValidateResponse(
            valid=valid,
            issues=issues,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/stats")
async def get_stats(
    settings: Dict[str, Any] = Depends(get_settings)
):
    """
    Get system statistics
    
    Returns basic usage and performance statistics.
    """
    # TODO: Implement actual statistics tracking
    return {
        "requests_total": 0,
        "avg_response_time_ms": 0,
        "avg_confidence": 0,
        "top_queries": [],
        "error_rate": 0,
        "uptime_seconds": 0
    }


# Background task functions
async def log_performance(query: str, duration_ms: float, confidence: float, level: str):
    """Log performance metrics in background"""
    # TODO: Implement actual logging to database or monitoring system
    print(f"PERF: {level} | {duration_ms:.0f}ms | conf={confidence:.2f} | query='{query[:50]}...'")


async def log_error(query: str, error: str, duration_ms: float):
    """Log errors in background"""
    # TODO: Implement actual error logging
    print(f"ERROR: {duration_ms:.0f}ms | '{query[:50]}...' | {error}")


# Include router in main app
def get_router() -> APIRouter:
    """Get the configured API router"""
    return router
