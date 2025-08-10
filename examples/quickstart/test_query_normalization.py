#!/usr/bin/env python3
"""
Test script to demonstrate query normalization
"""

import sys
import os

# Add the server package to path so we can import the normalization function
sys.path.append(os.path.join(os.path.dirname(__file__), '../../packages/fantastic_router_server/src'))

def test_normalization():
    """Test query normalization"""
    
    # Import the normalization function
    try:
        from fantastic_router_server.api.routes import _normalize_query
    except ImportError:
        print("❌ Could not import normalization function")
        print("Make sure the server is running: make up")
        return
    
    print("🧪 Testing Query Normalization")
    print("=" * 50)
    
    test_cases = [
        ("show me Michael's properties", "michael's properties"),
        ("michaels properties", "michael's properties"),
        ("get michael properties", "michael's properties"),
        ("find michael properties", "michael's properties"),
        ("michael properties", "michael's properties"),
        ("properties of michael", "properties of michael"),
        ("michael's property list", "michael's property list"),
        ("display michael properties", "michael's properties"),
        ("show me John's income", "john's income"),
        ("johns income", "john's income"),
        ("get john income", "john's income"),
        ("michael contact info", "michael's contact"),
        ("michaels contact information", "michael's contact"),
    ]
    
    print("📝 Testing normalization:")
    print("Original Query -> Normalized Query")
    print("-" * 50)
    
    for original, expected in test_cases:
        normalized = _normalize_query(original)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} '{original}' -> '{normalized}'")
        if normalized != expected:
            print(f"   Expected: '{expected}'")
    
    print("\n" + "="*50)
    print("🎯 Summary:")
    print("Normalization should make different queries more similar")
    print("This helps with pattern matching and caching!")

if __name__ == "__main__":
    test_normalization() 