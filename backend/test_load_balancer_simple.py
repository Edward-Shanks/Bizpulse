"""
Simple test to verify Ollama load balancing is working

Run this script to see which endpoints are being selected:
    python test_load_balancer_simple.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.utils.llm_providers.ollama import get_ollama_endpoint, _initialize_ollama_endpoints

def main():
    print("="*80)
    print("OLLAMA LOAD BALANCER TEST")
    print("="*80)
    
    # Show configuration
    print("\n📋 Configuration:")
    print(f"   OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")
    print(f"   OLLAMA_ENDPOINTS: {settings.OLLAMA_ENDPOINTS}")
    print(f"   Number of endpoints: {len(settings.OLLAMA_ENDPOINTS)}")
    
    # Initialize
    _initialize_ollama_endpoints()
    
    # Test 20 requests
    print(f"\n🔄 Testing endpoint selection (20 requests):")
    print("-" * 80)
    
    selected = []
    for i in range(20):
        endpoint = get_ollama_endpoint()
        selected.append(endpoint)
        port = endpoint.split(':')[-1] if ':' in endpoint else 'unknown'
        print(f"Request {i+1:2d}: {endpoint} (port: {port})")
    
    # Count distribution
    from collections import Counter
    counts = Counter(selected)
    
    print("\n" + "="*80)
    print("📊 DISTRIBUTION RESULTS:")
    print("="*80)
    
    for endpoint, count in sorted(counts.items()):
        port = endpoint.split(':')[-1] if ':' in endpoint else 'unknown'
        percentage = (count / len(selected)) * 100
        print(f"   Port {port}: {count:2d} times ({percentage:5.1f}%) - {endpoint}")
    
    # Check if all expected endpoints are used
    expected_ports = {'11434', '11435', '11436', '11437'}
    used_ports = {ep.split(':')[-1] for ep in selected if ':' in ep}
    
    print("\n" + "="*80)
    print("✅ VERIFICATION:")
    print("="*80)
    
    if len(counts) == 4:
        print("✅ SUCCESS: All 4 endpoints are being used!")
    elif len(counts) == 1:
        print("❌ PROBLEM: Only 1 endpoint is being used!")
        print(f"   Only using: {list(counts.keys())[0]}")
        print("\n   Possible causes:")
        print("   1. OLLAMA_ENDPOINTS is not configured correctly")
        print("   2. Check config.py - OLLAMA_ENDPOINTS should have 4 URLs")
        print("   3. Check backend logs for initialization messages")
    else:
        print(f"⚠️  WARNING: Only {len(counts)} endpoints are being used (expected 4)")
        print(f"   Used: {sorted(used_ports)}")
        print(f"   Expected: {sorted(expected_ports)}")
    
    # Check fairness
    if len(counts) > 1:
        counts_list = list(counts.values())
        min_count = min(counts_list)
        max_count = max(counts_list)
        diff = max_count - min_count
        
        print(f"\n📈 Fairness:")
        print(f"   Min: {min_count}, Max: {max_count}, Difference: {diff}")
        if diff <= 1:
            print("   ✅ Distribution is fair")
        else:
            print(f"   ⚠️  Some imbalance (difference = {diff})")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()


