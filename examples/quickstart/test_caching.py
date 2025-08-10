#!/usr/bin/env python3
"""
Test script to demonstrate the dual caching system:
1. Request-level caching (exact matches)
2. Structural caching (pattern-based matches)
"""

import subprocess
import json
import time
import sys

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

def get_cache_stats():
    """Get cache statistics using curl"""
    url = f"{BASE_URL}/api/v1/cache/stats"
    
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "GET", url
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"❌ Curl error: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def test_caching():
    """Test both types of caching"""
    
    print("🧪 Testing Dual Caching System")
    print("=" * 50)
    
    # Test 1: Request-level caching (exact matches)
    print("\n1️⃣ Testing Request-Level Caching")
    print("-" * 30)
    
    # First request - should hit LLM
    print("📤 First request: 'show me Michael's properties'")
    start_time = time.time()
    response1 = make_request("show me Michael's properties")
    duration1 = (time.time() - start_time) * 1000
    
    if not response1:
        print("❌ Failed to get response")
        return
    
    print(f"⏱️  Duration: {duration1:.2f}ms")
    print(f"🎯 Cache type: {response1.get('performance', {}).get('cache_type', 'unknown')}")
    print(f"💾 Cache hits: {response1.get('performance', {}).get('cache_hits', 0)}")
    
    # Second request - should hit request cache
    print("\n📤 Second request: 'show me Michael's properties' (exact same)")
    start_time = time.time()
    response2 = make_request("show me Michael's properties")
    duration2 = (time.time() - start_time) * 1000
    
    if not response2:
        print("❌ Failed to get response")
        return
    
    print(f"⏱️  Duration: {duration2:.2f}ms")
    print(f"🎯 Cache type: {response2.get('performance', {}).get('cache_type', 'unknown')}")
    print(f"💾 Cache hits: {response2.get('performance', {}).get('cache_hits', 0)}")
    
    # Test 2: Structural caching (pattern matches)
    print("\n\n2️⃣ Testing Structural Caching")
    print("-" * 30)
    
    # First request for a new person - should hit LLM
    print("📤 First request: 'show me Sarah's properties'")
    start_time = time.time()
    response3 = make_request("show me Sarah's properties")
    duration3 = (time.time() - start_time) * 1000
    
    if not response3:
        print("❌ Failed to get response")
        return
    
    print(f"⏱️  Duration: {duration3:.2f}ms")
    print(f"🎯 Cache type: {response3.get('performance', {}).get('cache_type', 'unknown')}")
    print(f"💾 Cache hits: {response3.get('performance', {}).get('cache_hits', 0)}")
    
    # Second request for another person - should hit structural cache
    print("\n📤 Second request: 'show me John's properties' (different person, same pattern)")
    start_time = time.time()
    response4 = make_request("show me John's properties")
    duration4 = (time.time() - start_time) * 1000
    
    if not response4:
        print("❌ Failed to get response")
        return
    
    print(f"⏱️  Duration: {duration4:.2f}ms")
    print(f"🎯 Cache type: {response4.get('performance', {}).get('cache_type', 'unknown')}")
    print(f"💾 Cache hits: {response4.get('performance', {}).get('cache_hits', 0)}")
    
    # Test 3: Check cache statistics
    print("\n\n3️⃣ Cache Statistics")
    print("-" * 30)
    
    stats = get_cache_stats()
    if stats:
        print(f"📊 Request cache entries: {stats.get('request_cache', {}).get('total_entries', 0)}")
        print(f"📊 Structural cache entries: {stats.get('structural_cache', {}).get('total_entries', 0)}")
        print(f"📊 Cache patterns: {len(stats.get('cache_patterns', []))}")
    else:
        print("❌ Failed to get cache stats")
    
    # Test 4: Performance comparison
    print("\n\n4️⃣ Performance Comparison")
    print("-" * 30)
    
    print(f"🔄 LLM Call (first request): {duration1:.2f}ms")
    print(f"⚡ Request Cache (exact match): {duration2:.2f}ms")
    print(f"🔄 LLM Call (new pattern): {duration3:.2f}ms")
    print(f"⚡ Structural Cache (pattern match): {duration4:.2f}ms")
    
    if duration2 < duration1:
        speedup1 = duration1 / duration2
        print(f"🚀 Request cache speedup: {speedup1:.1f}x faster")
    
    if duration4 < duration3:
        speedup2 = duration3 / duration4
        print(f"🚀 Structural cache speedup: {speedup2:.1f}x faster")

if __name__ == "__main__":
    print("🚀 Starting caching test...")
    print("Make sure the server is running: make up")
    print()
    
    try:
        test_caching()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the server is running with: make up") 