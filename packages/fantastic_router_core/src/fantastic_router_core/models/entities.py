from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

# TODO: maybe remove entity type along with entity_type, seems unnecesary
class EntityType(str, Enum):
    """Common entity types across domains"""
    PERSON = "person"
    ORGANIZATION = "organization"
    OBJECT = "object"  # Generic for domain-specific objects
    DOCUMENT = "document"
    EVENT = "event"
    LOCATION = "location"


class SearchStrategy(str, Enum):
    """Strategies for searching entities"""
    EXACT_MATCH = "exact_match"
    FUZZY_MATCH = "fuzzy_match"
    SEMANTIC_SEARCH = "semantic_search"
    FULL_TEXT_SEARCH = "full_text_search"


class EntitySearchRequest(BaseModel):
    """Request for entity search"""
    query: str = Field(..., description="Search query")
    entity_type: Optional[str] = Field(None, description="Expected entity type")
    table_hints: List[str] = Field(default_factory=list, description="Tables to prioritize in search")
    max_results: int = Field(default=10, description="Maximum results to return")
    min_confidence: float = Field(default=0.5, description="Minimum confidence threshold")


class EntitySearchResult(BaseModel):
    """Result from entity search"""
    entities: List["EntityMatch"] = Field(..., description="Found entities")
    search_strategy_used: SearchStrategy = Field(..., description="Strategy that found these results")
    total_searched: int = Field(..., description="Total entities searched")
    execution_time_ms: float = Field(..., description="Search execution time")


class EntityMatch(BaseModel):
    """A matched entity from search"""
    id: str = Field(..., description="Entity unique identifier")
    name: str = Field(..., description="Entity display name")
    table: str = Field(..., description="Source table")
    entity_type: str = Field(..., description="Inferred entity type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")
    
    # Match details
    matched_fields: List[str] = Field(..., description="Fields that matched the search")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw entity data")
    
    # Context
    reasoning: Optional[str] = Field(None, description="Why this entity was matched")


class ContextualEntityResolution(BaseModel):
    """LLM analysis of entity resolution in context"""
    entity_name: str = Field(..., description="Entity name from query")
    inferred_type: str = Field(..., description="Inferred entity type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in type inference")
    
    # Search strategy
    recommended_tables: List[str] = Field(..., description="Tables to search")
    search_fields: List[str] = Field(..., description="Fields to search in")
    join_strategy: Optional[str] = Field(None, description="How to join tables if needed")
    
    # Reasoning
    reasoning: str = Field(..., description="LLM reasoning for this resolution")
    context_clues: List[str] = Field(..., description="Context clues that informed the decision")


class DomainContext(BaseModel):
    """Context about the application domain"""
    domain_name: str = Field(..., description="Domain identifier")
    primary_entities: List[str] = Field(..., description="Main entity types in this domain")
    common_relationships: Dict[str, List[str]] = Field(..., description="Common entity relationships")
    domain_vocabulary: Dict[str, List[str]] = Field(default_factory=dict, description="Domain-specific synonyms")
    
    # Business rules
    business_rules: List[str] = Field(default_factory=list, description="Domain-specific business rules")


class EntityResolutionPlan(BaseModel):
    """Complete plan for resolving entities in a query"""
    query: str = Field(..., description="Original query")
    entities_to_resolve: List[str] = Field(..., description="Entity names found in query")
    
    # Resolution strategy for each entity
    resolution_strategies: List[ContextualEntityResolution] = Field(..., description="How to resolve each entity")
    
    # Execution plan
    search_order: List[str] = Field(..., description="Order to search for entities")
    fallback_strategies: List[SearchStrategy] = Field(..., description="Fallback search strategies")
    
    # Context
    domain_context: DomainContext = Field(..., description="Domain context for resolution")
    estimated_confidence: float = Field(..., description="Estimated overall confidence")


# Update forward references
EntitySearchResult.model_rebuild()
