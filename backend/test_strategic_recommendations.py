"""
Test script specifically for strategic recommendations endpoint
"""
import requests
import json
import sys
import time

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

def test_strategic_recommendations():
    """Test strategic recommendations endpoint with detailed logging"""
    print_status("\n" + "="*60, "BOLD")
    print_status("Testing Strategic Recommendations Endpoint", "BOLD")
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
            return
        
        token = login_response.json().get("token")
        print_status(f"Login successful: {login_response.json().get('email')}", "SUCCESS")
    except Exception as e:
        print_status(f"Login error: {str(e)}", "ERROR")
        return
    
    # Step 2: Test endpoint
    print_status("\nStep 2: Calling strategic recommendations endpoint...", "INFO")
    print_status("Note: This may take 30-60 seconds due to AI processing", "WARNING")
    
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/strategic-recommendations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120  # 2 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        print_status(f"\nResponse received in {elapsed_time:.2f} seconds", "INFO")
        print_status(f"Status Code: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            data = response.json()
            recommended_count = len(data.get('recommended', []))
            live_count = len(data.get('live', []))
            past_count = len(data.get('past', []))
            
            print_status(f"\n✅ Strategic recommendations generated successfully!", "SUCCESS")
            print_status(f"   Recommended: {recommended_count} campaigns", "INFO")
            print_status(f"   Live: {live_count} campaigns", "INFO")
            print_status(f"   Past: {past_count} campaigns", "INFO")
            
            if recommended_count > 0:
                print_status("\nSample recommendation:", "INFO")
                sample = data.get('recommended', [])[0]
                print(f"   Title: {sample.get('title', 'N/A')}")
                print(f"   Category: {sample.get('category', 'N/A')}")
                print(f"   Budget: €{sample.get('budget', 0):,.2f}")
                print(f"   AI Score: {sample.get('aiScore', 'N/A')}")
            
            return True
        else:
            print_status(f"\n❌ Request failed with status {response.status_code}", "ERROR")
            print_status(f"Response: {response.text[:1000]}", "ERROR")
            return False
            
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        print_status(f"\n❌ Request timed out after {elapsed_time:.2f} seconds", "ERROR")
        print_status("This could indicate:", "WARNING")
        print_status("  1. AI API is slow or unresponsive", "WARNING")
        print_status("  2. Network connectivity issues", "WARNING")
        print_status("  3. The endpoint is hanging on a database query", "WARNING")
        return False
    except requests.exceptions.ConnectionError:
        print_status("\n❌ Connection error - is the server running?", "ERROR")
        return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print_status(f"\n❌ Error after {elapsed_time:.2f} seconds: {str(e)}", "ERROR")
        import traceback
        print_status(f"Traceback: {traceback.format_exc()[:500]}", "ERROR")
        return False

if __name__ == "__main__":
    test_strategic_recommendations()

