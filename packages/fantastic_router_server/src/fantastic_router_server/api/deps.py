"""
FastAPI Dependencies for Fantastic Router Server
Handles dependency injection for LLM clients, database clients, and router configuration
"""

import os
import json
from typing import Optional, Dict, Any
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, Depends
from fantastic_router_core import FantasticRouter
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
        """Create LLM client based on environment variables"""
        
        # Try providers in order of preference
        
        # 1. Try Gemini first (often fastest/cheapest)
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        if gemini_key and gemini_key != "your-google-ai-api-key-here":
            try:
                # Import here to avoid dependency issues if not installed
                import sys
                sys.path.append("/app/adapters")
                from llm.gemini import create_gemini_client
                
                model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                return create_gemini_client(api_key=gemini_key, model=model)
            except ImportError:
                pass
        
        # 2. Try OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your-openai-api-key-here":
            try:
                import sys
                sys.path.append("/app/adapters")
                from llm.openai import create_openai_client
                
                model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-1106")
                max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
                return create_openai_client(
                    api_key=openai_key, 
                    model=model, 
                    max_tokens=max_tokens
                )
            except ImportError:
                pass
        
        # 3. Try Claude
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key != "your-anthropic-api-key-here":
            try:
                import sys
                sys.path.append("/app/adapters")
                from llm.anthropic import create_anthropic_client
                
                model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
                return create_anthropic_client(api_key=anthropic_key, model=model)
            except ImportError:
                pass
        
        # 4. Try Ollama (local)
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        try:
            import sys
            sys.path.append("/app/adapters")
            from llm.ollama import create_ollama_client
            
            # Test if Ollama is available
            import aiohttp
            import asyncio
            
            async def test_ollama():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{ollama_base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as response:
                            return response.status == 200
                except:
                    return False
            
            # For now, assume Ollama might be available
            return create_ollama_client(
                base_url=ollama_base_url,
                model=ollama_model
            )
        except ImportError:
            pass
        
        # 5. Fallback to mock client
        return MockLLMClient()
    
    def _create_db_client(self) -> DatabaseClient:
        """Create database client based on environment variables"""
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(
                status_code=500,
                detail="DATABASE_URL environment variable not set"
            )
        
        try:
            import sys
            sys.path.append("/app/adapters")
            from db.postgres import PostgreSQLDatabaseClient
            
            max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "10"))
            timeout = int(os.getenv("DB_TIMEOUT", "30"))
            
            return PostgreSQLDatabaseClient(
                connection_string=database_url,
                max_connections=max_connections,
                timeout=timeout
            )
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PostgreSQL dependencies not available"
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load router configuration"""
        
        # Try to load from various locations
        config_paths = [
            "/app/examples/quickstart/routes.json",
            "/app/routes.json",
            "routes.json"
        ]
        
        for config_path in config_paths:
            try:
                if Path(config_path).exists():
                    with open(config_path, 'r') as f:
                        return json.load(f)
            except Exception:
                continue
        
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
@lru_cache()
def get_settings() -> Dict[str, Any]:
    """Get application settings"""
    return {
        "app_env": os.getenv("APP_ENV", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "llm_timeout": int(os.getenv("LLM_TIMEOUT", "60")),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.1"))
    }


def get_container() -> DependencyContainer:
    """Get the dependency container"""
    return _container


def get_router(container: DependencyContainer = Depends(get_container)) -> FantasticRouter:
    """Get the router instance"""
    return container.router


def get_llm_client(container: DependencyContainer = Depends(get_container)) -> LLMClient:
    """Get the LLM client"""
    return container.llm_client


def get_db_client(container: DependencyContainer = Depends(get_container)) -> DatabaseClient:
    """Get the database client"""
    return container.db_client
