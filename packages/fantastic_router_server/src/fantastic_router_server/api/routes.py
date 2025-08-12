"""
API Routes for Fantastic Router Server
Defines the main endpoints for routing and planning functionality
"""

import time
import hashlib
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from fantastic_router_core import FantasticRouter
from fantastic_router_core.models.actions import ActionPlan
from .deps import get_router, get_settings

# Dual caching system: Request cache + Structural cache
# TODO: use redis instead of in-memory cache
_request_cache: Dict[str, Dict[str, Any]] = {}
_request_cache_ttl: Dict[str, float] = {}
_structural_cache: Dict[str, Dict[str, Any]] = {}
_structural_cache_ttl: Dict[str, float] = {}

CACHE_TTL_SECONDS = 300  # 5 minutes
STRUCTURAL_CACHE_TTL_SECONDS = 1800  # 30 minutes (longer for structural patterns)

def _extract_structural_pattern(query: str, action_plan: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
    """
    Extract structural pattern from query and action plan.
    Returns (pattern_key, entity_mapping)
    
    Example:
    Query: "show me Michael's properties" or "michaels properties"
    Action: "/landlords/michael-123/properties"
    Pattern: "show me {PERSON}'s properties" -> "/landlords/{PERSON_ID}/properties"
    """
    
    # Only create structural patterns for valid routes
    route = action_plan.get('route', '')
    if not route or '{' in route:
        # Don't create structural patterns for invalid routes
        return "", {}
    
    # Common entity patterns to recognize
    entity_patterns = {
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\'s\b': 'PERSON',  # Michael's, John Smith's
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b': 'PERSON',     # Michael, John Smith
        r'\b(\d+)\b': 'NUMBER',                                 # 123, 456
        r'\b([A-Za-z]+)\b': 'WORD'                             # properties, income
    }
    
    # Normalize query for better pattern matching
    normalized_query = _normalize_query(query)
    pattern_query = normalized_query
    entity_mapping = {}
    
    # Replace entities with placeholders
    for regex, entity_type in entity_patterns.items():
        matches = re.finditer(regex, normalized_query)
        for i, match in enumerate(matches):
            entity_value = match.group(1)
            placeholder = f"{{{entity_type}_{i}}}"
            pattern_query = pattern_query.replace(entity_value, placeholder)
            entity_mapping[placeholder] = entity_value
    
    # Extract route pattern
    pattern_route = route
    
    # Replace entity IDs with placeholders
    if 'entities' in action_plan:
        for i, entity in enumerate(action_plan['entities']):
            entity_id = entity.get('id', '')
            if entity_id and entity_id in route:
                placeholder = f"{{ENTITY_ID_{i}}}"
                pattern_route = pattern_route.replace(entity_id, placeholder)
                entity_mapping[placeholder] = entity_id
    
    # Create structural key
    structural_key = f"{pattern_query}|{pattern_route}"
    
    # Validate that the pattern doesn't have unresolved placeholders
    if '{' in pattern_route and 'ENTITY_ID_' not in pattern_route:
        print(f"⚠️  Skipping structural pattern - unresolved placeholders in route: {pattern_route}")
        return "", {}
    
    return structural_key, entity_mapping

def _normalize_query(query: str) -> str:
    """
    Normalize query to handle various natural language variations
    """
    # Convert to lowercase
    normalized = query.lower().strip()
    
    # Remove common filler words that don't affect meaning
    filler_words = {
        'show me', 'show', 'get', 'find', 'look up', 'search for',
        'display', 'view', 'see', 'give me', 'bring up'
    }
    
    for filler in filler_words:
        if normalized.startswith(filler + ' '):
            normalized = normalized[len(filler):].strip()
            break
    
    # Handle possessive variations
    # "michaels properties" -> "michael's properties"
    normalized = re.sub(r'(\w+)s\s+(\w+)', r"\1's \2", normalized)
    
    # Handle common contractions and variations
    normalized = re.sub(r'\b(properties|property)\b', 'properties', normalized)
    normalized = re.sub(r'\b(income|earnings|salary)\b', 'income', normalized)
    normalized = re.sub(r'\b(contact|info|information)\b', 'contact', normalized)
    
    return normalized

def _generate_request_cache_key(query: str, user_id: Optional[str], user_role: Optional[str]) -> str:
    """Generate cache key for exact request matching"""
    cache_data = {
        "query": query.lower().strip(),
        "user_id": user_id,
        "user_role": user_role
    }
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_str.encode()).hexdigest()

def _get_cached_response(cache_key: str, cache_type: str = "request") -> Optional[Dict[str, Any]]:
    """Get cached response if available and not expired"""
    cache = _request_cache if cache_type == "request" else _structural_cache
    ttl_cache = _request_cache_ttl if cache_type == "request" else _structural_cache_ttl
    
    if cache_key not in cache:
        return None
    
    # Check TTL
    if time.time() > ttl_cache[cache_key]:
        # Expired, remove from cache
        del cache[cache_key]
        del ttl_cache[cache_key]
        return None
    
    return cache[cache_key]

def _cache_response(cache_key: str, response: Dict[str, Any], cache_type: str = "request"):
    """Cache the response with appropriate TTL"""
    try:
        # Deep copy and serialize the response to handle UUIDs and other non-serializable objects
        import copy
        import uuid
        
        def serialize_value(obj):
            """Recursively serialize objects, handling UUIDs and other special types"""
            if isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_value(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            else:
                return obj
        
        # Serialize the response
        serialized_response = serialize_value(response)
        
        cache = _request_cache if cache_type == "request" else _structural_cache
        ttl_cache = _request_cache_ttl if cache_type == "request" else _structural_cache_ttl
        ttl_seconds = CACHE_TTL_SECONDS if cache_type == "request" else STRUCTURAL_CACHE_TTL_SECONDS
        
        cache[cache_key] = serialized_response
        ttl_cache[cache_key] = time.time() + ttl_seconds
        
    except Exception as e:
        print(f"❌ Failed to cache response: {e}")
        # Don't fail the request if caching fails
        pass

def _apply_structural_cache(query: str, structural_key: str, entity_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Apply structural cache by replacing placeholders with actual values
    """
    try:
        cached = _get_cached_response(structural_key, "structural")
        if not cached:
            return None
        
        # Deep copy to avoid modifying the original cache
        response = copy.deepcopy(cached)
        
        # Convert to string for replacement
        response_str = json.dumps(response)
        
        # Replace placeholders with actual values
        for placeholder, value in entity_mapping.items():
            response_str = response_str.replace(placeholder, str(value))
        
        # Convert back to dict
        try:
            reconstructed_response = json.loads(response_str)
            
            # Validate that the reconstructed route is valid
            route = reconstructed_response.get('action_plan', {}).get('route', '')
            if route and '{' in route:
                print(f"⚠️  Structural cache reconstruction failed - route still has placeholders: {route}")
                return None
            
            return reconstructed_response
            
        except json.JSONDecodeError:
            print(f"❌ Failed to deserialize structural cache response")
            return None
            
    except Exception as e:
        print(f"❌ Failed to apply structural cache: {e}")
        return None

def _matches_structural_pattern(query: str, pattern_query: str) -> bool:
    """
    Check if a query matches a structural pattern
    """
    # Normalize both queries for comparison
    query_normalized = _normalize_query(query)
    pattern_normalized = _normalize_query(pattern_query)
    
    # Simple pattern matching - check if structure is similar
    # This is a basic implementation - could be enhanced with more sophisticated NLP
    
    # Count words and check if structure is similar
    query_words = query_normalized.split()
    pattern_words = pattern_normalized.split()
    
    if len(query_words) != len(pattern_words):
        return False
    
    # Check if non-placeholder words match
    for i, (query_word, pattern_word) in enumerate(zip(query_words, pattern_words)):
        if not pattern_word.startswith('{') and not pattern_word.endswith('}'):
            # This is not a placeholder, so it should match exactly
            if query_word != pattern_word:
                return False
    
    return True

def _extract_entities_from_query(query: str, pattern_query: str) -> Dict[str, str]:
    """
    Extract entities from query based on pattern
    """
    entity_mapping = {}
    
    # Normalize both queries
    query_normalized = _normalize_query(query)
    pattern_normalized = _normalize_query(pattern_query)
    
    query_words = query_normalized.split()
    pattern_words = pattern_normalized.split()
    
    for i, (query_word, pattern_word) in enumerate(zip(query_words, pattern_words)):
        if pattern_word.startswith('{') and pattern_word.endswith('}'):
            # This is a placeholder, extract the corresponding entity
            placeholder = pattern_word
            entity_mapping[placeholder] = query_word
    
    return entity_mapping

def _validate_route(route: str, route_patterns: List[Dict[str, Any]]) -> Tuple[bool, str, str]:
    """
    Validate if a route matches any defined pattern.
    Returns (is_valid, matched_pattern, error_message)
    """
    if not route or not route.startswith('/'):
        return False, "", "Route must start with '/'"
    
    # Check against each defined pattern
    for pattern_data in route_patterns:
        # Handle both dict and Pydantic objects
        if hasattr(pattern_data, 'pattern'):
            # Pydantic object
            pattern = pattern_data.pattern
        else:
            # Dictionary
            pattern = pattern_data.get('pattern', '')
            
        if not pattern:
            continue
            
        # Convert pattern to regex for matching
        regex_pattern = _pattern_to_regex(pattern)
        if regex_pattern and re.match(regex_pattern, route):
            return True, pattern, ""
    
    return False, "", f"Route '{route}' doesn't match any defined patterns"

def _pattern_to_regex(pattern: str) -> str:
    """
    Convert route pattern to regex for validation.
    Example: "/{entity_type}/{entity_id}/{view_type}" -> "^/[^/]+/[^/]+/[^/]+$"
    """
    if not pattern:
        return ""
    
    # Replace parameter placeholders with regex groups
    regex = pattern.replace('{', '').replace('}', '')
    
    # Convert to actual regex pattern
    # {entity_type} -> [^/]+ (any non-slash characters)
    regex = re.sub(r'[a-zA-Z_]+', r'[^/]+', regex)
    
    # Ensure it starts and ends correctly
    if not regex.startswith('^'):
        regex = '^' + regex
    if not regex.endswith('$'):
        regex = regex + '$'
    
    return regex

def _validate_and_fix_route(route: str, action_plan: Dict[str, Any], route_patterns: List[Dict[str, Any]]) -> str:
    """
    Validate route and fix common issues.
    Returns a valid route or raises an error.
    """
    # First, validate the route
    is_valid, matched_pattern, error_msg = _validate_route(route, route_patterns)
    
    if is_valid:
        return route
    
    # If invalid, try to fix common issues
    print(f"⚠️  Invalid route detected: {route}")
    print(f"⚠️  Error: {error_msg}")
    
    # Try to extract entity info and build a valid route
    entities = action_plan.get('entities', [])
    if entities:
        entity = entities[0]
        entity_id = entity.get('id', '')
        entity_table = entity.get('table', '')
        
        # Map table to entity_type
        entity_type_map = {
            'users': 'landlords',  # Assuming users are landlords for now
            'properties': 'properties',
            'leases': 'leases'
        }
        
        entity_type = entity_type_map.get(entity_table, 'landlords')
        
        # Build a valid route based on the most common pattern
        valid_route = f"/{entity_type}/{entity_id}/overview"
        
        # Validate the fixed route
        is_valid_fixed, _, _ = _validate_route(valid_route, route_patterns)
        
        if is_valid_fixed:
            print(f"✅ Fixed route: {route} -> {valid_route}")
            return valid_route
        else:
            print(f"❌ Could not fix route: {route}")
            raise ValueError(f"Invalid route '{route}' and could not generate valid alternative")
    
    # If no entities, try a generic fallback
    fallback_route = "/landlords/search"
    is_valid_fallback, _, _ = _validate_route(fallback_route, route_patterns)
    
    if is_valid_fallback:
        print(f"✅ Using fallback route: {fallback_route}")
        return fallback_route
    
    # If all else fails, raise an error
    raise ValueError(f"Invalid route '{route}' - no valid patterns found")


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
    performance: Dict[str, Any] = Field(..., description="Performance metrics including cache information")
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
    
    # Check if caching is enabled
    cache_enabled = settings.get('caching', {}).get('enabled', True)
    cache_hits = 0
    
    if cache_enabled:
        # TODO: if cached then: 1. Consider if response is good (chched one) 2. if many responses then use them as alternatives. £. If not many responses then call API to fill them up.
        print("🔍 Cache enabled - checking for cached responses...")
        
        # Step 1: Check request-level cache (exact match)
        request_cache_key = _generate_request_cache_key(request.query, request.user_id, request.user_role)
        cached_response = _get_cached_response(request_cache_key, "request")
        
        print(f"🔍 Cache Debug: Key={request_cache_key[:10]}..., Cache hit={cached_response is not None}")
        print(f"🔍 Cache Debug: Request cache size={len(_request_cache)}, Structural cache size={len(_structural_cache)}")
        
        if cached_response:
            cache_hits = 1
            duration_ms = (time.time() - start_time) * 1000
            cached_response["performance"]["duration_ms"] = round(duration_ms, 2)
            cached_response["performance"]["cache_hits"] = cache_hits
            cached_response["performance"]["cache_type"] = "request"
            print(f"✅ Cache hit! Returning cached response")
            return PlanResponse(**cached_response)
        
        # Step 2: Check structural cache (pattern matching)
        # Try to match against existing structural patterns without LLM call
        structural_hit = None
        try:
            for structural_key in _structural_cache.keys():
                if time.time() <= _structural_cache_ttl.get(structural_key, 0):
                    # Check if this query matches the structural pattern
                    pattern_query, pattern_route = structural_key.split('|', 1)
                    
                    # Simple pattern matching - replace placeholders with actual values
                    if _matches_structural_pattern(request.query, pattern_query):
                        # Found a structural match, try to apply it
                        entity_mapping = _extract_entities_from_query(request.query, pattern_query)
                        structural_hit = _apply_structural_cache(request.query, structural_key, entity_mapping)
                        if structural_hit:
                            break
        except Exception as e:
            print(f"❌ Structural cache check failed: {e}")
            # Continue with normal flow if structural cache fails
            structural_hit = None
        
        if structural_hit:
            cache_hits = 1
            duration_ms = (time.time() - start_time) * 1000
            structural_hit["performance"]["duration_ms"] = round(duration_ms, 2)
            structural_hit["performance"]["cache_hits"] = cache_hits
            structural_hit["performance"]["cache_type"] = "structural"
            
            # CRITICAL: Validate route in cached response too
            try:
                route_patterns = fantastic_router.config.route_patterns if hasattr(fantastic_router.config, 'route_patterns') else []
                cached_route = structural_hit.get("action_plan", {}).get("route", "")
                if cached_route:
                    validated_route = _validate_and_fix_route(cached_route, structural_hit.get("action_plan", {}), route_patterns)
                    structural_hit["action_plan"]["route"] = validated_route
                    print(f"✅ Cached route validated: {validated_route}")
            except Exception as e:
                print(f"❌ Cached route validation failed: {e}")
                # Use fallback for cached response too
                structural_hit["action_plan"]["route"] = "/landlords/search"
                structural_hit["action_plan"]["confidence"] = max(0.1, structural_hit["action_plan"].get("confidence", 0.5) - 0.3)
                print(f"⚠️  Using fallback for cached route: {structural_hit['action_plan']['route']}")
            
            print(f"✅ Cache hit! Returning cached response")
            return PlanResponse(**structural_hit)
    else:
        print("🚫 Cache disabled - skipping cache checks")
    
    try:
        # Plan the action using our core router
        action_plan = await fantastic_router.plan(
            query=request.query,
            user_role=request.user_role,
            session_data=request.context,
            max_results=request.max_alternatives
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
        
        # CRITICAL: Validate and fix the route
        try:
            route_patterns = fantastic_router.config.route_patterns if hasattr(fantastic_router.config, 'route_patterns') else []
            validated_route = _validate_and_fix_route(action_plan.route, action_plan_dict, route_patterns)
            action_plan_dict["route"] = validated_route
            print(f"✅ Route validated: {validated_route}")
        except Exception as e:
            print(f"❌ Route validation failed: {e}")
            # Use a safe fallback route
            action_plan_dict["route"] = "/landlords/search"
            action_plan_dict["confidence"] = max(0.1, action_plan_dict["confidence"] - 0.3)  # Reduce confidence
            print(f"⚠️  Using fallback route: {action_plan_dict['route']}")
        
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
        # TODO: make component to reuse everytime easily
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
        
        response = PlanResponse(
            success=True,
            action_plan=action_plan_dict,
            alternatives=alternatives,
            performance={
                "duration_ms": round(duration_ms, 2),
                "level": perf_level,
                "llm_calls": 1,  # From our single-call optimization
                "cache_hits": cache_hits,
                "cache_type": "none"
            },
            metadata={
                "query_length": len(request.query),
                "user_id": request.user_id,
                "user_role": request.user_role,
                "timestamp": start_time
            }
        )
        
        # Cache the response if caching is enabled
        if cache_enabled:
            # Step 2: Cache the response for future requests
            _cache_response(request_cache_key, response.dict(), "request")
            print(f"💾 Cached response for key={request_cache_key[:10]}...")
            
            # Step 3: Extract and cache structural pattern for similar queries
            try:
                structural_key, entity_mapping = _extract_structural_pattern(request.query, action_plan_dict)
                print(f"🔍 Structural pattern: {structural_key[:50]}...")
                
                # Create structural cache entry with placeholders
                structural_response = response.dict()
                structural_response_str = json.dumps(structural_response)
                
                # Replace actual values with placeholders for structural cache
                for placeholder, value in entity_mapping.items():
                    structural_response_str = structural_response_str.replace(str(value), placeholder)
                
                try:
                    structural_cache_entry = json.loads(structural_response_str)
                    _cache_response(structural_key, structural_cache_entry, "structural")
                    print(f"💾 Cached structural pattern for key={structural_key[:50]}...")
                except json.JSONDecodeError:
                    # If structural caching fails, just continue
                    print(f"❌ Failed to cache structural pattern")
                    pass
            except Exception as e:
                print(f"❌ Failed to extract structural pattern: {e}")
                # Continue without structural caching
                pass
        else:
            print("🚫 Cache disabled - not storing response")
        
        return response
        
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
    Get usage and performance statistics
    
    Returns aggregated statistics about API usage, performance,
    and system health.
    """
    # TODO: Implement actual statistics tracking
    
    # Calculate cache statistics
    request_cache_size = len(_request_cache)
    structural_cache_size = len(_structural_cache)
    
    # Count active (non-expired) entries
    current_time = time.time()
    active_request_cache = sum(1 for ttl in _request_cache_ttl.values() if current_time <= ttl)
    active_structural_cache = sum(1 for ttl in _structural_cache_ttl.values() if current_time <= ttl)
    
    return {
        "requests_total": 1247,  # TODO: Implement actual tracking
        "avg_response_time_ms": 1850.5,
        "avg_confidence": 0.84,
        "top_queries": [
            "show me properties",
            "create new tenant", 
            "edit contact info"
        ],
        "error_rate": 0.02,
        "uptime_seconds": 86400,
        "cache": {
            "request_cache": {
                "total_entries": request_cache_size,
                "active_entries": active_request_cache,
                "ttl_seconds": CACHE_TTL_SECONDS
            },
            "structural_cache": {
                "total_entries": structural_cache_size,
                "active_entries": active_structural_cache,
                "ttl_seconds": STRUCTURAL_CACHE_TTL_SECONDS
            }
        }
    }

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get detailed cache statistics
    
    Returns detailed information about cache performance,
    hit rates, and memory usage.
    """
    current_time = time.time()
    
    # Calculate cache hit rates (this would need to be tracked over time)
    # For now, return basic cache information
    
    return {
        "request_cache": {
            "total_entries": len(_request_cache),
            "active_entries": sum(1 for ttl in _request_cache_ttl.values() if current_time <= ttl),
            "expired_entries": sum(1 for ttl in _request_cache_ttl.values() if current_time > ttl),
            "ttl_seconds": CACHE_TTL_SECONDS,
            "estimated_memory_mb": len(_request_cache) * 0.1  # Rough estimate
        },
        "structural_cache": {
            "total_entries": len(_structural_cache),
            "active_entries": sum(1 for ttl in _structural_cache_ttl.values() if current_time <= ttl),
            "expired_entries": sum(1 for ttl in _structural_cache_ttl.values() if current_time > ttl),
            "ttl_seconds": STRUCTURAL_CACHE_TTL_SECONDS,
            "estimated_memory_mb": len(_structural_cache) * 0.15  # Rough estimate
        },
        "cache_patterns": list(_structural_cache.keys())[:10]  # Show first 10 patterns
    }

@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all caches
    
    Clears both request-level and structural caches.
    Useful for testing or when cache becomes stale.
    """
    global _request_cache, _request_cache_ttl, _structural_cache, _structural_cache_ttl
    
    request_cache_size = len(_request_cache)
    structural_cache_size = len(_structural_cache)
    
    _request_cache.clear()
    _request_cache_ttl.clear()
    _structural_cache.clear()
    _structural_cache_ttl.clear()
    
    return {
        "message": "Cache cleared successfully",
        "cleared_entries": {
            "request_cache": request_cache_size,
            "structural_cache": structural_cache_size
        }
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
