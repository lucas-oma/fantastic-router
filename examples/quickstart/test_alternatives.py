#!/usr/bin/env python3
"""
Test script to verify that the API returns multiple alternatives
"""

import requests
import json
import time
import os

def test_alternatives():
    """Test that the API returns multiple alternatives"""
    
    # Test queries that should have multiple interpretations
    test_queries = [
        "show me Michael's properties",
        "find properties",
        "create new property",
        "edit landlord details"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("=" * 50)
        
        # Get API key from environment
        api_key = os.getenv('FR_API_KEY')
        if not api_key:
            print("!! No FR_API_KEY set. Set it with: export FR_API_KEY=your_api_key_here")
            return
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Make API request
        response = requests.post(
            "http://localhost:8000/api/v1/plan",
            json={
                "query": query,
                "max_alternatives": 5  # Request up to 5 alternatives
            },
            headers=headers
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
        
        print("-" * 50)

if __name__ == "__main__":
    print("🧪 Testing Multiple Alternatives Feature")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    test_alternatives() 