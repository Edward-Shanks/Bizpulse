"""
Test script for Customer Deep Intelligence APIs
Run this script to test all Customer Insights API endpoints
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with your actual token

# Headers
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def print_response(title: str, response: requests.Response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")
    print(f"{'='*60}\n")

def test_get_filters():
    """Test GET /analytics/customer-insights/filters"""
    print("Testing: Get Filter Options")
    response = requests.get(f"{BASE_URL}/analytics/customer-insights/filters", headers=headers)
    print_response("Get Filter Options", response)
    return response

def test_get_customer_insights(years: str = None, months: str = None):
    """Test GET /analytics/customer-insights"""
    print("Testing: Get Customer Insights Data")
    params = {}
    if years:
        params['years'] = years
    if months:
        params['months'] = months
    
    response = requests.get(f"{BASE_URL}/analytics/customer-insights", headers=headers, params=params)
    print_response("Get Customer Insights", response)
    return response

def test_chat_simple():
    """Test POST /analytics/customer-insights/chat (simple)"""
    print("Testing: Customer Insights Chat (Simple)")
    payload = {
        "message": "What is the total gross sales?",
        "context": {},
        "conversation_history": []
    }
    response = requests.post(f"{BASE_URL}/analytics/customer-insights/chat", headers=headers, json=payload)
    print_response("Customer Insights Chat", response)
    return response

def test_view_insights_chat():
    """Test POST /analytics/customer-insights/view-insights/chat"""
    print("Testing: View Insights Chat")
    payload = {
        "message": "What are the top performing channels?",
        "chart_title": "Sales Channel Performance",
        "context": {
            "selectedYears": [2025],
            "selectedMonths": ["January"]
        },
        "conversation_history": []
    }
    response = requests.post(f"{BASE_URL}/analytics/customer-insights/view-insights/chat", headers=headers, json=payload)
    print_response("View Insights Chat", response)
    return response

def test_view_insights_chat_with_followup():
    """Test POST /analytics/customer-insights/view-insights/chat with follow-up"""
    print("Testing: View Insights Chat (Follow-up Question)")
    
    # First message
    payload1 = {
        "message": "What is the total sales for January 2025?",
        "context": {
            "selectedYears": [2025],
            "selectedMonths": ["January"]
        },
        "conversation_history": []
    }
    response1 = requests.post(f"{BASE_URL}/analytics/customer-insights/view-insights/chat", headers=headers, json=payload1)
    print_response("View Insights Chat - First Question", response1)
    
    # Follow-up message
    if response1.status_code == 200:
        data1 = response1.json()
        payload2 = {
            "message": "What about February?",
            "context": {
                "selectedYears": [2025]
            },
            "conversation_history": [
                {"role": "user", "content": payload1["message"]},
                {"role": "assistant", "content": data1.get("response", "")}
            ]
        }
        response2 = requests.post(f"{BASE_URL}/analytics/customer-insights/view-insights/chat", headers=headers, json=payload2)
        print_response("View Insights Chat - Follow-up", response2)
        return response2
    
    return response1

def test_health_check():
    """Test GET /analytics/customer-insights/chat/health"""
    print("Testing: Health Check")
    response = requests.get(f"{BASE_URL}/analytics/customer-insights/chat/health")
    print_response("Health Check", response)
    return response

def test_chat_test():
    """Test GET /analytics/customer-insights/chat/test"""
    print("Testing: Chat Test Endpoint")
    response = requests.get(f"{BASE_URL}/analytics/customer-insights/chat/test", headers=headers)
    print_response("Chat Test", response)
    return response

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Customer Deep Intelligence API Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {'*' * 20}...{TOKEN[-10:] if len(TOKEN) > 10 else TOKEN}")
    print("="*60)
    
    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("\n⚠️  WARNING: Please set your JWT token in the TOKEN variable!")
        print("   Get your token by logging into the application.\n")
        return
    
    try:
        # Test 1: Health Check (no auth required)
        test_health_check()
        
        # Test 2: Get Filters
        test_get_filters()
        
        # Test 3: Get Customer Insights (no filters)
        test_get_customer_insights()
        
        # Test 4: Get Customer Insights (with filters)
        test_get_customer_insights(years="2025", months="January")
        
        # Test 5: Simple Chat
        test_chat_simple()
        
        # Test 6: View Insights Chat
        test_view_insights_chat()
        
        # Test 7: View Insights Chat with Follow-up
        test_view_insights_chat_with_followup()
        
        # Test 8: Chat Test Endpoint
        test_chat_test()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

