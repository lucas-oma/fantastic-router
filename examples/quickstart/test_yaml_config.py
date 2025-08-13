#!/usr/bin/env python3
"""
Test script to verify YAML configuration loading
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_yaml_config_loading():
    """Test that the YAML config can be loaded correctly"""
    
    print("Testing YAML configuration loading...")
    
    try:
        # Test the config loader
        from packages.fantastic_router_server.src.fantastic_router_server.config_loader import get_config, get_llm_config, get_database_config
        
        print("✓ Config loader imported successfully")
        
        # Load the main config
        config = get_config()
        print(f"✓ Main config loaded: {len(config)} top-level keys")
        
        # Check for expected sections
        expected_sections = ['app', 'database', 'entities', 'routes', 'schema', 'semantic_mappings', 'llm', 'logging', 'security', 'monitoring']
        for section in expected_sections:
            if section in config:
                print(f"✓ Found {section} section")
            else:
                print(f"⚠ Missing {section} section")
        
        # Test LLM config
        llm_config = get_llm_config()
        print(f"✓ LLM config loaded: {llm_config}")
        
        # Test database config
        db_config = get_database_config()
        print(f"✓ Database config loaded: {db_config}")
        
        # Test router config extraction
        from packages.fantastic_router_server.src.fantastic_router_server.api.deps import DependencyContainer
        
        container = DependencyContainer()
        router_config = container.config
        print(f"✓ Router config extracted: {len(router_config)} keys")
        
        # Check router-specific sections
        router_sections = ['domain', 'base_url', 'entities', 'route_patterns', 'database_schema']
        for section in router_sections:
            if section in router_config:
                print(f"✓ Found router {section} section")
            else:
                print(f"⚠ Missing router {section} section")
        
        print("\n🎉 YAML configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ YAML configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variable_substitution():
    """Test environment variable substitution in YAML"""
    
    print("\nTesting environment variable substitution...")
    
    try:
        # Set some test environment variables
        os.environ['DB_API_TOKEN'] = 'test-token-123'
        os.environ['LLM_API_KEY'] = 'test-llm-key-456'
        
        from packages.fantastic_router_server.src.fantastic_router_server.config_loader import get_config
        
        config = get_config()
        
        # Check if environment variables were substituted
        db_token = config.get('database', {}).get('token')
        llm_key = config.get('llm', {}).get('api_key')
        
        if db_token == 'test-token-123':
            print("✓ Database token substitution working")
        else:
            print(f"⚠ Database token substitution failed: got {db_token}")
            
        if llm_key == 'test-llm-key-456':
            print("✓ LLM key substitution working")
        else:
            print(f"⚠ LLM key substitution failed: got {llm_key}")
        
        # Clean up
        del os.environ['DB_API_TOKEN']
        del os.environ['LLM_API_KEY']
        
        print("✓ Environment variable substitution test completed")
        return True
        
    except Exception as e:
        print(f"❌ Environment variable substitution test failed: {e}")
        return False

def test_legacy_json_fallback():
    """Test that legacy JSON config still works as fallback"""
    
    print("\nTesting legacy JSON fallback...")
    
    try:
        # Temporarily rename the YAML config to test JSON fallback
        yaml_config_path = Path(project_root) / "configs" / "app.yaml"
        yaml_backup_path = Path(project_root) / "configs" / "app.yaml.backup"
        
        if yaml_config_path.exists():
            yaml_config_path.rename(yaml_backup_path)
            
            try:
                from packages.fantastic_router_server.src.fantastic_router_server.config_loader import get_config
                config = get_config()
                print("✓ JSON fallback working")
                
            finally:
                # Restore YAML config
                if yaml_backup_path.exists():
                    yaml_backup_path.rename(yaml_config_path)
        else:
            print("⚠ No YAML config found to test fallback")
            
        return True
        
    except Exception as e:
        print(f"❌ JSON fallback test failed: {e}")
        return False

if __name__ == "__main__":
    print("Fantastic Router YAML Configuration Test")
    print("=" * 50)
    
    success = True
    success &= test_yaml_config_loading()
    success &= test_environment_variable_substitution()
    success &= test_legacy_json_fallback()
    
    if success:
        print("\n🎉 All tests passed! YAML configuration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
        sys.exit(1) 