#!/usr/bin/env python3
"""
Test script to demonstrate natural query variations:
- "show me Michael's properties"
- "michaels properties" 
- "get michael properties"
- etc.
"""

import subprocess
import json
import time

BASE_URL = "http://localhost:8000"

def make_request(query):
    """Make a request to the planning endpoint using curl"""
    url = f"{BASE_URL}/api/v1/plan"
    payload = json.dumps({
        "query": query,
        "user_role": "admin"
    })
    
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST", url,
            "-H", "Content-Type: application/json",
            "-d", payload
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"❌ Curl error: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def test_natural_queries():
    """Test various natural query variations"""
    
    print("🧪 Testing Natural Query Variations")
    print("=" * 50)
    
    # Test different ways to ask for the same thing
    queries = [
        "show me Michael's properties",
        "michaels properties",
        "get michael properties", 
        "find michael properties",
        "michael properties",
        "properties of michael",
        "michael's property list",
        "display michael properties"
    ]
    
    print("📝 Testing these query variations:")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. '{query}'")
    
    print("\n" + "="*50)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ Testing: '{query}'")
        print("-" * 30)
        
        start_time = time.time()
        response = make_request(query)
        duration = (time.time() - start_time) * 1000
        
        if response and response.get('success'):
            action_plan = response.get('action_plan', {})
            route = action_plan.get('route', 'N/A')
            confidence = action_plan.get('confidence', 0)
            cache_type = response.get('performance', {}).get('cache_type', 'unknown')
            cache_hits = response.get('performance', {}).get('cache_hits', 0)
            
            print(f"✅ Success!")
            print(f"🛣️  Route: {route}")
            print(f"🎯 Confidence: {confidence:.2f}")
            print(f"⏱️  Duration: {duration:.2f}ms")
            print(f"💾 Cache: {cache_type} (hits: {cache_hits})")
        else:
            print(f"❌ Failed: {response}")
    
    print("\n" + "="*50)
    print("🎯 Summary:")
    print("All these variations should ideally route to the same destination!")
    print("The system should understand that they all mean the same thing.")

if __name__ == "__main__":
    print("🚀 Starting natural query test...")
    print("Make sure the server is running: make up")
    print()
    
    try:
        test_natural_queries()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the server is running with: make up") 