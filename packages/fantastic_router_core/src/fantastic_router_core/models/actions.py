from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions the router can suggest"""
    NAVIGATE = "NAVIGATE"
    QUERY = "QUERY"
    MUTATION = "MUTATION"
    CREATE = "CREATE"
    EDIT = "EDIT"
    DELETE = "DELETE"


class EntityMatch(BaseModel):
    """Represents a matched entity from the database"""
    id: str = Field(..., description="Unique identifier for the entity")
    name: str = Field(..., description="Display name of the entity")
    table: str = Field(..., description="Database table where entity was found")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the match")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional entity metadata")


class RouteParameter(BaseModel):
    """A parameter in a route pattern"""
    name: str = Field(..., description="Parameter name")
    value: str = Field(..., description="Resolved parameter value")
    type: str = Field(default="string", description="Parameter type")
    source: str = Field(..., description="How this parameter was resolved (entity, literal, computed)")


class ActionPlan(BaseModel):
    """The result of planning an action based on user query"""
    action_type: ActionType = Field(..., description="Type of action to perform")
    route: str = Field(..., description="Target route/URL for the action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this action plan")
    
    # Parameters and entities
    parameters: List[RouteParameter] = Field(default_factory=list, description="Resolved route parameters")
    entities: List[EntityMatch] = Field(default_factory=list, description="Entities referenced in the query")
    
    # Metadata
    reasoning: str = Field(..., description="LLM reasoning for this action plan")
    query_params: Dict[str, str] = Field(default_factory=dict, description="URL query parameters")
    matched_pattern: Optional[str] = Field(None, description="Route pattern that was matched")
    
    # Alternative suggestions
    alternatives: List["ActionPlan"] = Field(default_factory=list, description="Alternative action plans")


class PlanningContext(BaseModel):
    """Context information for planning actions"""
    user_query: str = Field(..., description="Original user query")
    domain: str = Field(..., description="Application domain (e.g., 'property_management')")
    user_role: Optional[str] = Field(None, description="User's role for RBAC")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    
    # Database and routing context
    database_schema: Dict[str, Any] = Field(..., description="Database schema information")
    route_patterns: List[Dict[str, Any]] = Field(..., description="Available route patterns")
    
    # Optional constraints
    allowed_actions: Optional[List[ActionType]] = Field(None, description="Actions allowed for this user")
    max_results: int = Field(default=5, description="Maximum number of alternative plans")


# Update the forward reference
ActionPlan.model_rebuild()
