"""
Test Fantastic Router with real database and LLM
This script connects to the PostgreSQL database and tests real queries
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add packages to path
sys.path.append(str(Path(__file__).parent.parent.parent / "packages" / "fantastic_router_core" / "src"))
sys.path.append(str(Path(__file__).parent.parent.parent / "adapters"))

from fantastic_router_core import FantasticRouter
from llm.openai import OpenAILLMClient
from db.postgres import PostgreSQLDatabaseClient
from examples.quickstart.example import parse_site_configuration
import json

def get_performance_indicator(duration_ms: float) -> str:
    """Get performance indicator based on query duration"""
    if duration_ms < 1000:
        return "🚀 [Excellent]"
    elif duration_ms < 3000:
        return "🏃 [Good]"
    elif duration_ms < 5000:
        return "🐌 [Needs optimization]"
    elif duration_ms < 10000:
        return "💩 [Slow]"
    else:
        return "💀 [RIP]"


async def test_real_system():
    """Test the system with real database and LLM"""
    
    print("🧪 Testing Fantastic Router with Real Systems")
    print("=" * 60)
    
    # 1. Setup clients
    print("1. Setting up clients...")
    
    # LLM Client
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "your-api-key-here":
        print("   ⚠️  No OpenAI API key found. Using mock responses.")
        llm_client = MockLLMClient()
    else:
        llm_client = OpenAILLMClient(api_key=openai_key)
        print("   ✅ OpenAI client configured")
    
    # Database Client
    db_url = os.getenv("DATABASE_URL", "postgresql://fantastic_user:fantastic_pass@localhost:5432/property_mgmt")
    db_client = PostgreSQLDatabaseClient(connection_string=db_url)
    
    # Test database connection
    if await db_client.test_connection():
        print("   ✅ Database connected successfully")
    else:
        print("   ❌ Database connection failed")
        print("   💡 Make sure to run: docker-compose up postgres")
        return
    
    # 2. Load configuration
    print("\n2. Loading configuration...")
    config_path = Path(__file__).parent / "routes.json"
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    config = parse_site_configuration(config_dict)
    print(f"   ✅ Configuration loaded for domain: {config.domain}")
    
    # 3. Create router
    print("\n3. Creating router...")
    router = FantasticRouter(
        llm_client=llm_client,
        db_client=db_client,
        config=config
    )
    print("   ✅ Router created")
    
    # 4. Test queries
    print("\n4. Testing queries against real data...")
    print("-" * 40)
    
    test_queries = [
        "show me James Smith's monthly income",
        "view John Doe's contact information", 
        "show Sarah Johnson's properties",
        "create new property",
        "list all tenants",
        "show Emily Davis lease information"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        
        # Start timing
        start_time = time.time()
        
        try:
            # Plan the action
            action_plan = await router.plan(query)
            
            # Calculate timing
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            print(f"   📍 Route: {action_plan.route}")
            print(f"   🎯 Action: {action_plan.action_type.value}")
            print(f"   📊 Confidence: {action_plan.confidence:.2f}")
            print(f"   ⏱️  Time: {duration_ms:.0f}ms")
            
            if action_plan.entities:
                print(f"   👥 Entities found:")
                for entity in action_plan.entities:
                    print(f"      - {entity.name} (ID: {entity.id}, Table: {entity.table})")
            
            if action_plan.parameters:
                print(f"   ⚙️  Parameters:")
                for param in action_plan.parameters:
                    print(f"      - {param.name}: {param.value} (from {param.source})")
            
            # Show reasoning for low confidence
            if action_plan.confidence < 0.7:
                print(f"   🤔 Reasoning: {action_plan.reasoning}")
            
            # Status with performance indicator
            status = "✅ Success" if action_plan.confidence > 0.5 else "⚠️  Low confidence"
            print(f"   {status}")

            perf_indicator = get_performance_indicator(duration_ms)
            print(f"   Performance: {perf_indicator}")
            
        except Exception as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            print(f"   ❌ Error: {e}")
            print(f"   ⏱️  Time: {duration_ms:.0f}ms (failed)")
            import traceback
            traceback.print_exc()
    
    # 5. Test database queries directly
    print(f"\n5. Testing direct database queries...")
    print("-" * 40)
    
    try:
        # Test entity search with timing
        start_time = time.time()
        results = await db_client.search(
            query="James Smith",
            tables=["users"],
            fields=["name", "email"],
            limit=5
        )
        duration_ms = (time.time() - start_time) * 1000
        print(f"   🔍 Search 'James Smith' in users: {len(results)} results ({duration_ms:.0f}ms)")
        for result in results:
            print(f"      - {result.get('name')} ({result.get('email')})")
        
        # Test landlord search with timing
        start_time = time.time()
        results = await db_client.search(
            query="Smith",
            tables=["landlords", "users"],
            fields=["name"],
            limit=5
        )
        duration_ms = (time.time() - start_time) * 1000
        print(f"   🔍 Search 'Smith' in landlords/users: {len(results)} results ({duration_ms:.0f}ms)")
        
    except Exception as e:
        print(f"   ❌ Database search error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Testing completed!")
    print("\n📊 Performance Guide:")
    print("🚀 < 1s: Excellent")
    print("🏃 1-3ms: Good")  
    print("🐌 3-5ms: Needs optimization")
    print("💩 5-10s: Slow")
    print("💀 > 10s: RIP")
    print("\n💡 Tips:")
    print("- Check the database has data: docker-compose exec postgres psql -U fantastic_user -d property_mgmt -c 'SELECT * FROM users;'")
    print("- View logs: docker-compose logs app")
    print(f"- Access pgAdmin: http://localhost:{os.getenv('PGADMIN_PORT', '8080')} (admin@pgadmin.com / admin)")


class MockLLMClient:
    """Mock LLM client for testing without API key"""
    
    async def analyze(self, prompt: str, temperature: float = 0.1):
        """Return mock responses based on prompt content"""
        
        if "intent" in prompt.lower() or "analyze this query" in prompt.lower():
            # Mock intent analysis
            if "james smith" in prompt.lower() and "income" in prompt.lower():
                return {
                    "action_type": "NAVIGATE",
                    "entities": ["James Smith"],
                    "view_type": "income",
                    "confidence": 0.9,
                    "reasoning": "User wants to view James Smith's income information",
                    "context_clues": ["income", "monthly", "James Smith"]
                }
            elif "create" in prompt.lower() and "property" in prompt.lower():
                return {
                    "action_type": "CREATE",
                    "entities": ["property"],
                    "view_type": None,
                    "confidence": 0.95,
                    "reasoning": "User wants to create a new property",
                    "context_clues": ["create", "new", "property"]
                }
            else:
                return {
                    "action_type": "NAVIGATE",
                    "entities": [],
                    "view_type": None,
                    "confidence": 0.6,
                    "reasoning": "Generic navigation request",
                    "context_clues": []
                }
        
        elif "entity_resolutions" in prompt.lower() or "resolve entities" in prompt.lower():
            # Mock entity resolution
            return {
                "entity_resolutions": [
                    {
                        "entity_name": "James Smith",
                        "inferred_type": "person",
                        "confidence": 0.9,
                        "recommended_tables": ["users", "landlords"],
                        "search_fields": ["name", "email"],
                        "join_strategy": "landlords.user_id = users.id",
                        "reasoning": "James Smith is likely a person, could be landlord based on income context",
                        "context_clues": ["income", "monthly"]
                    }
                ],
                "search_order": ["James Smith"],
                "estimated_confidence": 0.9
            }
        
        elif "route" in prompt.lower() or "pattern" in prompt.lower():
            # Mock route matching
            return {
                "matched_pattern": "/{entity_type}/{entity_id}/{view_type}",
                "resolved_route": "/landlords/james-smith-123/financials",
                "parameters": [
                    {
                        "name": "entity_type",
                        "value": "landlords",
                        "type": "string",
                        "source": "inferred"
                    },
                    {
                        "name": "entity_id", 
                        "value": "james-smith-123",
                        "type": "string",
                        "source": "entity"
                    },
                    {
                        "name": "view_type",
                        "value": "financials",
                        "type": "string",
                        "source": "inferred"
                    }
                ],
                "confidence": 0.85,
                "reasoning": "Matched entity detail view pattern for landlord financial information"
            }
        
        return {"error": "Mock LLM - unrecognized prompt type"}


if __name__ == "__main__":
    asyncio.run(test_real_system()) 