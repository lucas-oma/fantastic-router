"""
Optimized single-call action planner for faster performance
"""

import json
from typing import Dict, List, Any, Optional

from ..models.actions import ActionPlan, ActionType, RouteParameter, PlanningContext
from ..models.entities import EntityMatch
from .intent_parser import LLMClient


class SingleCallActionPlanner:
    """Optimized planner that does intent parsing, entity resolution, and route matching in one LLM call"""
    
    def __init__(self, llm_client: LLMClient, entity_resolver: Any):
        self.llm = llm_client
        self.entity_resolver = entity_resolver
    
    async def plan_action(self, context: PlanningContext) -> ActionPlan:
        """Plan an action with a single LLM call instead of three"""
        
        # Single comprehensive LLM call
        llm_response = await self._comprehensive_analysis(context)
        
        # Resolve entities based on LLM suggestions
        entities = await self._resolve_suggested_entities(llm_response, context)
        
        # Build final action plan
        return self._build_action_plan(context, llm_response, entities)
    
    async def _comprehensive_analysis(self, context: PlanningContext) -> Dict[str, Any]:
        """Single LLM call that does intent parsing, entity analysis, and route matching"""
        
        prompt = self._build_comprehensive_prompt(context)
        return await self.llm.analyze(prompt, temperature=0.1)
    
    def _build_comprehensive_prompt(self, context: PlanningContext) -> str:
        """Build a single comprehensive prompt that handles all analysis steps"""
        
        # Format database schema
        schema_summary = self._format_schema_summary(context.database_schema)
        
        # Format route patterns
        patterns_text = self._format_route_patterns(context.route_patterns)
        
        return f"""
You are an expert at analyzing user queries for web application routing. Complete ALL analysis in one response.

DOMAIN: {context.domain}
USER QUERY: "{context.user_query}"

DATABASE SCHEMA:
{schema_summary}

AVAILABLE ROUTE PATTERNS:
{patterns_text}

TASK: Analyze this query and provide a complete routing solution:

1. INTENT ANALYSIS:
   - What action type (NAVIGATE, CREATE, EDIT, DELETE, QUERY)
   - What entities are mentioned
   - What view/data type is requested

2. ENTITY RESOLUTION:
   - For each entity, determine which database tables to search
   - Which fields to search in those tables
   - Your confidence in finding each entity

3. ROUTE MATCHING:
   - Which route pattern best matches this intent
   - How to fill in the pattern parameters
   - The final resolved route

RESPONSE FORMAT (JSON):
{{
    "intent": {{
        "action_type": "NAVIGATE|CREATE|EDIT|DELETE|QUERY",
        "entities": ["entity1", "entity2"],
        "view_type": "specific_view_or_null",
        "confidence": 0.9
    }},
    "entity_resolution": [
        {{
            "entity_name": "James Smith",
            "search_tables": ["users", "landlords"],
            "search_fields": ["name", "email"],
            "confidence": 0.9
        }}
    ],
    "route_matching": {{
        "matched_pattern": "/{{entity_type}}/{{entity_id}}/{{view_type}}",
        "resolved_route": "/landlords/ENTITY_ID_PLACEHOLDER/financials",
        "parameters": [
            {{
                "name": "entity_type",
                "value": "landlords",
                "source": "inferred"
            }},
            {{
                "name": "entity_id",
                "value": "ENTITY_ID_PLACEHOLDER",
                "source": "entity"
            }},
            {{
                "name": "view_type",
                "value": "financials",
                "source": "inferred"
            }}
        ],
        "confidence": 0.85
    }},
    "overall_confidence": 0.87,
    "reasoning": "User wants to navigate to James Smith's financial information. James Smith is likely a landlord based on income context."
}}

EXAMPLES:
Query: "show me James Smith's monthly income"
--> NAVIGATE to landlord financials, search users/landlords tables for "James Smith"

Query: "create new property"  
--> CREATE action, no entity search needed, route to /properties/create

Analyze the query now:
"""

    def _format_schema_summary(self, database_schema: Dict[str, Any]) -> str:
        """Format database schema for the prompt"""
        if 'tables' not in database_schema:
            return "No schema information available"
        
        summary = []
        for table_name, table_info in database_schema['tables'].items():
            columns = []
            if 'columns' in table_info:
                columns = [col.get('name', '') for col in table_info['columns'][:8]]  # Limit columns
            summary.append(f"- {table_name}: {', '.join(columns)}")
            if 'description' in table_info:
                summary.append(f"  Purpose: {table_info['description']}")
        
        return "\n".join(summary)
    
    def _format_route_patterns(self, route_patterns: List[Dict[str, Any]]) -> str:
        """Format route patterns for the prompt"""
        patterns = []
        for pattern in route_patterns[:5]:  # Limit to avoid context overflow
            patterns.append(f"- {pattern.get('pattern', '')}: {pattern.get('description', '')}")
            if 'intent_patterns' in pattern:
                for intent in pattern['intent_patterns'][:2]:
                    patterns.append(f"  Example: \"{intent}\"")
        return "\n".join(patterns)
    
    async def _resolve_suggested_entities(
        self, 
        llm_response: Dict[str, Any], 
        context: PlanningContext
    ) -> List[EntityMatch]:
        """Resolve entities based on LLM suggestions"""
        
        entities = []
        entity_resolutions = llm_response.get('entity_resolution', [])
        
        for resolution in entity_resolutions:
            try:
                matches = await self.entity_resolver.search_entity(
                    entity_name=resolution.get('entity_name', ''),
                    tables=resolution.get('search_tables', []),
                    search_fields=resolution.get('search_fields', []),
                    max_results=5,
                    min_confidence=0.5
                )
                entities.extend(matches)
            except Exception as e:
                print(f"Error resolving entity {resolution.get('entity_name')}: {e}")
                continue
        
        return entities
    
    # TODO: remove unused context
    def _build_action_plan(
        self,
        context: PlanningContext,
        llm_response: Dict[str, Any],
        entities: List[EntityMatch]
    ) -> ActionPlan:
        """Build the final action plan"""
        
        # Extract intent info with defaults
        intent = llm_response.get('intent', {})
        route_info = llm_response.get('route_matching', {})
        
        # Build parameters, replacing placeholders with actual entity IDs
        parameters = []
        resolved_route = route_info.get('resolved_route') or '/'
        
        for param in route_info.get('parameters', []):
            param_value = param.get('value') or ''  # Handle None values
            
            # Replace entity ID placeholder with actual entity ID
            if param_value == 'ENTITY_ID_PLACEHOLDER' and entities:
                param_value = entities[0].id  # Use first found entity
                resolved_route = resolved_route.replace('ENTITY_ID_PLACEHOLDER', param_value)
            
            parameters.append(RouteParameter(
                name=param.get('name') or '',  # Handle None values
                value=param_value,
                type=param.get('type') or 'string',  # Handle None values
                source=param.get('source') or 'llm'  # Handle None values
            ))
        
        # Convert entities to ActionPlan format
        from ..models.actions import EntityMatch as ActionEntityMatch
        action_entities = []
        for entity in entities:
            action_entity = ActionEntityMatch(
                id=entity.id,
                name=entity.name,
                table=entity.table,
                confidence=entity.confidence,
                metadata=entity.raw_data
            )
            action_entities.append(action_entity)
        
        # Safely extract action type
        action_type_str = intent.get('action_type') or 'NAVIGATE'
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            action_type = ActionType.NAVIGATE
        
        # Safely extract confidence
        try:
            confidence = float(llm_response.get('overall_confidence', 0.5))
        except (ValueError, TypeError):
            confidence = 0.5
        
        return ActionPlan(
            action_type=action_type,
            route=resolved_route,
            confidence=confidence,
            parameters=parameters,
            entities=action_entities,
            reasoning=llm_response.get('reasoning') or 'LLM analysis completed',
            query_params={},
            matched_pattern=route_info.get('matched_pattern') or '',
            alternatives=[]
        ) 