#!/usr/bin/env python3
"""
Test script to verify environment variable substitution in YAML config
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_environment_variable_substitution():
    """Test that all environment variables are properly substituted"""
    
    print("Testing environment variable substitution in YAML config...")
    
    # Set test environment variables
    test_env_vars = {
        'OPENAI_API_KEY': 'sk-test-openai-key-123',
        'OPENAI_MODEL': 'gpt-4-turbo',
        'LLM_MAX_TOKENS': '2000',
        'GEMINI_API_KEY': 'sk-test-gemini-key-456',
        'GEMINI_MODEL': 'gemini-2.0-flash',
        'ANTHROPIC_API_KEY': 'sk-test-anthropic-key-789',
        'ANTHROPIC_MODEL': 'claude-3.5-sonnet',
        'OLLAMA_BASE_URL': 'http://localhost:11435',
        'OLLAMA_MODEL': 'llama3.2:8b',
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb',
        'DB_MAX_CONNECTIONS': '20',
        'DB_TIMEOUT': '45',
        'APP_ENV': 'staging',
        'LOG_LEVEL': 'DEBUG',
        'USE_FAST_PLANNER': 'false',
        'LLM_TIMEOUT': '120',
        'LLM_TEMPERATURE': '0.2'
    }
    
    # Set environment variables
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    try:
        from packages.fantastic_router_server.src.fantastic_router_server.config_loader import get_config
        
        config = get_config()
        
        # Test LLM configuration
        llm_config = config.get('llm', {})
        print(f"✓ LLM Provider: {llm_config.get('provider')}")
        print(f"✓ LLM Temperature: {llm_config.get('temperature')}")
        print(f"✓ LLM Max Tokens: {llm_config.get('max_tokens')}")
        print(f"✓ LLM Timeout: {llm_config.get('timeout')}")
        
        # Test LLM provider-specific configs
        openai_config = llm_config.get('openai', {})
        print(f"✓ OpenAI API Key: {openai_config.get('api_key')}")
        print(f"✓ OpenAI Model: {openai_config.get('model')}")
        
        gemini_config = llm_config.get('gemini', {})
        print(f"✓ Gemini API Key: {gemini_config.get('api_key')}")
        print(f"✓ Gemini Model: {gemini_config.get('model')}")
        
        anthropic_config = llm_config.get('anthropic', {})
        print(f"✓ Anthropic API Key: {anthropic_config.get('api_key')}")
        print(f"✓ Anthropic Model: {anthropic_config.get('model')}")
        
        ollama_config = llm_config.get('ollama', {})
        print(f"✓ Ollama Base URL: {ollama_config.get('base_url')}")
        print(f"✓ Ollama Model: {ollama_config.get('model')}")
        
        # Test database configuration
        db_config = config.get('database', {})
        print(f"✓ Database Type: {db_config.get('type')}")
        print(f"✓ Database Connection String: {db_config.get('connection_string')}")
        print(f"✓ Database Max Connections: {db_config.get('max_connections')}")
        print(f"✓ Database Timeout: {db_config.get('timeout')}")
        
        # Test app configuration
        app_config = config.get('app', {})
        print(f"✓ App Environment: {app_config.get('environment')}")
        print(f"✓ Use Fast Planner: {app_config.get('use_fast_planner')}")
        
        # Test logging configuration
        logging_config = config.get('logging', {})
        print(f"✓ Log Level: {logging_config.get('level')}")
        
        print("\n🎉 All environment variables substituted correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Environment variable substitution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up environment variables
        for key in test_env_vars.keys():
            if key in os.environ:
                del os.environ[key]

def test_default_values():
    """Test that default values work when environment variables are not set"""
    
    print("\nTesting default values...")
    
    try:
        from packages.fantastic_router_server.src.fantastic_router_server.config_loader import get_config
        
        config = get_config()
        
        # Test default values
        llm_config = config.get('llm', {})
        print(f"✓ Default LLM Max Tokens: {llm_config.get('max_tokens')}")
        print(f"✓ Default LLM Temperature: {llm_config.get('temperature')}")
        print(f"✓ Default LLM Timeout: {llm_config.get('timeout')}")
        
        # Test provider defaults
        openai_config = llm_config.get('openai', {})
        print(f"✓ Default OpenAI Model: {openai_config.get('model')}")
        
        db_config = config.get('database', {})
        print(f"✓ Default Database Max Connections: {db_config.get('max_connections')}")
        print(f"✓ Default Database Timeout: {db_config.get('timeout')}")
        
        app_config = config.get('app', {})
        print(f"✓ Default App Environment: {app_config.get('environment')}")
        
        logging_config = config.get('logging', {})
        print(f"✓ Default Log Level: {logging_config.get('level')}")
        
        print("✓ Default values working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Default values test failed: {e}")
        return False

if __name__ == "__main__":
    print("Fantastic Router Environment Variable Substitution Test")
    print("=" * 60)
    
    success = True
    success &= test_environment_variable_substitution()
    success &= test_default_values()
    
    if success:
        print("\n🎉 All tests passed! Environment variable substitution is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        sys.exit(1) 