"""
FastAPI Dependencies for Fantastic Router Server
Handles dependency injection for LLM clients, database clients, and router configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException

from fantastic_router_core import FantasticRouter
from fantastic_router_core.models.site import SiteConfiguration
from fantastic_router_core.planning.single_call_planner import SingleCallActionPlanner
from fantastic_router_core.planning.intent_parser import LLMClient
from fantastic_router_core.retrieval.vector import DatabaseClient


class DependencyContainer:
    """Container for managing application dependencies"""
    
    def __init__(self):
        self._llm_client: Optional[LLMClient] = None
        self._db_client: Optional[DatabaseClient] = None
        self._router: Optional[FantasticRouter] = None
        self._config: Optional[Dict[str, Any]] = None
    
    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = self._create_llm_client()
        return self._llm_client
    
    @property
    def db_client(self) -> DatabaseClient:
        if self._db_client is None:
            self._db_client = self._create_db_client()
        return self._db_client
    
    @property
    def config(self) -> Dict[str, Any]:
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    @property
    def router(self) -> FantasticRouter:
        if self._router is None:
            self._router = self._create_router()
        return self._router
    
    def _create_llm_client(self) -> LLMClient:
        """Create LLM client based on YAML config"""
        
        try:
            # Get LLM config from YAML
            from ..config_loader import get_llm_config
            llm_config = get_llm_config()
            
            if llm_config:
                provider = llm_config.get('provider', 'openai')
                
                # Get global LLM settings
                temperature = float(llm_config.get('temperature', 0.1))
                max_tokens = int(llm_config.get('max_tokens', 1000))
                timeout = int(llm_config.get('timeout', 60))
                
                # Get provider-specific configuration
                if provider == "openai":
                    openai_config = llm_config.get('openai', {})
                    api_key = openai_config.get('api_key')
                    model = openai_config.get('model')
                    
                    if api_key and api_key != "your-openai-api-key-here":
                        try:
                            import sys
                            sys.path.append("/app/adapters")
                            from llm.openai import create_openai_client
                            return create_openai_client(
                                api_key=api_key, 
                                model=model, 
                                max_tokens=max_tokens
                            )
                        except ImportError:
                            pass
                            
                elif provider == "gemini":
                    gemini_config = llm_config.get('gemini', {})
                    api_key = gemini_config.get('api_key')
                    model = gemini_config.get('model')
                    
                    if api_key and api_key != "your-google-ai-api-key-here":
                        try:
                            import sys
                            sys.path.append("/app/adapters")
                            from llm.gemini import create_gemini_client
                            return create_gemini_client(
                                api_key=api_key, 
                                model=model,
                                temperature=temperature
                            )
                        except ImportError:
                            pass
                            
                elif provider == "anthropic":
                    anthropic_config = llm_config.get('anthropic', {})
                    api_key = anthropic_config.get('api_key')
                    model = anthropic_config.get('model')
                    
                    if api_key and api_key != "your-anthropic-api-key-here":
                        try:
                            import sys
                            sys.path.append("/app/adapters")
                            from llm.anthropic import create_anthropic_client
                            return create_anthropic_client(
                                api_key=api_key, 
                                model=model,
                                temperature=temperature
                            )
                        except ImportError:
                            pass
                            
                elif provider == "ollama":
                    ollama_config = llm_config.get('ollama', {})
                    base_url = ollama_config.get('base_url', 'http://localhost:11434')
                    model = ollama_config.get('model')
                    
                    try:
                        import sys
                        sys.path.append("/app/adapters")
                        from llm.ollama import create_ollama_client
                        return create_ollama_client(
                            base_url=base_url, 
                            model=model,
                            temperature=temperature
                        )
                    except ImportError:
                        pass
        except Exception:
            pass
        
        # Fallback to mock client if no LLM is configured
        return MockLLMClient()
    
    def _create_db_client(self) -> DatabaseClient:
        """Create database client based on YAML config"""
        
        try:
            # Get database config from YAML
            from ..config_loader import get_database_config
            db_config = get_database_config()
            
            if db_config:
                db_type = db_config.get('type', 'direct')
                
                if db_type == 'api':
                    # API-based database client
                    try:
                        import sys
                        sys.path.append("/app/adapters")
                        from db.supabase import SupabaseDatabaseClient
                        
                        api_config = db_config.get('api', {})
                        api_endpoint = api_config.get('endpoint')
                        token = api_config.get('token')
                        
                        if api_endpoint and token:
                            return SupabaseDatabaseClient(
                                api_endpoint=api_endpoint,
                                token=token,
                                schema_endpoint=api_config.get('schema_endpoint', '/schema'),
                                search_endpoint=api_config.get('search_endpoint', '/search'),
                                rate_limit=api_config.get('max_requests_per_minute', 100)
                            )
                    except ImportError:
                        pass
                        
                elif db_type == 'direct':
                    # Direct database connection
                    connection_string = db_config.get('connection_string')
                    if not connection_string:
                        raise HTTPException(
                            status_code=500,
                            detail="Database connection string not configured"
                        )
                    
                    try:
                        import sys
                        sys.path.append("/app/adapters")
                        from db.postgres import PostgreSQLDatabaseClient
                        
                        max_connections = int(db_config.get('max_connections', 10))
                        timeout = int(db_config.get('timeout', 30))
                        
                        return PostgreSQLDatabaseClient(
                            connection_string=connection_string,
                            max_connections=max_connections,
                            timeout=timeout
                        )
                    except ImportError:
                        raise HTTPException(
                            status_code=500,
                            detail="PostgreSQL dependencies not available"
                        )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database configuration error: {str(e)}"
            )
    
    def _create_router(self) -> FantasticRouter:
        """Create the main router instance"""
        from fantastic_router_core.models.site import (
            SiteConfiguration, 
            EntityDefinition,
            RoutePattern,
            DatabaseSchema,
            TableSchema,
            ColumnSchema,
            RouteParameter,
            ParameterType
        )
        
        # Parse config into SiteConfiguration
        config_dict = self.config
        
        try:
            # Convert dict to proper SiteConfiguration object
            
            # Parse entities
            entities = {}
            for name, entity_data in config_dict.get("entities", {}).items():
                entities[name] = EntityDefinition(**entity_data)
            
            # Parse route patterns
            route_patterns = []
            for pattern_data in config_dict.get("route_patterns", []):
                # Convert parameters dict
                parameters = {}
                for param_name, param_data in pattern_data.get("parameters", {}).items():
                    param_type = param_data.get("type", "string")
                    parameters[param_name] = RouteParameter(
                        type=ParameterType(param_type),
                        description=param_data.get("description", f"{param_name} parameter"),
                        required=param_data.get("required", True)
                    )
                
                route_pattern = RoutePattern(
                    pattern=pattern_data["pattern"],
                    name=pattern_data["name"],
                    description=pattern_data["description"],
                    intent_patterns=pattern_data.get("intent_patterns", []),
                    parameters=parameters
                )
                route_patterns.append(route_pattern)
            
            # Parse database schema
            tables = {}
            for table_name, table_data in config_dict.get("database_schema", {}).get("tables", {}).items():
                columns = []
                for col_data in table_data.get("columns", []):
                    columns.append(ColumnSchema(
                        name=col_data["name"],
                        type=col_data["type"],
                        nullable=col_data.get("nullable", True),
                        description=col_data.get("description")
                    ))
                
                tables[table_name] = TableSchema(
                    name=table_name,
                    columns=columns,
                    description=table_data.get("description"),
                    primary_key=table_data.get("primary_key", "id")
                )
            
            database_schema = DatabaseSchema(tables=tables)
            
            # Create SiteConfiguration
            site_config = SiteConfiguration(
                domain=config_dict.get("domain", "unknown"),
                base_url=config_dict.get("base_url", "http://localhost"),
                entities=entities,
                route_patterns=route_patterns,
                database_schema=database_schema
            )
            
            use_fast_planner = os.getenv("USE_FAST_PLANNER", "true").lower() == "true"
            
            return FantasticRouter(
                llm_client=self.llm_client,
                db_client=self.db_client,
                config=site_config,  # Now properly parsed!
                use_fast_planner=use_fast_planner
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create router: {str(e)}"
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load router configuration"""
        
        try:
            # Use the config loader to get configuration
            from ..config_loader import get_config
            config = get_config()
            
            # If it's a YAML config, extract the router-specific parts
            if 'app' in config:
                # This is a YAML config, extract router config
                router_config = {
                    "domain": config.get('app', {}).get('domain', 'property_management'),
                    "base_url": config.get('app', {}).get('base_url', 'https://myapp.com'),
                    "entities": config.get('entities', {}),
                    "route_patterns": config.get('routes', []),
                    "database_schema": config.get('schema', {}),
                    "semantic_mappings": config.get('semantic_mappings', {}),
                    "default_actions": config.get('default_actions', [])
                }
                return router_config
            else:
                # This is a legacy JSON config, return as-is
                return config
                
        except Exception as e:
            # Fallback to basic config
            return {
                "domain": "property_management",
                "base_url": "https://myapp.com",
                "entities": {
                    "person": {
                        "name": "person",
                        "table": "users",
                        "description": "People in the system",
                        "search_fields": ["name", "email"],
                        "display_field": "name",
                        "unique_identifier": "id"
                    }
                },
                "route_patterns": [
                    {
                        "pattern": "/{entity_type}/{entity_id}/{view_type}",
                        "name": "entity_detail_view",
                        "description": "View specific details for an entity instance",
                        "intent_patterns": [
                            "show {entity} {view_data}",
                            "view {entity} {view_data}"
                        ],
                        "parameters": {
                            "entity_type": {"type": "string", "required": True},
                            "entity_id": {"type": "string", "required": True},
                            "view_type": {"type": "string", "required": True}
                        }
                    }
                ],
                "database_schema": {
                    "tables": {
                        "users": {
                            "name": "users",
                            "description": "All users in the system",
                            "columns": [
                                {"name": "id", "type": "uuid"},
                                {"name": "name", "type": "varchar"},
                                {"name": "email", "type": "varchar"}
                            ]
                        }
                    }
                }
            }
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load application settings from YAML config"""
        try:
            # Use the config loader to get configuration
            from ..config_loader import get_config
            config = get_config()
            
            # Extract settings from YAML config
            app_config = config.get('app', {})
            llm_config = config.get('llm', {})
            logging_config = config.get('logging', {})
            
            return {
                "app_env": app_config.get('environment', 'development'),
                "log_level": logging_config.get('level', 'INFO'),
                "llm_timeout": int(llm_config.get('timeout', 60)),
                "llm_temperature": float(llm_config.get('temperature', 0.1)),
                "use_fast_planner": app_config.get('use_fast_planner', True)
            }
        except Exception as e:
            # Fallback to environment variables if YAML config fails
            return {
                "app_env": os.getenv("APP_ENV", "development"),
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "llm_timeout": int(os.getenv("LLM_TIMEOUT", "60")),
                "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
                "use_fast_planner": os.getenv("USE_FAST_PLANNER", "true").lower() == "true"
            }


class MockLLMClient:
    """Mock LLM client for when no real LLM is available"""
    
    async def analyze(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Return mock response"""
        return {
            "action_type": "NAVIGATE",
            "entities": [],
            "confidence": 0.8,
            "reasoning": "Mock LLM response - no real LLM configured",
            "route": "/mock/route",
            "parameters": []
        }


# Global container instance
_container = DependencyContainer()


# FastAPI dependency functions
def get_router() -> FantasticRouter:
    """Get the router instance"""
    return _container.router


def get_settings() -> Dict[str, Any]:
    """Get application settings"""
    return {
        "app_env": os.getenv("APP_ENV", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "llm_timeout": int(os.getenv("LLM_TIMEOUT", "60")),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.1"))
    }
