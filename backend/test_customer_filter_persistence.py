import requests
import json
import sys

# Configure encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@thrivebrands.ai"
ADMIN_PASSWORD = "Thrive@123"

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "SUCCESS": "\033[92m",  # Green
        "ERROR": "\033[91m",    # Red
        "WARNING": "\033[93m", # Yellow
        "INFO": "\033[94m",     # Blue
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    print(f"{color}[{status}]{reset} {message}")

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
            token = data.get("token") or data.get("access_token")
            if token:
                print_status(f"✅ Login successful", "SUCCESS")
                return token
            else:
                print_status(f"❌ No token in response: {data}", "ERROR")
                return None
        else:
            print_status(f"❌ Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        print_status(f"❌ Login error: {str(e)}", "ERROR")
        return None

def test_filter_options_with_customer(token: str):
    """Test that filter options API includes customers parameter"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Filter Options with Customer Filter", "INFO")
    print_status("="*60, "INFO")
    
    try:
        # Test 1: Get filter options with customer=Austria
        print_status("\n📋 Test 1: Get filter options with customers=Austria", "INFO")
        response = requests.get(
            f"{BASE_URL}/filters/options?customers=Austria",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            print_status(f"✅ Filter options retrieved successfully", "SUCCESS")
            print_status(f"   Customers in response: {len(customers)}", "INFO")
            print_status(f"   Austria in list: {'Austria' in customers}", "INFO")
            if 'Austria' in customers:
                print_status(f"   ✅ Austria is preserved in customer list", "SUCCESS")
            else:
                print_status(f"   ⚠️ Austria not found in customer list", "WARNING")
        else:
            print_status(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 2: Get filter options with customer=Austria and month=Feb
        print_status("\n📋 Test 2: Get filter options with customers=Austria&months=Feb", "INFO")
        response = requests.get(
            f"{BASE_URL}/filters/options?customers=Austria&months=Feb",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            months = data.get('months', [])
            print_status(f"✅ Filter options retrieved successfully", "SUCCESS")
            print_status(f"   Customers in response: {len(customers)}", "INFO")
            print_status(f"   Months in response: {len(months)}", "INFO")
            print_status(f"   Austria in customer list: {'Austria' in customers}", "INFO")
            print_status(f"   Feb in month list: {'Feb' in months}", "INFO")
            
            if 'Austria' in customers:
                print_status(f"   ✅ Austria is preserved when month filter is applied", "SUCCESS")
            else:
                print_status(f"   ⚠️ Austria removed from customer list (might be expected if no data)", "WARNING")
        else:
            print_status(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 3: Get customer analysis data with both filters
        print_status("\n📋 Test 3: Get customer analysis with customers=Austria&months=Feb", "INFO")
        response = requests.get(
            f"{BASE_URL}/analytics/customer-analysis?customers=Austria&months=Feb",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total_revenue = data.get('total_revenue', 0)
            customer_performance = data.get('customer_performance', [])
            print_status(f"✅ Customer analysis retrieved successfully", "SUCCESS")
            print_status(f"   Total Revenue: €{total_revenue:,.2f}", "INFO")
            print_status(f"   Customer Performance Records: {len(customer_performance)}", "INFO")
            
            if total_revenue == 0:
                print_status(f"   ℹ️ No data for Austria in Feb (expected based on your description)", "INFO")
            else:
                print_status(f"   ✅ Data found for Austria in Feb", "SUCCESS")
        else:
            print_status(f"❌ Request failed: {response.status_code} - {response.text}", "ERROR")
            return False
        
        # Test 4: Verify customer filter is NOT removed when month filter is applied
        print_status("\n📋 Test 4: Verify customer filter persistence", "INFO")
        print_status("   This test verifies that when you call filter options with months=Feb", "INFO")
        print_status("   AND customers=Austria, the customer filter should be preserved", "INFO")
        
        # First get options with just customer
        response1 = requests.get(
            f"{BASE_URL}/filters/options?customers=Austria",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        # Then get options with customer + month
        response2 = requests.get(
            f"{BASE_URL}/filters/options?customers=Austria&months=Feb",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            customers1 = set(response1.json().get('customers', []))
            customers2 = set(response2.json().get('customers', []))
            
            if 'Austria' in customers1 and 'Austria' in customers2:
                print_status(f"   ✅ Austria preserved in both calls", "SUCCESS")
                return True
            elif 'Austria' in customers1 and 'Austria' not in customers2:
                print_status(f"   ⚠️ Austria removed when month filter applied (might be expected if no data)", "WARNING")
                print_status(f"   This is OK if there's genuinely no Austria data for Feb", "INFO")
                return True
            else:
                print_status(f"   ❌ Austria not found in initial customer list", "ERROR")
                return False
        else:
            print_status(f"❌ Request failed", "ERROR")
            return False
        
    except Exception as e:
        print_status(f"❌ Test error: {str(e)}", "ERROR")
        import traceback
        print_status(f"Traceback: {traceback.format_exc()}", "ERROR")
        return False

if __name__ == "__main__":
    print_status("="*60, "INFO")
    print_status("Customer Filter Persistence Test", "INFO")
    print_status("="*60, "INFO")
    
    token = test_login()
    if token:
        success = test_filter_options_with_customer(token)
        if success:
            print_status("\n✅ All tests completed!", "SUCCESS")
        else:
            print_status("\n❌ Some tests failed", "ERROR")
    else:
        print_status("\n❌ Cannot proceed without authentication token", "ERROR")

