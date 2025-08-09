import json
from typing import Dict, List, Any, Optional

from ..models.actions import ActionPlan, ActionType, RouteParameter, PlanningContext
from ..models.entities import EntityMatch, EntityResolutionPlan
from ..models.site import RoutePattern, SiteConfiguration
from .intent_parser import IntentParser, IntentAnalysis, LLMClient


class RouteMatch:
    """Result of matching a route pattern"""
    def __init__(
        self,
        pattern: str,
        resolved_route: str,
        parameters: List[RouteParameter],
        confidence: float,
        reasoning: str
    ):
        self.pattern = pattern
        self.resolved_route = resolved_route
        self.parameters = parameters
        self.confidence = confidence
        self.reasoning = reasoning


class ActionPlanner:
    """Main action planner that orchestrates intent parsing, entity resolution, and route generation"""
    
    def __init__(self, llm_client: LLMClient, entity_resolver: Any):
        self.llm = llm_client
        self.intent_parser = IntentParser(llm_client)
        self.entity_resolver = entity_resolver
    
    async def plan_action(
        self, 
        context: PlanningContext
    ) -> ActionPlan:
        """Plan an action based on user query and context"""
        
        # Step 1: Parse intent
        intent = await self._parse_intent(context)
        
        # Step 2: Resolve entities
        entities = await self._resolve_entities(context, intent)
        
        # Step 3: Match route pattern
        route_match = await self._match_route_pattern(context, intent, entities)
        
        # Step 4: Generate final action plan
        return self._build_action_plan(context, intent, entities, route_match)
    
    async def _parse_intent(self, context: PlanningContext) -> IntentAnalysis:
        """Parse user intent from query"""
        from ..models.entities import DomainContext
        
        # Build domain context from site configuration
        domain_context = DomainContext(
            domain_name=context.domain,
            primary_entities=list(context.database_schema.get('entities', {}).keys()),
            common_relationships={},  # TODO: Extract from schema
            domain_vocabulary={}  # TODO: Load from configuration
        )
        
        return await self.intent_parser.parse_intent(
            context.user_query,
            domain_context,
            context.route_patterns
        )
    
    async def _resolve_entities(
        self, 
        context: PlanningContext, 
        intent: IntentAnalysis
    ) -> List[EntityMatch]:
        """Resolve entities mentioned in the query"""
        
        if not intent.entities:
            return []
        
        # Get entity resolution plan from LLM
        from ..models.entities import DomainContext
        domain_context = DomainContext(
            domain_name=context.domain,
            primary_entities=list(context.database_schema.get('entities', {}).keys()),
            common_relationships={},
            domain_vocabulary={}
        )
        
        resolution_plan = await self.intent_parser.analyze_entities_in_context(
            context.user_query,
            intent.entities,
            context.database_schema,
            domain_context
        )
        
        # Execute entity search using the resolver
        resolved_entities = []
        for strategy in resolution_plan.resolution_strategies:
            matches = await self.entity_resolver.search_entity(
                entity_name=strategy.entity_name,
                tables=strategy.recommended_tables,
                search_fields=strategy.search_fields,
                join_strategy=strategy.join_strategy
            )
            resolved_entities.extend(matches)
        
        return resolved_entities
    
    async def _match_route_pattern(
        self,
        context: PlanningContext,
        intent: IntentAnalysis,
        entities: List[EntityMatch]
    ) -> RouteMatch:
        """Match intent to a route pattern using LLM"""
        
        prompt = self._build_route_matching_prompt(context, intent, entities)
        response = await self.llm.analyze(prompt, temperature=0.1)
        
        return self._parse_route_match_response(response, entities)
    
    def _build_route_matching_prompt(
        self,
        context: PlanningContext,
        intent: IntentAnalysis,
        entities: List[EntityMatch]
    ) -> str:
        """Build prompt for route pattern matching"""
        
        # Format available patterns
        patterns_text = ""
        for pattern in context.route_patterns:
            patterns_text += f"""
Pattern: {pattern.get('pattern', '')}
Description: {pattern.get('description', '')}
Intent Patterns: {pattern.get('intent_patterns', [])}
Parameters: {list(pattern.get('parameters', {}).keys())}
"""
        
        # Format resolved entities
        entities_text = ""
        for entity in entities:
            entities_text += f"- {entity.name} (ID: {entity.id}, Table: {entity.table}, Type: {entity.entity_type})\n"
        
        return f"""
You are an expert at matching user intents to web application routes.

USER QUERY: "{context.user_query}"
PARSED INTENT: {intent.action_type.value}
VIEW TYPE: {intent.view_type or 'None'}
RESOLVED ENTITIES:
{entities_text}

AVAILABLE ROUTE PATTERNS:
{patterns_text}

TASK: Match the intent to the best route pattern and fill in the parameters.

Consider:
1. Which pattern best matches the intent and action type?
2. How should the pattern variables be filled using the resolved entities?
3. What query parameters might be needed?
4. What's your confidence in this match?

RESPONSE FORMAT (JSON):
{{
    "matched_pattern": "/pattern/from/list",
    "resolved_route": "/actual/resolved/path",
    "parameters": [
        {{
            "name": "param_name",
            "value": "resolved_value",
            "type": "string",
            "source": "entity|literal|computed"
        }}
    ],
    "query_params": {{
        "param1": "value1"
    }},
    "confidence": 0.9,
    "reasoning": "Why this pattern was chosen and how parameters were resolved"
}}

EXAMPLES:
- Query: "show James Smith income" --> Pattern: "/{{entity_type}}/{{entity_id}}/{{view_type}}" --> Route: "/landlords/james-smith-123/financials"
- Query: "create new property" --> Pattern: "/{{entity_type}}/create" --> Route: "/properties/create"

Match the route now:
"""

    # TODO: check why entities are not used in the response
    def _parse_route_match_response(
        self, 
        response: Dict[str, Any], 
        entities: List[EntityMatch]
    ) -> RouteMatch:
        """Parse LLM response into RouteMatch"""
        
        try:
            parameters = []
            for param in response.get('parameters', []):
                parameters.append(RouteParameter(
                    name=param.get('name', ''),
                    value=param.get('value', ''),
                    type=param.get('type', 'string'),
                    source=param.get('source', 'unknown')
                ))
            
            return RouteMatch(
                pattern=response.get('matched_pattern', ''),
                resolved_route=response.get('resolved_route', ''),
                parameters=parameters,
                confidence=float(response.get('confidence', 0.0)),
                reasoning=response.get('reasoning', '')
            )
            
        except (ValueError, KeyError) as e:
            # Fallback for malformed responses
            return RouteMatch(
                pattern="",
                resolved_route="/",
                parameters=[],
                confidence=0.0,
                reasoning=f"Failed to parse route match: {e}"
            )
    
    # TODO: check why is context not used in the action plan
    def _build_action_plan(
        self,
        context: PlanningContext,
        intent: IntentAnalysis,
        entities: List[EntityMatch],
        route_match: RouteMatch
    ) -> ActionPlan:
        """Build the final action plan"""
        
        # Convert EntityMatch to the ActionPlan's EntityMatch format
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
        
        # Build reasoning
        reasoning = f"""
Intent Analysis: {intent.reasoning}
Entity Resolution: Found {len(entities)} entities
Route Matching: {route_match.reasoning}
Overall Confidence: {min(intent.confidence, route_match.confidence)}
"""
        
        return ActionPlan(
            action_type=intent.action_type,
            route=route_match.resolved_route,
            confidence=min(intent.confidence, route_match.confidence),
            parameters=route_match.parameters,
            entities=action_entities,
            reasoning=reasoning.strip(),
            query_params={},  # TODO: Extract from route_match if needed
            matched_pattern=route_match.pattern,
            alternatives=[]  # TODO: Generate alternatives
        )
    
    async def generate_alternatives(
        self, 
        primary_plan: ActionPlan,
        context: PlanningContext
    ) -> List[ActionPlan]:
        """Generate alternative action plans"""
        
        # TODO: This could be enhanced to generate multiple interpretations
        # For now, return empty list
        return []
