"""
Test Fantastic Router with Gemini LLM
Demonstrates drop-in compatibility with different LLM providers
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
from llm.gemini import create_gemini_client
from llm.openai import create_openai_client
from db.postgres import PostgreSQLDatabaseClient
from examples.quickstart.example import parse_site_configuration
import json


async def test_gemini_vs_openai():
    """Compare Gemini and OpenAI performance side by side"""
    
    print("🧪 Testing Fantastic Router: Gemini vs OpenAI")
    print("=" * 60)
    
    # Setup database client (shared)
    db_url = os.getenv("DATABASE_URL", "postgresql://fantastic_user:fantastic_pass@localhost:5432/property_mgmt")
    db_client = PostgreSQLDatabaseClient(connection_string=db_url)
    
    if not await db_client.test_connection():
        print("   ❌ Database connection failed")
        return
    
    # Load configuration (shared)
    config_path = Path(__file__).parent / "routes.json"
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    config = parse_site_configuration(config_dict)
    
    # Setup LLM clients
    llm_clients = {}
    
    # Gemini client
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if gemini_key and gemini_key != "your-gemini-api-key-here":
        try:
            llm_clients["Gemini"] = create_gemini_client(
                api_key=gemini_key,
                model="gemini-1.5-flash"  # Fast model
            )
            print("   ✅ Gemini client configured")
        except ImportError as e:
            print(f"   ⚠️  Gemini not available: {e}")
    else:
        print("   ⚠️  No Gemini API key found (set GEMINI_API_KEY)")
    
    # OpenAI client
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your-openai-api-key-here":
        llm_clients["OpenAI"] = create_openai_client(
            api_key=openai_key,
            model="gpt-3.5-turbo-1106"  # Fast model
        )
        print("   ✅ OpenAI client configured")
    else:
        print("   ⚠️  No OpenAI API key found")
    
    if not llm_clients:
        print("   ❌ No LLM clients available. Please set API keys.")
        return
    
    # Test queries
    test_queries = [
        "show me James Smith's monthly income",
        "create new property",
        "list all tenants"
    ]
    
    # Test each LLM provider
    for provider, llm_client in llm_clients.items():
        print(f"\n🤖 Testing {provider}...")
        print("-" * 40)
        
        # Create router with this LLM
        router = FantasticRouter(
            llm_client=llm_client,
            db_client=db_client,
            config=config,
            use_fast_planner=True  # Use single-call optimization
        )
        
        # Test each query
        for i, query in enumerate(test_queries, 1):
            print(f"\n  🔍 Test {i}: '{query}'")
            
            start_time = time.time()
            try:
                action_plan = await router.plan(query)
                duration_ms = (time.time() - start_time) * 1000
                
                print(f"     📍 Route: {action_plan.route}")
                print(f"     🎯 Action: {action_plan.action_type.value}")
                print(f"     📊 Confidence: {action_plan.confidence:.2f}")
                print(f"     ⏱️  Time: {duration_ms:.0f}ms")
                
                # Performance indicator
                if duration_ms < 1000:
                    perf = "🚀 [Excellent]"
                elif duration_ms < 3000:
                    perf = "🏃 [Good]"
                elif duration_ms < 5000:
                    perf = "🐌 [Needs optimization]"
                elif duration_ms < 10000:
                    perf = "💩 [Slow]"
                else:
                    perf = "💀 [RIP]"
                
                status = "✅ Success" if action_plan.confidence > 0.5 else "⚠️  Low confidence"
                print(f"     {status} {perf}")
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                print(f"     ❌ Error: {str(e)[:100]}...")
                print(f"     ⏱️  Time: {duration_ms:.0f}ms (failed)")


async def test_single_provider():
    """Test with whatever provider is available"""
    
    print("🧪 Testing Fantastic Router with Available LLM")
    print("=" * 50)
    
    # Try to get any available LLM client
    llm_client = None
    provider_name = "None"
    
    # Try Gemini first (often faster and cheaper)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
    if gemini_key and gemini_key != "your-gemini-api-key-here":
        try:
            llm_client = create_gemini_client(api_key=gemini_key)
            provider_name = "Gemini"
            print("   ✅ Using Gemini LLM")
        except ImportError:
            print("   ⚠️  Gemini not available (pip install google-generativeai)")
    
    # Fallback to OpenAI
    if not llm_client:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your-openai-api-key-here":
            llm_client = create_openai_client(api_key=openai_key)
            provider_name = "OpenAI"
            print("   ✅ Using OpenAI LLM")
    
    if not llm_client:
        print("   ❌ No LLM provider available")
        print("   💡 Set GEMINI_API_KEY or OPENAI_API_KEY environment variable")
        return
    
    # Setup router (same as before)
    db_url = os.getenv("DATABASE_URL", "postgresql://fantastic_user:fantastic_pass@localhost:5432/property_mgmt")
    db_client = PostgreSQLDatabaseClient(connection_string=db_url)
    
    if not await db_client.test_connection():
        print("   ❌ Database connection failed")
        return
    
    config_path = Path(__file__).parent / "routes.json"
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    config = parse_site_configuration(config_dict)
    
    router = FantasticRouter(
        llm_client=llm_client,
        db_client=db_client,
        config=config,
        use_fast_planner=True
    )
    
    # Test a single query
    query = "show me James Smith's monthly income"
    print(f"\n🔍 Testing: '{query}'")
    print(f"🤖 Provider: {provider_name}")
    
    start_time = time.time()
    try:
        action_plan = await router.plan(query)
        duration_ms = (time.time() - start_time) * 1000
        
        print(f"\n✅ Results:")
        print(f"   📍 Route: {action_plan.route}")
        print(f"   🎯 Action: {action_plan.action_type.value}")
        print(f"   📊 Confidence: {action_plan.confidence:.2f}")
        print(f"   ⏱️  Time: {duration_ms:.0f}ms")
        print(f"   🤖 Provider: {provider_name}")
        
        if action_plan.entities:
            print(f"   👥 Entities: {[e.name for e in action_plan.entities]}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    # Choose which test to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        asyncio.run(test_gemini_vs_openai())
    else:
        asyncio.run(test_single_provider()) 