"""
Fantastic Router - Quickstart Example

This example shows how to set up and use the Fantastic Router
for a property management application.
"""

import asyncio
import json
import os
from pathlib import Path

# Import the router and adapters
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "packages" / "fantastic_router_core" / "src"))
sys.path.append(str(Path(__file__).parent.parent.parent / "adapters"))

from fantastic_router_core import FantasticRouter
from fantastic_router_core.models.site import SiteConfiguration
from llm.openai import OpenAILLMClient
from db.postgres import PostgreSQLDatabaseClient


async def main():
    """Main example function"""
    
    print("🚀 Fantastic Router Quickstart Example")
    print("=" * 50)
    
    # 1. Set up LLM client (OpenAI)
    print("1. Setting up LLM client...")
    llm_client = OpenAILLMClient(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        model="gpt-4",
        max_tokens=1000
    )
    
    # Test LLM connection
    if await llm_client.test_connection():
        print("   ✅ LLM client connected")
    else:
        print("   ❌ LLM client connection failed")
        return
    
    # 2. Set up database client (PostgreSQL)
    print("2. Setting up database client...")
    db_client = PostgreSQLDatabaseClient(
        connection_string=os.getenv(
            "DATABASE_URL", 
            "postgresql://user:password@localhost:5432/property_mgmt"
        )
    )
    
    # Test database connection
    if await db_client.test_connection():
        print("   ✅ Database client connected")
    else:
        print("   ❌ Database connection failed (this is expected if no DB is set up)")
        # For demo purposes, we'll continue with a mock client
        db_client = MockDatabaseClient()
    
    # 3. Load configuration
    print("3. Loading configuration...")
    config_path = Path(__file__).parent / "routes.json"
    
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    # Convert to SiteConfiguration (simplified - would need proper parsing in production)
    config = parse_site_configuration(config_dict)
    print(f"   ✅ Loaded configuration for domain: {config.domain}")
    
    # 4. Create router
    print("4. Creating Fantastic Router...")
    router = FantasticRouter(
        llm_client=llm_client,
        db_client=db_client,
        config=config
    )
    print("   ✅ Router created successfully")
    
    # 5. Test some queries
    print("\n5. Testing queries...")
    print("-" * 30)
    
    test_queries = [
        "show me James Smith's monthly income",
        "create new property",
        "edit John Doe's contact information",
        "list all tenants",
        "search for properties in downtown"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        try:
            action_plan = await router.plan(query)
            
            print(f"   Action: {action_plan.action_type.value}")
            print(f"   Route: {action_plan.route}")
            print(f"   Confidence: {action_plan.confidence:.2f}")
            print(f"   Entities: {[e.name for e in action_plan.entities]}")
            
            if action_plan.confidence < 0.5:
                print(f"   ⚠️  Low confidence - reasoning: {action_plan.reasoning}")
            else:
                print("   ✅ High confidence match")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Quickstart example completed!")
    print("\nNext steps:")
    print("- Set up your own database and update the connection string")
    print("- Customize the routes.json for your domain")
    print("- Add your OpenAI API key to environment variables")
    print("- Integrate into your web application")


class MockDatabaseClient:
    """Mock database client for demo purposes"""
    
    async def search(self, query, tables, fields, limit=10):
        """Mock search that returns fake data"""
        
        # Return some fake entities based on the query
        if "james" in query.lower() or "smith" in query.lower():
            return [
                {
                    "id": "james-smith-123",
                    "name": "James Smith",
                    "email": "james.smith@example.com",
                    "monthly_income": 5000.00
                }
            ]
        elif "john" in query.lower() or "doe" in query.lower():
            return [
                {
                    "id": "john-doe-456", 
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "monthly_rent": 1500.00
                }
            ]
        
        return []


def parse_site_configuration(config_dict):
    """Parse configuration dictionary into SiteConfiguration object"""
    
    # TODO:This is a simplified parser - in production you'd want proper validation
    from fantastic_router_core.models.site import (
        SiteConfiguration, RoutePattern, EntityDefinition, 
        DatabaseSchema, TableSchema, ColumnSchema,
        RouteParameter, ParameterType
    )
    
    # Parse entities
    entities = {}
    for name, entity_data in config_dict.get("entities", {}).items():
        entities[name] = EntityDefinition(**entity_data)
    
    # Parse route patterns
    route_patterns = []
    for pattern_data in config_dict.get("route_patterns", []):
        # Parse parameters
        parameters = {}
        for param_name, param_data in pattern_data.get("parameters", {}).items():
            param_type = ParameterType(param_data.get("type", "string"))
            parameters[param_name] = RouteParameter(
                type=param_type,
                description=param_data.get("description", ""),
                examples=param_data.get("examples", []),
                required=param_data.get("required", True)
            )
        
        route_pattern = RoutePattern(
            pattern=pattern_data["pattern"],
            name=pattern_data["name"],
            description=pattern_data["description"],
            intent_patterns=pattern_data.get("intent_patterns", []),
            parameters=parameters,
            examples=pattern_data.get("examples", [])
        )
        route_patterns.append(route_pattern)
    
    # Parse database schema
    tables = {}
    for table_name, table_data in config_dict.get("database_schema", {}).get("tables", {}).items():
        columns = []
        for col_data in table_data.get("columns", []):
            columns.append(ColumnSchema(**col_data))
        
        tables[table_name] = TableSchema(
            name=table_data["name"],
            columns=columns,
            description=table_data.get("description"),
            primary_key=table_data.get("primary_key", "id")
        )
    
    database_schema = DatabaseSchema(
        tables=tables,
        relationships=config_dict.get("database_schema", {}).get("relationships", {})
    )
    
    # Create final configuration
    return SiteConfiguration(
        domain=config_dict["domain"],
        base_url=config_dict["base_url"],
        entities=entities,
        route_patterns=route_patterns,
        database_schema=database_schema,
        semantic_mappings=config_dict.get("semantic_mappings", {}),
        default_actions=config_dict.get("default_actions", [])
    )


if __name__ == "__main__":
    asyncio.run(main()) 