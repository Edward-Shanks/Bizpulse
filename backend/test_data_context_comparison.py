"""
Test script to compare data context output between old and new implementations
"""
import requests
import json
import sys
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@thrivebrands.ai"
ADMIN_PASSWORD = "Thrive@123"

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[94m",      # Blue
        "SUCCESS": "\033[92m",   # Green
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",      # Red
        "RESET": "\033[0m"       # Reset
    }
    color = colors.get(status, colors["RESET"])
    print(f"{color}{message}{colors['RESET']}")

def test_login():
    """Login and get JWT token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")  # Support both formats
            if token:
                print_status(f"✅ Login successful", "SUCCESS")
                return token
            else:
                print_status(f"❌ No access token in response: {response.json()}", "ERROR")
                return None
        else:
            print_status(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        print_status(f"❌ Login error: {str(e)}", "ERROR")
        return None

def test_insights_chat(token: str, message: str, chart_title: str = None, context: Dict[str, Any] = None):
    """Test insights chat endpoint and return response"""
    try:
        payload = {
            "message": message,
            "chart_title": chart_title or "",
            "context": context or {},
            "session_id": "test_session",
            "conversation_history": []
        }
        
        response = requests.post(
            f"{BASE_URL}/insights/chat",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print_status(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        print_status(f"❌ Request error: {str(e)}", "ERROR")
        return None

def analyze_response(response_data: Dict[str, Any], test_name: str):
    """Analyze response data and print detailed information"""
    print_status(f"\n{'='*60}", "INFO")
    print_status(f"Analysis: {test_name}", "INFO")
    print_status(f"{'='*60}", "INFO")
    
    if not response_data:
        print_status("❌ No response data", "ERROR")
        return
    
    # Response text
    response_text = response_data.get('response', '')
    print_status(f"\n📝 Response Length: {len(response_text)} characters", "INFO")
    print_status(f"📝 Response Preview (first 300 chars):", "INFO")
    print_status(f"   {response_text[:300]}...", "INFO")
    
    # Data context
    context = response_data.get('context', '')
    print_status(f"\n📊 Data Context Length: {len(context)} characters", "INFO")
    print_status(f"📊 Data Context Preview (first 500 chars):", "INFO")
    print_status(f"   {context[:500]}...", "INFO")
    
    # Pivot table
    pivot_table = response_data.get('data', {}).get('pivot_table', [])
    print_status(f"\n📈 Pivot Table Items: {len(pivot_table)}", "INFO")
    if pivot_table:
        print_status(f"📈 First 3 items:", "INFO")
        for i, item in enumerate(pivot_table[:3]):
            print_status(f"   {i+1}. {item}", "INFO")
    
    # Follow-up questions
    follow_up = response_data.get('data', {}).get('follow_up_questions', [])
    print_status(f"\n💡 Follow-up Questions: {len(follow_up)}", "INFO")
    if follow_up:
        for i, q in enumerate(follow_up[:3]):
            print_status(f"   {i+1}. {q}", "INFO")
    
    # Check for comprehensive analysis indicators
    response_lower = response_text.lower()
    has_recommendations = any(word in response_lower for word in ['recommendation', 'suggest', 'should', 'consider', 'action'])
    has_insights = any(word in response_lower for word in ['insight', 'pattern', 'trend', 'analysis', 'indicates'])
    has_numbers = any(char.isdigit() for char in response_text)
    
    print_status(f"\n✅ Analysis Quality Indicators:", "INFO")
    print_status(f"   Has Recommendations: {has_recommendations}", "SUCCESS" if has_recommendations else "WARNING")
    print_status(f"   Has Insights: {has_insights}", "SUCCESS" if has_insights else "WARNING")
    print_status(f"   Has Numbers: {has_numbers}", "SUCCESS" if has_numbers else "WARNING")
    
    # Check for specific issues
    if "no data" in response_lower or "no sales" in response_lower:
        print_status(f"   ⚠️  Mentions 'no data' - might indicate query issue", "WARNING")
    
    if len(response_text) < 200:
        print_status(f"   ⚠️  Response is very short (< 200 chars) - might be incomplete", "WARNING")
    
    if len(pivot_table) == 0 and "brand" in test_name.lower():
        print_status(f"   ⚠️  No pivot table data for brand query - might indicate issue", "WARNING")

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    print_status("\n" + "="*60, "INFO")
    print_status("Data Context Comparison Test", "INFO")
    print_status("="*60, "INFO")
    
    # Login
    token = test_login()
    if not token:
        print_status("❌ Cannot proceed without authentication", "ERROR")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Top 15 Brands by Revenue",
            "message": "tell me Top 15 Brands by Revenue",
            "chart_title": "Top 15 Brands by Revenue",
            "context": {}
        },
        {
            "name": "Top 15 Brands by Revenue (with year)",
            "message": "tell me Top 15 Brands by Revenue for 2024",
            "chart_title": "Top 15 Brands by Revenue",
            "context": {}
        },
        {
            "name": "Top 15 Brands by Revenue (with month)",
            "message": "tell me Top 15 Brands by Revenue for January 2024",
            "chart_title": "Top 15 Brands by Revenue",
            "context": {}
        },
        {
            "name": "Top Sub-Categories by Revenue",
            "message": "tell me Top Sub-Categories by Revenue for March 2024",
            "chart_title": "Top Sub-Categories by Revenue",
            "context": {}
        },
        {
            "name": "Brand Performance Analysis",
            "message": "Show me brand performance trends",
            "chart_title": "Brand Performance",
            "context": {}
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print_status(f"\n{'='*60}", "INFO")
        print_status(f"Test {i}/{len(test_cases)}: {test_case['name']}", "INFO")
        print_status(f"{'='*60}", "INFO")
        
        start_time = time.time()
        response = test_insights_chat(
            token,
            test_case['message'],
            test_case['chart_title'],
            test_case['context']
        )
        end_time = time.time()
        
        if response:
            print_status(f"✅ Response received in {end_time - start_time:.2f} seconds", "SUCCESS")
            analyze_response(response, test_case['name'])
            results.append({
                "test": test_case['name'],
                "success": True,
                "response_time": end_time - start_time,
                "response_length": len(response.get('response', '')),
                "pivot_table_count": len(response.get('data', {}).get('pivot_table', []))
            })
        else:
            print_status(f"❌ Test failed", "ERROR")
            results.append({
                "test": test_case['name'],
                "success": False
            })
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print_status("\n" + "="*60, "INFO")
    print_status("Test Summary", "INFO")
    print_status("="*60, "INFO")
    
    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print_status(f"\n✅ Successful: {successful}/{total}", "SUCCESS" if successful == total else "WARNING")
    
    if successful > 0:
        avg_time = sum(r.get('response_time', 0) for r in results if r.get('success')) / successful
        print_status(f"⏱️  Average Response Time: {avg_time:.2f} seconds", "INFO")
        
        avg_length = sum(r.get('response_length', 0) for r in results if r.get('success')) / successful
        print_status(f"📝 Average Response Length: {avg_length:.0f} characters", "INFO")
        
        avg_pivot = sum(r.get('pivot_table_count', 0) for r in results if r.get('success')) / successful
        print_status(f"📈 Average Pivot Table Items: {avg_pivot:.1f}", "INFO")
    
    print_status("\n✅ All tests completed!", "SUCCESS")

if __name__ == "__main__":
    main()

