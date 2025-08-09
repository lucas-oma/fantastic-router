"""
PostgreSQL database client adapter for Fantastic Router
"""

import asyncpg
import json
from typing import List, Dict, Any, Optional
import asyncio

# TODO: here and in every db connector, we should have a list of restricted tables and/or columns.

class PostgreSQLDatabaseClient:
    """PostgreSQL client that implements the DatabaseClient protocol"""
    
    def __init__(
        self,
        connection_string: str,
        max_connections: int = 10,
        timeout: int = 30
    ):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool: Optional[asyncpg.Pool] = None
        self._schema_cache: Dict[str, List[str]] = {}  # Cache table columns
    
    async def initialize(self):
        """Initialize the connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                max_size=self.max_connections,
                timeout=self.timeout
            )
    
    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def search(
        self,
        query: str,
        tables: List[str],
        fields: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in the database
        
        Args:
            query: Search query string
            tables: List of table names to search
            fields: List of field names to search in
            limit: Maximum number of results
            
        Returns:
            List of matching records as dictionaries
        """
        
        if not self.pool:
            await self.initialize()
        
        results = []
        
        async with self.pool.acquire() as conn:
            for table in tables:
                try:
                    # Use cached columns if available
                    if table in self._schema_cache:
                        available_columns = self._schema_cache[table]
                    else:
                        # Get actual text/searchable columns for this table
                        table_columns = await conn.fetch(
                            """SELECT column_name, data_type 
                               FROM information_schema.columns 
                               WHERE table_name = $1 AND table_schema = 'public'
                               AND data_type IN ('character varying', 'varchar', 'text', 'char', 'character')""",
                            table
                        )
                        available_columns = [row['column_name'] for row in table_columns]
                        self._schema_cache[table] = available_columns  # Cache for next time
                    
                    # Filter fields to only include existing columns
                    valid_fields = [field for field in fields if field in available_columns]
                    
                    if not valid_fields:
                        # If no specified fields exist, try common search fields
                        common_fields = ['name', 'email', 'address', 'title']
                        valid_fields = [field for field in common_fields if field in available_columns]
                    
                    if not valid_fields:
                        continue  # Skip this table if no searchable fields
                    
                    # Build search query with valid fields only
                    sql, params = self._build_search_query(query, table, valid_fields, limit)
                    
                    # Execute query
                    rows = await conn.fetch(sql, *params)
                    
                    # Convert to dictionaries
                    for row in rows:
                        record = dict(row)
                        results.append(record)
                        
                except Exception as e:
                    print(f"Error searching table {table}: {e}")
                    continue
        
        return results[:limit]  # Ensure we don't exceed limit
    
    def _build_search_query(
        self,
        query: str,
        table: str,
        fields: List[str],
        limit: int
    ) -> tuple[str, List[Any]]:
        """Build SQL search query with parameters"""
        
        # Sanitize table name (basic protection)
        if not table.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: {table}")
        
        # Build WHERE conditions for each field
        where_conditions = []
        params = []
        
        for i, field in enumerate(fields):
            # Sanitize field name
            if not field.replace('_', '').isalnum():
                continue
            
            # Add ILIKE condition for case-insensitive search
            where_conditions.append(f"{field} ILIKE ${len(params) + 1}")
            params.append(f"%{query}%")
        
        if not where_conditions:
            # Fallback: search all text fields
            where_conditions = [f"CAST(column_name AS TEXT) ILIKE ${len(params) + 1}"]
            params.append(f"%{query}%")
        
        # Combine conditions with OR
        where_clause = " OR ".join(where_conditions)
        
        # Build final query
        sql = f"""
        SELECT * 
        FROM {table} 
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN {fields[0] if fields else 'id'} ILIKE ${len(params) + 1} THEN 1
                ELSE 2 
            END,
            {fields[0] if fields else 'id'}
        LIMIT ${len(params) + 2}
        """
        
        # Add exact match parameter for ordering
        params.append(query)
        params.append(limit)
        
        return sql, params
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        
        if not self.pool:
            await self.initialize()
        
        schema = {"tables": {}, "relationships": {}}
        
        async with self.pool.acquire() as conn:
            # Get table information
            tables_query = """
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
            
            rows = await conn.fetch(tables_query)
            
            # Group by table
            for row in rows:
                table_name = row['table_name']
                
                if table_name not in schema["tables"]:
                    schema["tables"][table_name] = {
                        "name": table_name,
                        "columns": [],
                        "primary_key": "id"  # Assume 'id' for now
                    }
                
                schema["tables"][table_name]["columns"].append({
                    "name": row['column_name'],
                    "type": row['data_type'],
                    "nullable": row['is_nullable'] == 'YES',
                    "description": None  # Could be enhanced with comments
                })
            
            # Get foreign key relationships
            fk_query = """
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """
            
            fk_rows = await conn.fetch(fk_query)
            
            for row in fk_rows:
                key = f"{row['table_name']}.{row['column_name']}"
                value = f"{row['foreign_table_name']}.{row['foreign_column_name']}"
                schema["relationships"][key] = value
        
        return schema
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        
        try:
            if not self.pool:
                await self.initialize()
            
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False


# Convenience function for creating PostgreSQL client
def create_postgres_client(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    max_connections: int = 10,
    timeout: int = 30
) -> PostgreSQLDatabaseClient:
    """Create a PostgreSQL database client"""
    
    connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    return PostgreSQLDatabaseClient(
        connection_string=connection_string,
        max_connections=max_connections,
        timeout=timeout
    )
