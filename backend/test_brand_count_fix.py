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

def test_brand_analysis_counts(token: str):
    """Test brand analysis active brands count"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Brand Analysis Active Brands Count", "INFO")
    print_status("="*60, "INFO")
    
    test_cases = [
        {"years": "2023", "months": "March", "expected": 34, "name": "March 2023"},
        {"years": "2023", "months": "June", "expected": 33, "name": "June 2023"},
        {"years": "2024", "months": None, "expected": 33, "name": "2024 Overall"},
        {"years": "2024", "months": "January", "expected": 31, "name": "January 2024"},
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        years = test_case["years"]
        months = test_case["months"]
        expected = test_case["expected"]
        name = test_case["name"]
        
        print_status(f"\n📊 Testing: {name}", "INFO")
        print_status("-" * 60, "INFO")
        
        try:
            # Build query params
            params = {"years": years}
            if months:
                params["months"] = months
            
            # Call brand analysis API
            response = requests.get(
                f"{BASE_URL}/analytics/brand-analysis",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                active_brands = data.get("active_brands", 0)
                brand_performance = data.get("brand_performance", [])
                
                print_status(f"   Active brands (API): {active_brands}", "INFO")
                print_status(f"   Expected: {expected}", "INFO")
                print_status(f"   Brand performance records: {len(brand_performance)}", "INFO")
                
                # Count brands manually from brand_performance
                manual_count = sum(
                    1 for item in brand_performance
                    if item.get("Brand") and 
                       item.get("Brand") != "Unknown" and 
                       str(item.get("Brand")).strip() != "" and
                       str(item.get("Brand")).lower() not in ["unknown", "none", "null", ""]
                )
                
                print_status(f"   Manual count (from brand_performance): {manual_count}", "INFO")
                
                if active_brands == expected:
                    print_status(f"   ✅ PASS: Active brands count matches expected!", "SUCCESS")
                else:
                    print_status(f"   ❌ FAIL: Active brands count ({active_brands}) does not match expected ({expected})", "ERROR")
                    all_passed = False
                    
                    # Show brands with 0 revenue
                    zero_revenue_brands = [
                        item["Brand"] for item in brand_performance
                        if item.get("Revenue", 0) == 0 and 
                           item.get("Brand") and 
                           item.get("Brand") != "Unknown"
                    ]
                    if zero_revenue_brands:
                        print_status(f"   Brands with 0 revenue: {zero_revenue_brands}", "WARNING")
                
            else:
                print_status(f"   ❌ API call failed: {response.status_code} - {response.text}", "ERROR")
                all_passed = False
                
        except Exception as e:
            print_status(f"   ❌ Test error: {str(e)}", "ERROR")
            import traceback
            print_status(f"   Traceback: {traceback.format_exc()}", "ERROR")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print_status("="*60, "INFO")
    print_status("Brand Analysis Active Brands Count Fix Verification", "INFO")
    print_status("="*60, "INFO")
    
    token = test_login()
    if token:
        success = test_brand_analysis_counts(token)
        if success:
            print_status("\n✅ All tests passed! Active brands count is now correct.", "SUCCESS")
        else:
            print_status("\n❌ Some tests failed. Please review the output above.", "ERROR")
    else:
        print_status("\n❌ Cannot proceed without authentication token", "ERROR")

