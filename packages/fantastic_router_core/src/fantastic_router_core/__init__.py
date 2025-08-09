"""
Fantastic Router - LLM-powered intent router for web applications
"""

from typing import Dict, Any, Optional, List
import json

from .models.actions import ActionPlan, PlanningContext
from .models.site import SiteConfiguration
from .planning.action_planner import ActionPlanner
from .planning.single_call_planner import SingleCallActionPlanner
from .planning.intent_parser import LLMClient
from .retrieval.vector import EntityResolver, DatabaseClient


class FantasticRouter:
    """
    Main router class that provides LLM-powered intent routing for web applications.
    
    Usage:
        router = FantasticRouter(
            llm_client=your_llm_client,
            db_client=your_db_client,
            config=site_configuration
        )
        
        action = await router.plan("show me James Smith's income")
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        db_client: DatabaseClient,
        config: SiteConfiguration,
        use_fast_planner: bool = True
    ):
        self.config = config
        self.llm_client = llm_client
        self.db_client = db_client
        
        # Initialize components
        self.entity_resolver = EntityResolver(db_client)
        
        # Choose planner based on performance preference
        if use_fast_planner:
            self.action_planner = SingleCallActionPlanner(llm_client, self.entity_resolver)
        else:
            self.action_planner = ActionPlanner(llm_client, self.entity_resolver)
    
    async def plan(
        self,
        query: str,
        user_role: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
        max_results: int = 5
    ) -> ActionPlan:
        """
        Plan an action based on a natural language query.
        
        Args:
            query: User's natural language request
            user_role: User's role for RBAC (optional)
            session_data: Additional session context (optional)
            max_results: Maximum number of alternative plans to generate
            
        Returns:
            ActionPlan with the recommended action and route
        """
        
        # Build planning context
        context = PlanningContext(
            user_query=query,
            domain=self.config.domain,
            user_role=user_role,
            session_data=session_data or {},
            database_schema=self._serialize_database_schema(),
            route_patterns=self._serialize_route_patterns(),
            max_results=max_results
        )
        
        # Generate action plan
        action_plan = await self.action_planner.plan_action(context)
        
        # Apply RBAC if configured
        if user_role and not self._check_route_permissions(action_plan.route, user_role):
            # Return a fallback or error action
            action_plan.confidence = 0.0
            action_plan.reasoning += "\nAccess denied: Insufficient permissions for this route"
        
        return action_plan
    
    def _serialize_database_schema(self) -> Dict[str, Any]:
        """Convert database schema to serializable format"""
        schema_dict = {
            "tables": {},
            "relationships": self.config.database_schema.relationships
        }
        
        for table_name, table_schema in self.config.database_schema.tables.items():
            schema_dict["tables"][table_name] = {
                "name": table_schema.name,
                "description": table_schema.description,
                "primary_key": table_schema.primary_key,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": col.nullable,
                        "description": col.description
                    }
                    for col in table_schema.columns
                ]
            }
        
        return schema_dict
    
    def _serialize_route_patterns(self) -> List[Dict[str, Any]]:
        """Convert route patterns to serializable format"""
        patterns = []
        
        for pattern in self.config.route_patterns:
            pattern_dict = {
                "pattern": pattern.pattern,
                "name": pattern.name,
                "description": pattern.description,
                "intent_patterns": pattern.intent_patterns,
                "domain_specific": pattern.domain_specific,
                "examples": pattern.examples,
                "parameters": {
                    name: {
                        "type": param.type.value,
                        "description": param.description,
                        "examples": param.examples,
                        "required": param.required
                    }
                    for name, param in pattern.parameters.items()
                }
            }
            patterns.append(pattern_dict)
        
        return patterns
    
    def _check_route_permissions(self, route: str, user_role: str) -> bool:
        """Check if user has permission to access the route"""
        
        # Find matching route pattern
        for pattern in self.config.route_patterns:
            if self._route_matches_pattern(route, pattern.pattern):
                if pattern.required_roles:
                    return user_role in pattern.required_roles
                return True  # No specific role requirements
        
        return True  # Default allow if no pattern matches
    
    def _route_matches_pattern(self, route: str, pattern: str) -> bool:
        """Check if a route matches a pattern (simple implementation)"""
        
        # Simple pattern matching - could be enhanced with proper regex
        route_parts = route.strip('/').split('/')
        pattern_parts = pattern.strip('/').split('/')
        
        if len(route_parts) != len(pattern_parts):
            return False
        
        for route_part, pattern_part in zip(route_parts, pattern_parts):
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue  # Variable part, matches anything
            elif route_part != pattern_part:
                return False
        
        return True


# Convenience function for creating router from configuration file
async def create_router_from_config(
    config_path: str,
    llm_client: LLMClient,
    db_client: DatabaseClient
) -> FantasticRouter:
    """Create a FantasticRouter from a configuration file"""
    
    with open(config_path, 'r') as f:
        if config_path.endswith('.json'):
            config_dict = json.load(f)
        else:
            import yaml
            config_dict = yaml.safe_load(f)
    
    # Convert dict to SiteConfiguration
    # This is a simplified conversion - in practice you'd want proper validation
    config = SiteConfiguration(**config_dict)
    
    return FantasticRouter(llm_client, db_client, config)


# Export main classes
__all__ = [
    'FantasticRouter',
    'ActionPlan',
    'SiteConfiguration',
    'create_router_from_config'
]
