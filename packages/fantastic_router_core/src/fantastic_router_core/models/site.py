from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ParameterType(str, Enum):
    """Types of route parameters"""
    STRING = "string"
    INTEGER = "integer"
    UUID = "uuid"
    SLUG = "slug"
    ENUM = "enum"


class RouteParameter(BaseModel):
    """Definition of a route parameter"""
    type: ParameterType = Field(..., description="Parameter type")
    description: str = Field(..., description="Human-readable description")
    examples: List[str] = Field(default_factory=list, description="Example values")
    enum_values: Optional[List[str]] = Field(None, description="Allowed values for enum type")
    required: bool = Field(default=True, description="Whether parameter is required")


class RoutePattern(BaseModel):
    """Defines a route pattern that the LLM can match against"""
    pattern: str = Field(..., description="URL pattern (e.g., '/{entity_type}/{entity_id}/{view_type}')")
    name: str = Field(..., description="Unique name for this pattern")
    description: str = Field(..., description="What this route pattern does")
    
    # Intent matching
    intent_patterns: List[str] = Field(..., description="Natural language patterns that match this route")
    
    # Parameters
    parameters: Dict[str, RouteParameter] = Field(default_factory=dict, description="Route parameters")
    query_params: Dict[str, RouteParameter] = Field(default_factory=dict, description="Optional query parameters")
    
    # Metadata
    domain_specific: bool = Field(default=False, description="Whether this is domain-specific")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example queries and resolutions")
    
    # Access control
    required_roles: Optional[List[str]] = Field(None, description="Roles required to access this route")


class EntityDefinition(BaseModel):
    """Defines an entity type in the domain"""
    name: str = Field(..., description="Entity name (e.g., 'user', 'house', 'landlord')")
    table: str = Field(..., description="Primary database table")
    description: str = Field(..., description="What this entity represents")
    
    # Search configuration
    search_fields: List[str] = Field(..., description="Fields to search when looking for this entity")
    display_field: str = Field(..., description="Field to use for display names")
    unique_identifier: str = Field(..., description="Primary key field")
    
    # Relationships
    related_entities: Dict[str, str] = Field(default_factory=dict, description="Related entities and their relationship")
    
    # Synonyms and aliases
    aliases: List[str] = Field(default_factory=list, description="Alternative names for this entity")


class DatabaseSchema(BaseModel):
    """Represents the database schema information"""
    tables: Dict[str, "TableSchema"] = Field(..., description="Database tables")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Foreign key relationships")
    
    
class TableSchema(BaseModel):
    """Schema for a database table"""
    name: str = Field(..., description="Table name")
    columns: List["ColumnSchema"] = Field(..., description="Table columns")
    description: Optional[str] = Field(None, description="Table description")
    primary_key: str = Field(..., description="Primary key column")


class ColumnSchema(BaseModel):
    """Schema for a database column"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    nullable: bool = Field(default=True, description="Whether column can be null")
    description: Optional[str] = Field(None, description="Column description")


class SiteConfiguration(BaseModel):
    """Complete site configuration"""
    domain: str = Field(..., description="Application domain")
    base_url: str = Field(..., description="Base URL for the application")
    
    # Core configuration
    entities: Dict[str, EntityDefinition] = Field(..., description="Entity definitions")
    route_patterns: List[RoutePattern] = Field(..., description="Available route patterns")
    database_schema: DatabaseSchema = Field(..., description="Database schema")
    
    # Domain-specific settings
    semantic_mappings: Dict[str, List[str]] = Field(default_factory=dict, description="Semantic word mappings")
    default_actions: List[str] = Field(default_factory=list, description="Common actions for this domain")
    
    # API configuration
    database_api: Optional["DatabaseAPIConfig"] = Field(None, description="Database API configuration")


class DatabaseAPIConfig(BaseModel):
    """Configuration for database API access"""
    endpoint: str = Field(..., description="API base URL")
    token: str = Field(..., description="API authentication token")
    search_endpoint: str = Field(default="/search", description="Entity search endpoint")
    schema_endpoint: str = Field(default="/schema", description="Schema introspection endpoint")
    rate_limit: int = Field(default=100, description="Requests per minute limit")


# Update forward references
DatabaseSchema.model_rebuild()
SiteConfiguration.model_rebuild()
