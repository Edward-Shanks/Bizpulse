"""
Test script for Customer Insights Chat endpoint
"""
import requests
import json
import sys

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@thrivebrands.ai"
ADMIN_PASSWORD = "Thrive@123"

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages"""
    colors = {
        "SUCCESS": '\033[92m',
        "ERROR": '\033[91m',
        "WARNING": '\033[93m',
        "INFO": '\033[94m',
        "BOLD": '\033[1m',
        "RESET": '\033[0m'
    }
    
    if status == "SUCCESS":
        print(f"{colors['SUCCESS']}✅ {message}{colors['RESET']}")
    elif status == "ERROR":
        print(f"{colors['ERROR']}❌ {message}{colors['RESET']}")
    elif status == "WARNING":
        print(f"{colors['WARNING']}⚠️  {message}{colors['RESET']}")
    elif status == "INFO":
        print(f"{colors['INFO']}ℹ️  {message}{colors['RESET']}")
    else:
        print(f"{colors['BOLD']}{message}{colors['RESET']}")

def test_customer_insights_chat():
    """Test Customer Insights Chat endpoint"""
    print_status("\n" + "="*60, "BOLD")
    print_status("Testing Customer Insights Chat Endpoint", "BOLD")
    print_status("="*60, "BOLD")
    
    # Step 1: Login
    print_status("\nStep 1: Logging in...", "INFO")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print_status(f"Login failed: {login_response.status_code} - {login_response.text}", "ERROR")
            return False
        
        token = login_response.json().get("token")
        print_status(f"Login successful: {login_response.json().get('email')}", "SUCCESS")
    except Exception as e:
        print_status(f"Login error: {str(e)}", "ERROR")
        return False
    
    # Step 2: Test Customer Insights Chat
    print_status("\nStep 2: Testing Customer Insights Chat...", "INFO")
    print_status("Note: This may take 30-60 seconds due to AI processing", "WARNING")
    
    try:
        payload = {
            "message": "What is the total gross sales?",
            "chart_title": "Sales Channel Performance",
            "context": {
                "selectedYears": [2025],
                "selectedMonths": ["January"]
            },
            "conversation_history": []
        }
        
        response = requests.post(
            f"{BASE_URL}/analytics/customer-insights/chat",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=120  # 2 minute timeout for AI
        )
        
        print_status(f"\nStatus Code: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"✅ Customer Insights Chat successful!", "SUCCESS")
            print_status(f"   Response length: {len(data.get('response', ''))} characters", "INFO")
            print_status(f"   Has data: {bool(data.get('data'))}", "INFO")
            print_status(f"\nResponse preview (first 200 chars):", "INFO")
            print(f"   {data.get('response', '')[:200]}...")
            return True
        else:
            print_status(f"\n❌ Request failed with status {response.status_code}", "ERROR")
            print_status(f"Response: {response.text[:500]}", "ERROR")
            return False
            
    except requests.exceptions.Timeout:
        print_status("\n❌ Request timed out", "ERROR")
        return False
    except requests.exceptions.ConnectionError:
        print_status("\n❌ Connection error - is the server running?", "ERROR")
        return False
    except Exception as e:
        print_status(f"\n❌ Error: {str(e)}", "ERROR")
        import traceback
        print_status(f"Traceback: {traceback.format_exc()[:500]}", "ERROR")
        return False

if __name__ == "__main__":
    import time
    print_status("Waiting 10 seconds for server to start...", "INFO")
    time.sleep(10)
    test_customer_insights_chat()

