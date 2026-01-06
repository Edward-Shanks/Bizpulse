"""
Test script to verify Ollama load balancing across multiple endpoints

This script sends multiple concurrent requests and tracks which endpoint
is used for each request to verify round-robin distribution.

Usage:
    python test_ollama_load_balancing.py
"""
import asyncio
import httpx
import json
import time
from collections import Counter
from typing import List, Dict
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.utils.llm_providers.ollama import get_ollama_endpoint, _initialize_ollama_endpoints

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_ENDPOINT = f"{API_BASE_URL}/api/insights/chat"
NUM_REQUESTS = 20  # Send 20 requests to see distribution
CONCURRENT_REQUESTS = 4  # Send 4 at a time

# Track which endpoints are used
endpoint_usage = []
request_times = []


async def send_test_request(request_id: int, token: str = None) -> Dict:
    """
    Send a test request to the chat endpoint and track timing
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {
        "message": f"Test request {request_id} - What is the revenue for 2024?",
        "session_id": f"test-session-{request_id}",
        "conversation_history": []
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                TEST_ENDPOINT,
                json=payload,
                headers=headers
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "request_id": request_id,
                    "status": "success",
                    "elapsed": elapsed,
                    "response_length": len(data.get("response", "")),
                    "status_code": response.status_code
                }
            else:
                return {
                    "request_id": request_id,
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text[:200],
                    "elapsed": elapsed
                }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "request_id": request_id,
            "status": "exception",
            "error": str(e),
            "elapsed": elapsed
        }


def test_endpoint_selection():
    """
    Test the get_ollama_endpoint() function directly
    """
    print("\n" + "="*80)
    print("TEST 1: Direct Endpoint Selection Test")
    print("="*80)
    
    # Initialize endpoints
    _initialize_ollama_endpoints()
    
    # Get endpoints from config
    print(f"\n📋 Configuration:")
    print(f"   OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")
    print(f"   OLLAMA_ENDPOINTS: {settings.OLLAMA_ENDPOINTS}")
    print(f"   Number of endpoints: {len(settings.OLLAMA_ENDPOINTS) if settings.OLLAMA_ENDPOINTS else 0}")
    
    # Test round-robin selection
    print(f"\n🔄 Testing round-robin selection ({NUM_REQUESTS} requests):")
    selected_endpoints = []
    
    for i in range(NUM_REQUESTS):
        endpoint = get_ollama_endpoint()
        selected_endpoints.append(endpoint)
        print(f"   Request {i+1:2d}: {endpoint}")
    
    # Analyze distribution
    endpoint_counts = Counter(selected_endpoints)
    
    print(f"\n📊 Distribution Analysis:")
    for endpoint, count in endpoint_counts.items():
        percentage = (count / NUM_REQUESTS) * 100
        print(f"   {endpoint}: {count} times ({percentage:.1f}%)")
    
    # Check if all endpoints are used
    expected_endpoints = set(settings.OLLAMA_ENDPOINTS) if settings.OLLAMA_ENDPOINTS else {settings.OLLAMA_BASE_URL}
    used_endpoints = set(selected_endpoints)
    
    print(f"\n✅ Expected endpoints: {sorted(expected_endpoints)}")
    print(f"✅ Used endpoints: {sorted(used_endpoints)}")
    
    if expected_endpoints == used_endpoints:
        print("✅ SUCCESS: All endpoints are being used!")
    else:
        missing = expected_endpoints - used_endpoints
        if missing:
            print(f"❌ WARNING: Some endpoints were NOT used: {missing}")
        extra = used_endpoints - expected_endpoints
        if extra:
            print(f"❌ WARNING: Unexpected endpoints used: {extra}")
    
    # Check distribution fairness
    if len(endpoint_counts) > 1:
        counts = list(endpoint_counts.values())
        min_count = min(counts)
        max_count = max(counts)
        diff = max_count - min_count
        
        print(f"\n📈 Fairness Check:")
        print(f"   Min requests per endpoint: {min_count}")
        print(f"   Max requests per endpoint: {max_count}")
        print(f"   Difference: {diff}")
        
        if diff <= 1:
            print("✅ Distribution is FAIR (difference <= 1)")
        else:
            print(f"⚠️  Distribution has some imbalance (difference = {diff})")
    
    return selected_endpoints


async def test_api_requests():
    """
    Test actual API requests and monitor which endpoints are used via logs
    Note: This requires checking backend logs to see which endpoint is used
    """
    print("\n" + "="*80)
    print("TEST 2: API Request Test (Check Backend Logs for Endpoint Usage)")
    print("="*80)
    
    print(f"\n📡 Sending {NUM_REQUESTS} concurrent requests to {TEST_ENDPOINT}")
    print(f"   Concurrent batch size: {CONCURRENT_REQUESTS}")
    print(f"   ⚠️  Note: Check backend logs to see which endpoints are used")
    print(f"   Look for log lines: '🧠 Ollama request sent to ...'")
    
    # Create batches of concurrent requests
    tasks = []
    for i in range(0, NUM_REQUESTS, CONCURRENT_REQUESTS):
        batch = []
        for j in range(CONCURRENT_REQUESTS):
            if i + j < NUM_REQUESTS:
                batch.append(send_test_request(i + j + 1))
        tasks.extend(batch)
        
        # Wait a bit between batches to see distribution
        if i + CONCURRENT_REQUESTS < NUM_REQUESTS:
            await asyncio.sleep(0.5)
    
    # Execute all requests
    print(f"\n🚀 Executing {len(tasks)} requests...")
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    # Analyze results
    successful = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    failed = len(results) - successful
    
    print(f"\n📊 Results:")
    print(f"   Total requests: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per request: {total_time/len(results):.2f}s")
    
    if successful > 0:
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        avg_response_time = sum(r["elapsed"] for r in successful_results) / len(successful_results)
        print(f"   Average response time: {avg_response_time:.2f}s")
    
    # Show errors if any
    errors = [r for r in results if isinstance(r, dict) and r.get("status") != "success"]
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   Request {error.get('request_id')}: {error.get('error', 'Unknown error')}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Check backend logs for '🧠 Ollama request sent to ...' messages")
    print(f"   2. Verify that all 4 endpoints (11434-11437) are being used")
    print(f"   3. If only one endpoint is used, check OLLAMA_ENDPOINTS configuration")


def test_endpoint_health():
    """
    Test if all endpoints are accessible
    """
    print("\n" + "="*80)
    print("TEST 3: Endpoint Health Check")
    print("="*80)
    
    endpoints_to_check = settings.OLLAMA_ENDPOINTS if settings.OLLAMA_ENDPOINTS else [settings.OLLAMA_BASE_URL]
    
    async def check_endpoint(endpoint: str):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{endpoint}/api/tags")
                return {
                    "endpoint": endpoint,
                    "status": "✅ ONLINE" if response.status_code == 200 else f"❌ HTTP {response.status_code}",
                    "accessible": response.status_code == 200
                }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status": f"❌ ERROR: {str(e)[:50]}",
                "accessible": False
            }
    
    async def check_all():
        tasks = [check_endpoint(ep.strip()) for ep in endpoints_to_check if ep.strip()]
        results = await asyncio.gather(*tasks)
        return results
    
    print(f"\n🔍 Checking {len(endpoints_to_check)} endpoints...")
    results = asyncio.run(check_all())
    
    print(f"\n📊 Health Status:")
    for result in results:
        print(f"   {result['endpoint']}: {result['status']}")
    
    accessible = sum(1 for r in results if r["accessible"])
    print(f"\n✅ {accessible}/{len(results)} endpoints are accessible")
    
    if accessible < len(results):
        print(f"⚠️  Some endpoints are not accessible. Load balancing may not work correctly.")
        print(f"   Make sure all Ollama instances are running on Mac Studio.")


async def main():
    """
    Run all tests
    """
    print("\n" + "="*80)
    print("OLLAMA LOAD BALANCING TEST SUITE")
    print("="*80)
    print("\nThis script tests the round-robin load balancing across multiple Ollama endpoints.")
    print("It verifies that requests are distributed evenly across all configured endpoints.\n")
    
    # Test 1: Direct endpoint selection
    test_endpoint_selection()
    
    # Test 2: Endpoint health check
    test_endpoint_health()
    
    # Test 3: API requests (requires backend to be running)
    print(f"\n" + "="*80)
    response = input(f"\n❓ Run API request test? (Requires backend running on {API_BASE_URL}) [y/N]: ")
    if response.lower() == 'y':
        try:
            await test_api_requests()
        except Exception as e:
            print(f"\n❌ API test failed: {e}")
            print(f"   Make sure backend is running on {API_BASE_URL}")
    else:
        print("⏭️  Skipping API request test")
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\n💡 Summary:")
    print("   - Test 1 verifies round-robin selection logic")
    print("   - Test 2 checks if all endpoints are accessible")
    print("   - Test 3 sends actual API requests (check backend logs)")
    print("\n   If only one endpoint is used, check:")
    print("   1. OLLAMA_ENDPOINTS configuration in config.py")
    print("   2. Backend logs for initialization messages")
    print("   3. That use_multiple_endpoints is True in OllamaProvider\n")


if __name__ == "__main__":
    asyncio.run(main())


