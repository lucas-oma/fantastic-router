"""
Optimized single-call action planner for faster performance
"""

import json
from typing import Dict, List, Any, Optional
import re # Added for regex validation

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

🔒 CRITICAL CONSTRAINT: You MUST ONLY use the route patterns provided below. NEVER invent new routes!

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

🚨 ROUTE VALIDATION REQUIREMENTS:
- The resolved_route MUST exactly match one of the patterns above
- Replace pattern variables with actual values (e.g., {{entity_type}} -> "landlords")
- If no exact match, use the closest pattern and adapt it
- NEVER return routes that don't follow the defined patterns
- If unsure, default to search routes (e.g., /landlords/search)

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
--> Route: /landlords/ENTITY_ID_PLACEHOLDER/financials

Query: "create new property"  
--> CREATE action, no entity search needed
--> Route: /properties/create

Query: "find properties"
--> QUERY action, no specific entity
--> Route: /properties/search

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
        if not route_patterns:
            return "NO ROUTE PATTERNS AVAILABLE - USE FALLBACK ROUTES ONLY"
        
        patterns = []
        patterns.append("🔒 CRITICAL: You MUST use ONLY these route patterns:")
        patterns.append("")
        
        for i, pattern_data in enumerate(route_patterns, 1):
            # Handle both dict and Pydantic objects
            if hasattr(pattern_data, 'pattern'):
                # Pydantic object
                pattern_str = pattern_data.pattern
                description = pattern_data.description
                intent_patterns = pattern_data.intent_patterns
                parameters = pattern_data.parameters
            else:
                # Dictionary
                pattern_str = pattern_data.get('pattern', '')
                description = pattern_data.get('description', '')
                intent_patterns = pattern_data.get('intent_patterns', [])
                parameters = pattern_data.get('parameters', {})
            
            patterns.append(f"{i}. PATTERN: {pattern_str}")
            patterns.append(f"   Description: {description}")
            
            if intent_patterns:
                patterns.append(f"   Intent Examples:")
                for intent in intent_patterns[:3]:  # Limit examples
                    patterns.append(f"     - \"{intent}\"")
            
            if parameters:
                patterns.append(f"   Parameters:")
                for param_name, param_info in parameters.items():
                    if hasattr(param_info, 'type'):
                        # Pydantic object
                        param_type = param_info.type
                        required = param_info.required
                        examples = getattr(param_info, 'examples', [])
                    else:
                        # Dictionary
                        param_type = param_info.get('type', 'string')
                        required = param_info.get('required', False)
                        examples = param_info.get('examples', [])
                    
                    req_text = "REQUIRED" if required else "optional"
                    examples_text = f" (examples: {', '.join(examples[:3])})" if examples else ""
                    patterns.append(f"     - {param_name}: {param_type} ({req_text}){examples_text}")
            
            patterns.append("")
        
        patterns.append("🚨 ROUTE VALIDATION RULES:")
        patterns.append("- You MUST return a route that EXACTLY matches one of the patterns above")
        patterns.append("- If no pattern matches, use the most similar pattern and adapt it")
        patterns.append("- NEVER invent new route patterns")
        patterns.append("- NEVER use routes that don't follow the defined patterns")
        patterns.append("- If unsure, use a search route (e.g., /{entity_type}/search)")
        patterns.append("")
        
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
        
        # Validate that the LLM used a valid route pattern
        resolved_route = route_info.get('resolved_route') or '/'
        matched_pattern = route_info.get('matched_pattern') or ''
        
        # Check if the route matches any defined pattern
        is_valid_route = self._validate_llm_route(resolved_route, context.route_patterns)
        if not is_valid_route:
            print(f"⚠️  LLM returned invalid route: {resolved_route}")
            print(f"⚠️  Attempted pattern: {matched_pattern}")
            # Use fallback route
            resolved_route = self._get_fallback_route(context.route_patterns)
            print(f"✅ Using fallback route: {resolved_route}")
        
        # Build parameters, replacing placeholders with actual entity IDs
        parameters = []
        
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
        
        # Reduce confidence if we had to use fallback route
        if not is_valid_route:
            confidence = max(0.1, confidence - 0.3)
        
        return ActionPlan(
            action_type=action_type,
            route=resolved_route,
            confidence=confidence,
            parameters=parameters,
            entities=action_entities,
            reasoning=f"LLM Analysis: {llm_response.get('reasoning', 'No reasoning provided')}",
            query_params={},
            matched_pattern=matched_pattern,
            alternatives=[]
        )
    
    def _validate_llm_route(self, route: str, route_patterns: List[Dict[str, Any]]) -> bool:
        """Validate that the LLM returned a route matching our patterns"""
        if not route or not route.startswith('/'):
            return False
        
        # Check if route matches any defined pattern
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
            regex_pattern = self._pattern_to_regex(pattern)
            if regex_pattern and re.match(regex_pattern, route):
                return True
        
        return False
    
    def _pattern_to_regex(self, pattern: str) -> str:
        """Convert route pattern to regex for validation"""
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
    
    def _get_fallback_route(self, route_patterns: List[Dict[str, Any]]) -> str:
        """Get a safe fallback route"""
        # Look for a search pattern first
        for pattern_data in route_patterns:
            pattern = pattern_data.get('pattern', '')
            if 'search' in pattern:
                return pattern.replace('{entity_type}', 'landlords')
        
        # Fallback to first pattern
        if route_patterns:
            pattern = route_patterns[0].get('pattern', '')
            return pattern.replace('{entity_type}', 'landlords').replace('{entity_id}', 'search').replace('{view_type}', 'overview')
        
        return "/landlords/search" 