#!/usr/bin/env python3
"""
Test script to verify system database setup
"""

import psycopg2
import os
import json

def test_system_database():
    """Test system database connection and basic operations"""
    
    # System database connection
    system_db_url = os.getenv('SYSTEM_DATABASE_URL', 'postgresql://system_user:system_pass@localhost:5433/fantastic_router_system')
    
    try:
        print("🔍 Testing System Database Connection...")
        conn = psycopg2.connect(system_db_url)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version[0]}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"📋 Available tables: {[table[0] for table in tables]}")
        
        # Check users table
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"👥 Users in system: {user_count}")
        
        # Check API keys table
        cursor.execute("SELECT COUNT(*) FROM api_keys;")
        api_key_count = cursor.fetchone()[0]
        print(f"🔑 API keys in system: {api_key_count}")
        
        # Check LLM providers
        cursor.execute("SELECT provider_name, model_name, is_default FROM llm_providers;")
        providers = cursor.fetchall()
        print(f"🤖 LLM Providers:")
        for provider in providers:
            default_mark = " (default)" if provider[2] else ""
            print(f"  - {provider[0]}: {provider[1]}{default_mark}")
        
        # Check domain configs
        cursor.execute("SELECT domain_name FROM domain_configs;")
        domains = cursor.fetchall()
        print(f"🌐 Domain Configurations: {[domain[0] for domain in domains]}")
        
        # Show example of how API key management would work
        print(f"\n🔧 Example API Key Management:")
        print(f"  1. Create API key for user")
        print(f"  2. Store hashed key in api_keys table")
        print(f"  3. Validate key on each request")
        print(f"  4. Track usage in request_logs table")
        print(f"  5. Apply rate limiting based on rate_limits table")
        
        cursor.close()
        conn.close()
        print(f"\n✅ System database test completed successfully!")
        
    except Exception as e:
        print(f"❌ System database test failed: {e}")
        print(f"   Make sure the system database is running on port 5433")

if __name__ == "__main__":
    print("🧪 Testing System Database Setup")
    print("=" * 50)
    test_system_database() 