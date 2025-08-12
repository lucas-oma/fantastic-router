#!/usr/bin/env python3
"""
Test script to verify complex queries generate more alternatives
"""

import requests
import json
import time

def test_complex_queries():
    """Test complex queries that should have many alternatives"""
    
    # Complex queries that could have multiple interpretations
    test_queries = [
        "show me Michael's financial information",
        "edit landlord details",
        "create new property for tenant",
        "find properties with high rent",
        "display user dashboard"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("=" * 60)
        
        # Make API request
        response = requests.post(
            "http://localhost:8000/api/v1/plan",
            json={
                "query": query,
                "max_alternatives": 5
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success!")
            print(f"🛣️  Primary Route: {data['action_plan']['route']}")
            print(f"🎯 Primary Confidence: {data['action_plan']['confidence']}")
            print(f"📝 Primary Reasoning: {data['action_plan']['reasoning'][:100]}...")
            
            # Check alternatives
            alternatives = data.get('alternatives', [])
            print(f"\n🔄 Alternatives ({len(alternatives)} found):")
            
            if alternatives:
                for i, alt in enumerate(alternatives, 1):
                    print(f"  {i}. Route: {alt['route']}")
                    print(f"     Confidence: {alt['confidence']}")
                    print(f"     Reasoning: {alt['reasoning'][:80]}...")
                    print()
            else:
                print("  ❌ No alternatives generated")
            
            print(f"⏱️  Duration: {data['performance']['duration_ms']}ms")
            print(f"💾 Cache: {data['performance']['cache_type']} (hits: {data['performance']['cache_hits']})")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
        
        print("-" * 60)

if __name__ == "__main__":
    print("🧪 Testing Complex Queries for Multiple Alternatives")
    print("=" * 70)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    test_complex_queries() 