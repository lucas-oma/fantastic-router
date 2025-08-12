#!/usr/bin/env python3
"""
Simple script to generate an API key for manual insertion into pgAdmin
"""

import uuid
import os
import time
import secrets

def generate_api_key():
    """Generate a new API key"""
    
    # Generate a random API key
    api_key = f"fr-{secrets.token_urlsafe(64)}"
    
    print(f"🔑 Generated API Key: {api_key}")
    print(f"")
    print(f"📝 To add this key to the system:")
    pgadmin_port = os.getenv('PGADMIN_PORT', '8080')
    pgadmin_email = os.getenv('PGADMIN_EMAIL', 'admin@pgadmin.com')
    pgadmin_password = os.getenv('PGADMIN_PASSWORD', 'admin')
    print(f"1. Open pgAdmin: http://localhost:{pgadmin_port}")
    print(f"2. Login: {pgadmin_email} / {pgadmin_password}")
    print(f"3. Connect to system database (localhost:5433)")
    print(f"4. Run this SQL:")
    print(f"")
    print(f"INSERT INTO api_keys (user_id, key_name, api_key, permissions, rate_limit_per_minute) VALUES (")
    print(f"  (SELECT id FROM users WHERE username = 'admin'),")
    print(f"  'Test API Key',")
    print(f"  '{api_key}',")
    print(f"  '{{\"read\": true, \"write\": true}}',")
    print(f"  100")
    print(f");")
    print(f"")
    print(f"💡 Usage example:")
    print(f"curl -X POST 'http://localhost:8000/api/v1/plan' \\")
    print(f"  -H 'Authorization: Bearer {api_key}' \\")
    print(f"  -H 'Content-Type: application/json' \\")
    print(f"  -d '{{\"query\": \"find properties\"}}'")
    
    return api_key

if __name__ == "__main__":
    generate_api_key() 