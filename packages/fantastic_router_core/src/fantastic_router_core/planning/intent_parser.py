import json
from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod

from ..models.actions import ActionType
from ..models.entities import EntityResolutionPlan, ContextualEntityResolution, DomainContext


class LLMClient(Protocol):
    """Protocol for LLM clients"""
    async def analyze(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Analyze a prompt and return structured response"""
        ...


class IntentAnalysis:
    """Result of intent analysis"""
    def __init__(
        self,
        action_type: ActionType,
        entities: List[str],
        view_type: Optional[str] = None,
        confidence: float = 0.0,
        reasoning: str = "",
        context_clues: List[str] = None
    ):
        self.action_type = action_type
        self.entities = entities
        self.view_type = view_type
        self.confidence = confidence
        self.reasoning = reasoning
        self.context_clues = context_clues or []


class IntentParser:
    """LLM-powered intent parser that understands user queries"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def parse_intent(
        self, 
        query: str, 
        domain_context: DomainContext,
        route_patterns: List[Dict[str, Any]]
    ) -> IntentAnalysis:
        """Parse user intent from natural language query"""
        
        prompt = self._build_intent_prompt(query, domain_context, route_patterns)
        response = await self.llm.analyze(prompt, temperature=0.1)
        
        return self._parse_llm_response(response)
    
    async def analyze_entities_in_context(
        self,
        query: str,
        entities: List[str],
        database_schema: Dict[str, Any],
        domain_context: DomainContext
    ) -> EntityResolutionPlan:
        """Analyze how to resolve entities based on query context"""
        
        prompt = self._build_entity_resolution_prompt(
            query, entities, database_schema, domain_context
        )
        response = await self.llm.analyze(prompt, temperature=0.1)
        
        return self._parse_entity_resolution_response(response, query, entities, domain_context)
    
    def _build_intent_prompt(
        self, 
        query: str, 
        domain_context: DomainContext,
        route_patterns: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for intent analysis"""
        
        pattern_examples = self._format_pattern_examples(route_patterns)
        
        # TODO: The only actions should be NAVIGATE and QUERY. Navigate should redirect to views were user creates/edit something.
        return f"""
You are an expert at understanding user intents for web application navigation.

DOMAIN CONTEXT:
- Domain: {domain_context.domain_name}
- Primary entities: {', '.join(domain_context.primary_entities)}
- Domain vocabulary: {json.dumps(domain_context.domain_vocabulary, indent=2)}

AVAILABLE ROUTE PATTERNS:
{pattern_examples}

USER QUERY: "{query}"

TASK: Analyze this query and determine:
1. What ACTION the user wants to perform (NAVIGATE, CREATE, EDIT, DELETE, QUERY)
2. What ENTITIES are mentioned in the query
3. What VIEW TYPE or data they want to see (if applicable)
4. Your confidence level (0.0 to 1.0)
5. Your reasoning

RESPONSE FORMAT (JSON):
{{
    "action_type": "NAVIGATE|CREATE|EDIT|DELETE|QUERY",
    "entities": ["entity1", "entity2"],
    "view_type": "specific_view_or_null",
    "confidence": 0.85,
    "reasoning": "Detailed explanation of your analysis",
    "context_clues": ["clue1", "clue2"]
}}

EXAMPLES:
- "show me James Smith's income" --> NAVIGATE, entities: ["James Smith"], view_type: "income"
- "create new property" --> CREATE, entities: ["property"], view_type: null
- "update John's contact info" --> EDIT, entities: ["John"], view_type: "contact"

Analyze the query now:
"""

    def _build_entity_resolution_prompt(
        self,
        query: str,
        entities: List[str], 
        database_schema: Dict[str, Any],
        domain_context: DomainContext
    ) -> str:
        """Build prompt for entity resolution analysis"""
        
        schema_summary = self._format_schema_summary(database_schema)
        
        # TODO: im not sure if this is able to redirect to URLs, since it does not create them
        return f"""
You are an expert at resolving entities in database queries.

DOMAIN: {domain_context.domain_name}
QUERY: "{query}"
ENTITIES TO RESOLVE: {entities}

DATABASE SCHEMA:
{schema_summary}

DOMAIN RELATIONSHIPS:
{json.dumps(domain_context.common_relationships, indent=2)}

TASK: For each entity, determine:
1. What TYPE of entity it is (person, property, etc.)
2. Which DATABASE TABLES to search
3. Which FIELDS to search in those tables
4. How to JOIN tables if needed
5. Your confidence in this strategy

Consider the CONTEXT of the query to determine entity types.
For example: "income" suggests landlord/owner, "rent payment" suggests tenant.

RESPONSE FORMAT (JSON):
{{
    "entity_resolutions": [
        {{
            "entity_name": "entity_name",
            "inferred_type": "person|property|etc",
            "confidence": 0.9,
            "recommended_tables": ["table1", "table2"],
            "search_fields": ["field1", "field2"],
            "join_strategy": "how_to_join_or_null",
            "reasoning": "why this strategy",
            "context_clues": ["clue1", "clue2"]
        }}
    ],
    "search_order": ["entity1", "entity2"],
    "estimated_confidence": 0.85
}}

Analyze the entities now:
"""

    def _format_pattern_examples(self, route_patterns: List[Dict[str, Any]]) -> str:
        """Format route patterns for the prompt"""
        examples = []
        for pattern in route_patterns[:5]:  # Limit to avoid context overflow
            examples.append(f"- {pattern.get('pattern', '')}: {pattern.get('description', '')}")
            if 'intent_patterns' in pattern:
                for intent in pattern['intent_patterns'][:2]:
                    examples.append(f"  Example: \"{intent}\"")
        return "\n".join(examples)
    
    def _format_schema_summary(self, database_schema: Dict[str, Any]) -> str:
        """Format database schema for the prompt"""
        if 'tables' not in database_schema:
            return "No schema information available"
        
        summary = []
        for table_name, table_info in database_schema['tables'].items():
            columns = []
            if 'columns' in table_info:
                columns = [col.get('name', '') for col in table_info['columns'][:10]]  # Limit columns
            summary.append(f"- {table_name}: {', '.join(columns)}")
            if 'description' in table_info:
                summary.append(f"  Description: {table_info['description']}")
        
        return "\n".join(summary)
    
    def _parse_llm_response(self, response: Dict[str, Any]) -> IntentAnalysis:
        """Parse LLM response into IntentAnalysis"""
        try:
            action_type = ActionType(response.get('action_type', 'NAVIGATE'))
            entities = response.get('entities', [])
            view_type = response.get('view_type')
            confidence = float(response.get('confidence', 0.0))
            reasoning = response.get('reasoning', '')
            context_clues = response.get('context_clues', [])
            
            return IntentAnalysis(
                action_type=action_type,
                entities=entities,
                view_type=view_type,
                confidence=confidence,
                reasoning=reasoning,
                context_clues=context_clues
            )
        except (ValueError, KeyError) as e:
            # Fallback for malformed responses
            return IntentAnalysis(
                action_type=ActionType.NAVIGATE,
                entities=[],
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {e}"
            )
    
    def _parse_entity_resolution_response(
        self, 
        response: Dict[str, Any], 
        query: str, 
        entities: List[str],
        domain_context: DomainContext
    ) -> EntityResolutionPlan:
        """Parse LLM response into EntityResolutionPlan"""
        
        try:
            resolutions = []
            for res in response.get('entity_resolutions', []):
                resolution = ContextualEntityResolution(
                    entity_name=res.get('entity_name', ''),
                    inferred_type=res.get('inferred_type', ''),
                    confidence=float(res.get('confidence', 0.0)),
                    recommended_tables=res.get('recommended_tables', []),
                    search_fields=res.get('search_fields', []),
                    join_strategy=res.get('join_strategy'),
                    reasoning=res.get('reasoning', ''),
                    context_clues=res.get('context_clues', [])
                )
                resolutions.append(resolution)
            
            return EntityResolutionPlan(
                query=query,
                entities_to_resolve=entities,
                resolution_strategies=resolutions,
                search_order=response.get('search_order', entities),
                fallback_strategies=[],  # Will be populated by search component
                domain_context=domain_context,
                estimated_confidence=float(response.get('estimated_confidence', 0.0))
            )
            
        except (ValueError, KeyError) as e:
            # Fallback for malformed responses
            return EntityResolutionPlan(
                query=query,
                entities_to_resolve=entities,
                resolution_strategies=[],
                search_order=entities,
                fallback_strategies=[],
                domain_context=domain_context,
                estimated_confidence=0.0
            )
