from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
import asyncio
import json

from ..models.entities import EntityMatch, EntitySearchRequest, EntitySearchResult, SearchStrategy


class DatabaseClient(Protocol):
    """Protocol for database clients"""
    async def search(
        self, 
        query: str, 
        tables: List[str], 
        fields: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for entities in the database"""
        ...


class EntityResolver:
    """Resolves entities by searching the database with various strategies"""
    
    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client
        self.search_strategies = {
            SearchStrategy.EXACT_MATCH: self._exact_match_search,
            SearchStrategy.FUZZY_MATCH: self._fuzzy_match_search,
            SearchStrategy.SEMANTIC_SEARCH: self._semantic_search,
            SearchStrategy.FULL_TEXT_SEARCH: self._full_text_search,
        }
    
    async def search_entity(
        self,
        entity_name: str,
        tables: List[str],
        search_fields: List[str],
        join_strategy: Optional[str] = None,
        max_results: int = 10,
        min_confidence: float = 0.5
    ) -> List[EntityMatch]:
        """Search for an entity using multiple strategies"""
        
        all_matches = []
        
        # Try different search strategies in order of preference
        strategies = [
            SearchStrategy.EXACT_MATCH,
            SearchStrategy.FUZZY_MATCH,
            SearchStrategy.SEMANTIC_SEARCH,
            SearchStrategy.FULL_TEXT_SEARCH
        ]
        
        for strategy in strategies:
            try:
                matches = await self._search_with_strategy(
                    strategy=strategy,
                    entity_name=entity_name,
                    tables=tables,
                    search_fields=search_fields,
                    max_results=max_results
                )
                
                # Filter by confidence threshold
                quality_matches = [m for m in matches if m.confidence >= min_confidence]
                all_matches.extend(quality_matches)
                
                # If we found high-confidence matches, we can stop
                if quality_matches and max(m.confidence for m in quality_matches) > 0.8:
                    break
                    
            except Exception as e:
                # Log error but continue with other strategies
                print(f"Error in {strategy.value} search: {e}")
                continue
        
        # Deduplicate and sort by confidence
        deduplicated = self._deduplicate_matches(all_matches)
        return sorted(deduplicated, key=lambda x: x.confidence, reverse=True)[:max_results]
    
    async def _search_with_strategy(
        self,
        strategy: SearchStrategy,
        entity_name: str,
        tables: List[str],
        search_fields: List[str],
        max_results: int
    ) -> List[EntityMatch]:
        """Search using a specific strategy"""
        
        search_func = self.search_strategies.get(strategy)
        if not search_func:
            return []
        
        return await search_func(entity_name, tables, search_fields, max_results)
    
    async def _exact_match_search(
        self,
        entity_name: str,
        tables: List[str],
        search_fields: List[str],
        max_results: int
    ) -> List[EntityMatch]:
        """Exact string matching search"""
        
        matches = []
        
        for table in tables:
            try:
                # Search for exact matches in specified fields
                results = await self.db_client.search(
                    query=entity_name,
                    tables=[table],
                    fields=search_fields,
                    limit=max_results
                )
                
                for result in results:
                    match = self._convert_to_entity_match(
                        result, table, entity_name, search_fields, 
                        confidence=0.95,  # High confidence for exact matches
                        strategy="exact_match"
                    )
                    if match:
                        matches.append(match)
                        
            except Exception as e:
                print(f"Error in exact search for table {table}: {e}")
                continue
        
        return matches
    
    async def _fuzzy_match_search(
        self,
        entity_name: str,
        tables: List[str],
        search_fields: List[str],
        max_results: int
    ) -> List[EntityMatch]:
        """Fuzzy string matching search"""
        
        # For now, implement a simple fuzzy search
        # In production, you'd use proper fuzzy matching algorithms
        
        fuzzy_queries = [
            entity_name.lower(),
            entity_name.replace(" ", ""),
            entity_name.split()[0] if " " in entity_name else entity_name,  # First name only
        ]
        
        matches = []
        
        for table in tables:
            for fuzzy_query in fuzzy_queries:
                try:
                    results = await self.db_client.search(
                        query=fuzzy_query,
                        tables=[table],
                        fields=search_fields,
                        limit=max_results
                    )
                    
                    for result in results:
                        # Calculate fuzzy confidence based on similarity
                        confidence = self._calculate_fuzzy_confidence(entity_name, result, search_fields)
                        
                        if confidence > 0.6:  # Only include reasonable matches
                            match = self._convert_to_entity_match(
                                result, table, entity_name, search_fields,
                                confidence=confidence,
                                strategy="fuzzy_match"
                            )
                            if match:
                                matches.append(match)
                                
                except Exception as e:
                    print(f"Error in fuzzy search for table {table}: {e}")
                    continue
        
        return matches
    
    async def _semantic_search(
        self,
        entity_name: str,
        tables: List[str],
        search_fields: List[str],
        max_results: int
    ) -> List[EntityMatch]:
        """Semantic/vector-based search (placeholder)"""
        
        # TODO: Implement actual semantic search using embeddings
        # For now, return empty list
        return []
    
    async def _full_text_search(
        self,
        entity_name: str,
        tables: List[str],
        search_fields: List[str],
        max_results: int
    ) -> List[EntityMatch]:
        """Full-text search across fields"""
        
        # Similar to fuzzy but with broader text matching
        matches = []
        
        # Split entity name into tokens for broader matching
        tokens = entity_name.lower().split()
        
        for table in tables:
            try:
                # Search for any token matches
                for token in tokens:
                    if len(token) > 2:  # Skip very short tokens
                        results = await self.db_client.search(
                            query=token,
                            tables=[table],
                            fields=search_fields,
                            limit=max_results
                        )
                        
                        for result in results:
                            confidence = self._calculate_text_match_confidence(entity_name, result, search_fields)
                            
                            if confidence > 0.4:  # Lower threshold for text search
                                match = self._convert_to_entity_match(
                                    result, table, entity_name, search_fields,
                                    confidence=confidence,
                                    strategy="full_text_search"
                                )
                                if match:
                                    matches.append(match)
                                    
            except Exception as e:
                print(f"Error in full-text search for table {table}: {e}")
                continue
        
        return matches
    
    def _convert_to_entity_match(
        self,
        result: Dict[str, Any],
        table: str,
        original_query: str,
        search_fields: List[str],
        confidence: float,
        strategy: str
    ) -> Optional[EntityMatch]:
        """Convert database result to EntityMatch"""
        
        try:
            # Try to extract ID and name from result
            entity_id = str(result.get('id', result.get('uuid', result.get('pk', ''))))
            
            # Try to find the best display name
            entity_name = ''
            for field in search_fields:
                if field in result and result[field]:
                    entity_name = str(result[field])
                    break
            
            if not entity_id or not entity_name:
                return None
            
            # Determine which fields matched
            matched_fields = []
            for field in search_fields:
                if field in result and original_query.lower() in str(result[field]).lower():
                    matched_fields.append(field)
            
            return EntityMatch(
                id=entity_id,
                name=entity_name,
                table=table,
                entity_type=self._infer_entity_type_from_table(table),
                confidence=confidence,
                matched_fields=matched_fields,
                raw_data=result,
                reasoning=f"Found via {strategy} in {table}.{','.join(matched_fields)}"
            )
            
        except Exception as e:
            print(f"Error converting result to EntityMatch: {e}")
            return None
    
    def _calculate_fuzzy_confidence(
        self, 
        query: str, 
        result: Dict[str, Any], 
        search_fields: List[str]
    ) -> float:
        """Calculate confidence for fuzzy matches"""
        
        query_lower = query.lower()
        max_confidence = 0.0
        
        for field in search_fields:
            if field in result and result[field]:
                field_value = str(result[field]).lower()
                
                # Simple similarity calculation
                if query_lower == field_value:
                    max_confidence = max(max_confidence, 0.95)
                elif query_lower in field_value or field_value in query_lower:
                    max_confidence = max(max_confidence, 0.8)
                elif any(word in field_value for word in query_lower.split()):
                    max_confidence = max(max_confidence, 0.6)
        
        return max_confidence
    
    def _calculate_text_match_confidence(
        self,
        query: str,
        result: Dict[str, Any],
        search_fields: List[str]
    ) -> float:
        """Calculate confidence for text matches"""
        
        # Similar to fuzzy but with lower baseline confidence
        return max(0.4, self._calculate_fuzzy_confidence(query, result, search_fields) * 0.7)
    
    def _infer_entity_type_from_table(self, table: str) -> str:
        """Infer entity type from table name"""
        
        # TODO: should be enhanced with configuration
        table_lower = table.lower()
        
        if 'user' in table_lower or 'person' in table_lower:
            return 'person'
        elif 'property' in table_lower or 'building' in table_lower:
            return 'property'
        elif 'landlord' in table_lower or 'owner' in table_lower:
            return 'landlord'
        elif 'tenant' in table_lower or 'renter' in table_lower:
            return 'tenant'
        else:
            return table_lower.rstrip('s')  # Remove plural 's'
    
    def _deduplicate_matches(self, matches: List[EntityMatch]) -> List[EntityMatch]:
        """Remove duplicate matches based on ID and table"""
        
        seen = set()
        deduplicated = []
        
        for match in matches:
            key = f"{match.table}:{match.id}"
            if key not in seen:
                seen.add(key)
                deduplicated.append(match)
        
        return deduplicated
