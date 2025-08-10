#!/usr/bin/env python3
"""
Test script to verify route validation is working correctly
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

def test_route_validation():
    """Test that routes are properly validated"""
    
    print("🧪 Testing Route Validation")
    print("=" * 50)
    
    # Test queries that should generate valid routes
    test_cases = [
        {
            "query": "show me Michael's properties",
            "expected_pattern": "/landlords/",
            "description": "Should route to landlord properties"
        },
        {
            "query": "michael properties",
            "expected_pattern": "/landlords/",
            "description": "Should route to landlord properties (normalized)"
        },
        {
            "query": "find properties",
            "expected_pattern": "/properties/search",
            "description": "Should route to properties search"
        },
        {
            "query": "create new property",
            "expected_pattern": "/properties/create",
            "description": "Should route to property creation"
        },
        {
            "query": "list all tenants",
            "expected_pattern": "/tenants",
            "description": "Should route to tenant list"
        },
        {
            "query": "edit landlord information",
            "expected_pattern": "/landlords/",
            "description": "Should route to landlord edit"
        }
    ]
    
    print("📝 Testing route validation:")
    print("Query -> Generated Route -> Valid?")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Testing: '{test_case['query']}'")
        print(f"   Expected: {test_case['expected_pattern']}")
        print(f"   Description: {test_case['description']}")
        
        start_time = time.time()
        response = make_request(test_case['query'])
        duration = (time.time() - start_time) * 1000
        
        if response and response.get('success'):
            action_plan = response.get('action_plan', {})
            route = action_plan.get('route', 'N/A')
            confidence = action_plan.get('confidence', 0)
            cache_type = response.get('performance', {}).get('cache_type', 'unknown')
            
            # Check if route is valid
            is_valid = route.startswith(test_case['expected_pattern'])
            status = "✅" if is_valid else "❌"
            
            print(f"   {status} Route: {route}")
            print(f"   🎯 Confidence: {confidence:.2f}")
            print(f"   ⏱️  Duration: {duration:.2f}ms")
            print(f"   💾 Cache: {cache_type}")
            
            if not is_valid:
                print(f"   ⚠️  WARNING: Route doesn't match expected pattern!")
        else:
            print(f"   ❌ Failed: {response}")
    
    print("\n" + "="*50)
    print("🎯 Summary:")
    print("All routes should be valid and match expected patterns!")
    print("Invalid routes should be automatically fixed or use fallbacks.")

if __name__ == "__main__":
    print("🚀 Starting route validation test...")
    print("Make sure the server is running: make up")
    print()
    
    try:
        test_route_validation()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the server is running with: make up") 