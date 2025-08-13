"""
Supabase database client adapter for Fantastic Router
"""

from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from postgrest import APIError

class SupabaseDatabaseClient:
    """Supabase client that implements the DatabaseClient protocol"""
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        max_connections: int = 10,
        timeout: int = 30,
        restricted_tables: Optional[List[str]] = None,
        restricted_columns: Optional[Dict[str, List[str]]] = None,
        allowed_tables: Optional[List[str]] = None
    ):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.max_connections = max_connections
        self.timeout = timeout
        self.client: Optional[Client] = None
        self._schema_cache: Dict[str, List[str]] = {}
        
        # Security: Restricted tables/columns that should never be accessed
        self.restricted_tables = set(restricted_tables or [
            'auth', 'storage', 'realtime', 'pg_', 'information_schema',
            'pg_catalog', 'pg_toast', 'pg_stat', 'pg_statistic'
        ])
        
        # Security: Specific columns that should never be accessed
        self.restricted_columns = restricted_columns or {
            'users': ['password_hash', 'password_salt', 'reset_token', 'api_key'],
            'sessions': ['session_data', 'token_hash'],
            'audit_logs': ['ip_address', 'user_agent', 'request_body'],
            'config': ['secret_key', 'api_keys', 'private_data']
        }
        
        # Security: Whitelist of allowed tables (if specified, only these are accessible)
        self.allowed_tables = set(allowed_tables) if allowed_tables else None
    
    async def initialize(self):
        """Initialize the Supabase client"""
        if not self.client:
            self.client = create_client(self.supabase_url, self.supabase_key)
    
    async def close(self):
        """Close the client connection"""
        # Supabase client doesn't need explicit closing
        pass
    
    def _validate_table_access(self, table: str) -> bool:
        """Validate if a table can be accessed based on security rules"""
        # Check if table is in restricted list
        if any(restricted in table.lower() for restricted in self.restricted_tables):
            return False
        
        # Check if table is in allowed list (whitelist mode)
        if self.allowed_tables and table not in self.allowed_tables:
            return False
        
        return True
    
    def _validate_column_access(self, table: str, column: str) -> bool:
        """Validate if a column can be accessed based on security rules"""
        # Check if column is restricted for this table
        if table in self.restricted_columns and column in self.restricted_columns[table]:
            return False
        
        return True
    
    def _filter_restricted_columns(self, table: str, columns: List[str]) -> List[str]:
        """Filter out restricted columns from a list"""
        if table not in self.restricted_columns:
            return columns
        
        restricted = set(self.restricted_columns[table])
        return [col for col in columns if col not in restricted]
    
    async def search(
        self,
        query: str,
        tables: List[str],
        fields: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in Supabase
        
        Args:
            query: Search query string
            tables: List of table names to search
            fields: List of field names to search in
            limit: Maximum number of results
            
        Returns:
            List of matching records as dictionaries
        """
        
        if not self.client:
            await self.initialize()
        
        results = []
        
        for table in tables:
            try:
                # Security: Validate table access
                if not self._validate_table_access(table):
                    continue  # Skip restricted tables
                
                # Get table reference
                table_ref = self.client.table(table)
                
                # Build search query
                search_query = table_ref.select('*')
                
                # Add text search filters for each field
                search_conditions = []
                for field in fields:
                    if self._validate_column_access(table, field):
                        # Use ilike for case-insensitive search
                        search_conditions.append(f"{field}.ilike.%{query}%")
                
                if search_conditions:
                    # Apply search conditions
                    for condition in search_conditions:
                        search_query = search_query.or_(condition)
                    
                    # Execute query with limit
                    response = search_query.limit(limit).execute()
                    
                    # Process results
                    for row in response.data:
                        # Filter out restricted columns
                        filtered_row = {}
                        for key, value in row.items():
                            if self._validate_column_access(table, key):
                                filtered_row[key] = value
                        
                        if filtered_row:
                            results.append(filtered_row)
                
            except APIError as e:
                # Log error but continue with other tables
                print(f"Supabase API error for table {table}: {e}")
                continue
            except Exception as e:
                # Log error but continue with other tables
                print(f"Error searching table {table}: {e}")
                continue
        
        return results[:limit]
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        if not self.client:
            await self.initialize()
        
        try:
            # Get schema information using Supabase's introspection
            # This is a simplified version - in production you might want more details
            schema = {
                "tables": {},
                "entities": {}
            }
            
            # For now, return a basic schema structure
            # In a real implementation, you'd query the information_schema
            return schema
            
        except Exception as e:
            print(f"Error getting schema: {e}")
            return {"tables": {}, "entities": {}}
    
    async def test_connection(self) -> bool:
        """Test the connection to Supabase"""
        try:
            if not self.client:
                await self.initialize()
            
            # Try a simple query to test connection
            # Use a table that should exist in most Supabase setups
            response = self.client.table('users').select('id').limit(1).execute()
            return True
            
        except Exception as e:
            print(f"Supabase connection test failed: {e}")
            return False


def create_supabase_client(
    supabase_url: str,
    supabase_key: str,
    max_connections: int = 10,
    timeout: int = 30,
    restricted_tables: Optional[List[str]] = None,
    restricted_columns: Optional[Dict[str, List[str]]] = None,
    allowed_tables: Optional[List[str]] = None
) -> SupabaseDatabaseClient:
    """Create a Supabase database client"""
    
    return SupabaseDatabaseClient(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        max_connections=max_connections,
        timeout=timeout,
        restricted_tables=restricted_tables,
        restricted_columns=restricted_columns,
        allowed_tables=allowed_tables
    )

