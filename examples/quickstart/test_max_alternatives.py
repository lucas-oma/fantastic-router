#!/usr/bin/env python3
"""
Test script to verify that max_alternatives parameter works correctly
"""

import requests
import json
import time
import os

def test_max_alternatives():
    """Test different max_alternatives values"""
    
    query = "find properties"
    
    # Get API key from environment
    api_key = os.getenv('FR_API_KEY')
    if not api_key:
        print("⚠️  No FR_API_KEY set. Set it with: export FR_API_KEY=your_api_key_here")
        print("   Or run: make generate-api-key to get a key")
        return
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    for max_alt in [1, 3, 5, 10]:
        print(f"\n🔍 Testing with max_alternatives={max_alt}")
        print("=" * 50)
        
        # Make API request
        response = requests.post(
            "http://localhost:8000/api/v1/plan",
            json={
                "query": query,
                "max_alternatives": max_alt
            },
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            alternatives = data.get('alternatives', [])
            print(f"✅ Success!")
            print(f"🛣️  Primary Route: {data['action_plan']['route']}")
            print(f"🎯 Primary Confidence: {data['action_plan']['confidence']}")
            print(f"🔄 Alternatives requested: {max_alt}, received: {len(alternatives)}")
            
            if alternatives:
                for i, alt in enumerate(alternatives, 1):
                    print(f"  {i}. Route: {alt['route']} (conf: {alt['confidence']})")
            
            print(f"⏱️  Duration: {data['performance']['duration_ms']}ms")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
        
        print("-" * 50)

if __name__ == "__main__":
    print("🧪 Testing max_alternatives Parameter")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    test_max_alternatives() 