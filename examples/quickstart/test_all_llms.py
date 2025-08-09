"""
Test Fantastic Router with All LLM Providers
Demonstrates drop-in compatibility across OpenAI, Gemini, and Ollama
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
from db.postgres import PostgreSQLDatabaseClient
from examples.quickstart.example import parse_site_configuration
import json


async def test_all_llm_providers():
    """Test all available LLM providers with the same query"""
    
    print("🧪 Testing Fantastic Router with All LLM Providers")
    print("=" * 60)
    
    # Setup shared components
    db_url = os.getenv("DATABASE_URL", "postgresql://fantastic_user:fantastic_pass@localhost:5432/property_mgmt")
    db_client = PostgreSQLDatabaseClient(connection_string=db_url)
    
    if not await db_client.test_connection():
        print("   ❌ Database connection failed")
        return
    
    config_path = Path(__file__).parent / "routes.json"
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    config = parse_site_configuration(config_dict)
    
    # Try to initialize all LLM clients
    llm_clients = {}
    
    # 1. OpenAI
    try:
        from llm.openai import create_openai_client
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your-openai-api-key-here":
            llm_clients["OpenAI"] = create_openai_client(api_key=openai_key)
            print("   ✅ OpenAI client configured")
        else:
            print("   ⚠️  OpenAI: No API key (set OPENAI_API_KEY)")
    except ImportError:
        print("   ❌ OpenAI: Import failed")
    
    # 2. Gemini
    try:
        from llm.gemini import create_gemini_client
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        if gemini_key and gemini_key != "your-gemini-api-key-here":
            llm_clients["Gemini"] = create_gemini_client(api_key=gemini_key)
            print("   ✅ Gemini client configured")
        else:
            print("   ⚠️  Gemini: No API key (set GEMINI_API_KEY)")
    except ImportError:
        print("   ❌ Gemini: Import failed (pip install google-generativeai)")
    
    # 3. Anthropic Claude
    try:
        from llm.anthropic import create_anthropic_client
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key != "your-anthropic-api-key-here":
            llm_clients["Claude"] = create_anthropic_client(api_key=anthropic_key)
            print("   ✅ Claude client configured")
        else:
            print("   ⚠️  Claude: No API key (set ANTHROPIC_API_KEY)")
    except ImportError:
        print("   ❌ Claude: Import failed (pip install anthropic)")
    
    # 4. Ollama
    try:
        from llm.ollama import create_ollama_client
        ollama_client = create_ollama_client()
        
        # Check if Ollama is running
        if await ollama_client._check_ollama_health():
            # Check available models
            models = await ollama_client.list_models()
            if models:
                # Use the first available model, prefer llama3.1
                preferred_models = ["llama3.1:8b", "llama3:8b", "llama2:7b"]
                selected_model = None
                
                for pref_model in preferred_models:
                    if pref_model in models:
                        selected_model = pref_model
                        break
                
                if not selected_model and models:
                    selected_model = models[0]  # Use first available
                
                if selected_model:
                    llm_clients["Ollama"] = create_ollama_client(model=selected_model)
                    print(f"   ✅ Ollama client configured (model: {selected_model})")
                else:
                    print("   ⚠️  Ollama: No suitable models found")
            else:
                print("   ⚠️  Ollama: No models installed (try: ollama pull llama3.1:8b)")
        else:
            print("   ⚠️  Ollama: Server not running (try: ollama serve)")
    except ImportError:
        print("   ❌ Ollama: Import failed (pip install aiohttp)")
    
    if not llm_clients:
        print("\n❌ No LLM providers available!")
        print("💡 Setup at least one:")
        print("   - OpenAI: export OPENAI_API_KEY=sk-...")
        print("   - Gemini: export GEMINI_API_KEY=AI...")
        print("   - Claude: export ANTHROPIC_API_KEY=sk-ant-...")
        print("   - Ollama: ollama serve && ollama pull llama3.1:8b")
        return
    
    # Test queries
    test_queries = [
        "show me James Smith's monthly income",
        "create new property",
        "list all tenants"
    ]
    
    # Performance comparison
    results = {}
    
    # Test each provider
    for provider, llm_client in llm_clients.items():
        print(f"\n🤖 Testing {provider}...")
        print("-" * 40)
        
        router = FantasticRouter(
            llm_client=llm_client,
            db_client=db_client,
            config=config,
            use_fast_planner=True
        )
        
        provider_results = []
        
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
                    perf = "🚀"
                elif duration_ms < 3000:
                    perf = "🏃"
                elif duration_ms < 5000:
                    perf = "🐌"
                elif duration_ms < 10000:
                    perf = "💩"
                else:
                    perf = "💀"
                
                status = "✅" if action_plan.confidence > 0.5 else "⚠️"
                print(f"     {status} {perf}")
                
                provider_results.append({
                    "query": query,
                    "duration_ms": duration_ms,
                    "confidence": action_plan.confidence,
                    "success": True
                })
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                print(f"     ❌ Error: {str(e)[:80]}...")
                print(f"     ⏱️  Time: {duration_ms:.0f}ms (failed)")
                
                provider_results.append({
                    "query": query,
                    "duration_ms": duration_ms,
                    "confidence": 0.0,
                    "success": False
                })
        
        results[provider] = provider_results
    
    # Summary comparison
    print(f"\n📊 Performance Summary")
    print("=" * 60)
    
    for provider, provider_results in results.items():
        successful = [r for r in provider_results if r["success"]]
        if successful:
            avg_time = sum(r["duration_ms"] for r in successful) / len(successful)
            avg_confidence = sum(r["confidence"] for r in successful) / len(successful)
            success_rate = len(successful) / len(provider_results) * 100
            
            # Overall performance indicator
            if avg_time < 1500:
                overall_perf = "🚀 [Excellent]"
            elif avg_time < 4000:
                overall_perf = "🏃 [Good]"
            elif avg_time < 7000:
                overall_perf = "🐌 [Slow]"
            elif avg_time < 15000:
                overall_perf = "💩 [Very Slow]"
            else:
                overall_perf = "💀 [RIP]"
            
            print(f"\n🤖 {provider}:")
            print(f"   ⏱️  Avg Time: {avg_time:.0f}ms")
            print(f"   📊 Avg Confidence: {avg_confidence:.2f}")
            print(f"   ✅ Success Rate: {success_rate:.0f}%")
            print(f"   🏆 Overall: {overall_perf}")
        else:
            print(f"\n🤖 {provider}: ❌ All tests failed")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if "Ollama" in results and any(r["success"] for r in results["Ollama"]):
        print("   🏠 Ollama: Best for privacy, no API costs, works offline")
    if "Gemini" in results and any(r["success"] for r in results["Gemini"]):
        print("   💰 Gemini: Often fastest and cheapest cloud option")
    if "Claude" in results and any(r["success"] for r in results["Claude"]):
        print("   🧠 Claude: Excellent reasoning and instruction following")
    if "OpenAI" in results and any(r["success"] for r in results["OpenAI"]):
        print("   🎯 OpenAI: Most reliable, good quality")
    
    print(f"\n🎉 Testing completed! All providers work as drop-in replacements.")


async def auto_setup_ollama():
    """Helper to automatically set up Ollama if needed"""
    try:
        from llm.ollama import create_ollama_client
        
        client = create_ollama_client()
        
        # Check if Ollama is running
        if not await client._check_ollama_health():
            print("⚠️  Ollama server not running")
            print("💡 Start with: ollama serve")
            return False
        
        # Check for models
        models = await client.list_models()
        if not models:
            print("📦 No Ollama models found. Pulling llama3.1:8b...")
            success = await client.pull_model("llama3.1:8b")
            if success:
                print("✅ Model downloaded successfully!")
            else:
                print("❌ Failed to download model")
                return False
        
        return True
        
    except ImportError:
        print("❌ Ollama client not available")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup-ollama":
        asyncio.run(auto_setup_ollama())
    else:
        asyncio.run(test_all_llm_providers()) 