#!/usr/bin/env python3
"""
Debug script to understand LLM client creation
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_llm_creation():
    """Debug LLM client creation process"""
    
    print("🔍 Debugging LLM Client Creation")
    print("=" * 40)
    
    try:
        # Test config loading
        from packages.fantastic_router_server.src.fantastic_router_server.config_loader import get_llm_config
        llm_config = get_llm_config()
        print(f"✅ LLM Config loaded: {len(llm_config)} keys")
        
        # Check provider
        provider = llm_config.get('provider')
        print(f"📋 Provider: {provider}")
        
        # Check OpenAI config
        openai_config = llm_config.get('openai', {})
        api_key = openai_config.get('api_key')
        model = openai_config.get('model')
        print(f"🔑 OpenAI API Key: {api_key[:10] if api_key else 'None'}...")
        print(f"🤖 OpenAI Model: {model}")
        
        # Check if API key is valid
        if api_key and api_key != "your-openai-api-key-here":
            print("✅ API key validation passed")
        else:
            print("❌ API key validation failed")
            return
        
        # Test adapter import
        try:
            import sys
            sys.path.append("/app/adapters")
            from llm.openai import create_openai_client
            print("✅ OpenAI adapter import successful")
        except ImportError as e:
            print(f"❌ OpenAI adapter import failed: {e}")
            return
        
        # Test client creation
        try:
            temperature = float(llm_config.get('temperature', 0.1))
            max_tokens = int(llm_config.get('max_tokens', 1000))
            
            client = create_openai_client(
                api_key=api_key,
                model=model,
                max_tokens=max_tokens
            )
            print(f"✅ OpenAI client created: {type(client).__name__}")
            
            # Test a simple analysis
            import asyncio
            async def test_analysis():
                try:
                    result = await client.analyze("show me properties", temperature=0.1)
                    print(f"✅ Analysis test successful")
                    print(f"   Full result: {result}")
                    print(f"   Action type: {result.get('action_type')}")
                    print(f"   Route: {result.get('route')}")
                    print(f"   Confidence: {result.get('confidence')}")
                except Exception as e:
                    print(f"❌ Analysis test failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            asyncio.run(test_analysis())
            
        except Exception as e:
            print(f"❌ OpenAI client creation failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm_creation() 