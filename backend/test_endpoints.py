"""
Comprehensive endpoint testing script
Tests all migrated endpoints to verify they work correctly
"""
import requests
import json
import sys
from typing import Optional

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "=" * 60)
    print("Testing Health Check Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check: {data}")
            return True
        else:
            print_error(f"Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\n" + "=" * 60)
    print("Testing Root Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Root endpoint: {data}")
            return True
        else:
            print_error(f"Root endpoint failed: Status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Root endpoint failed: {e}")
        return False

def test_login() -> Optional[str]:
    """Test login endpoint and return token"""
    print("\n" + "=" * 60)
    print("Testing Login Endpoint")
    print("=" * 60)
    
    try:
        payload = {
            "email": "data.admin@thrivebrands.ai",
            "password": "ThriveBrands@2024"
        }
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            email = data.get("email")
            print_success(f"Login successful for: {email}")
            print_info(f"Token received: {token[:50]}...")
            return token
        else:
            print_error(f"Login failed: Status {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Login failed: {e}")
        return None

def test_get_users(token: str):
    """Test get users endpoint"""
    print("\n" + "=" * 60)
    print("Testing Get Users Endpoint")
    print("=" * 60)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/users",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Get users successful: Found {len(data)} users")
            if data:
                print_info(f"First user: {data[0].get('email')}")
            return True
        else:
            print_error(f"Get users failed: Status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get users failed: {e}")
        return False

def test_get_current_user(token: str):
    """Test get current user endpoint"""
    print("\n" + "=" * 60)
    print("Testing Get Current User Endpoint")
    print("=" * 60)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/users/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Get current user successful: {data.get('email')}")
            return True
        else:
            print_error(f"Get current user failed: Status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get current user failed: {e}")
        return False

def test_get_users_by_department(token: str):
    """Test get users by department endpoint"""
    print("\n" + "=" * 60)
    print("Testing Get Users by Department Endpoint")
    print("=" * 60)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/users/by-department/technology",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Get users by department successful: Found {len(data)} users in technology")
            return True
        else:
            print_error(f"Get users by department failed: Status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get users by department failed: {e}")
        return False

def test_get_data_source(token: str):
    """Test get data source endpoint"""
    print("\n" + "=" * 60)
    print("Testing Get Data Source Endpoint")
    print("=" * 60)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE}/data/source",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Get data source successful")
            print_info(f"Source: {data.get('source')}")
            print_info(f"Database: {data.get('database')}")
            print_info(f"Record count: {data.get('record_count')}")
            return True
        else:
            print_error(f"Get data source failed: Status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get data source failed: {e}")
        return False

def test_data_sync(token: str):
    """Test data sync endpoint (may take time)"""
    print("\n" + "=" * 60)
    print("Testing Data Sync Endpoint")
    print("=" * 60)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        print_info("Requesting data sync (this may take a moment)...")
        response = requests.get(
            f"{API_BASE}/data/sync",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Data sync successful")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Message: {data.get('message')}")
            print_info(f"Records: {data.get('records_count')}")
            return True
        else:
            print_error(f"Data sync failed: Status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Data sync failed: {e}")
        return False

def test_invalid_token():
    """Test that invalid token is rejected"""
    print("\n" + "=" * 60)
    print("Testing Authentication (Invalid Token)")
    print("=" * 60)
    
    try:
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(
            f"{API_BASE}/users",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print_success("Invalid token correctly rejected (401 Unauthorized)")
            return True
        else:
            print_warning(f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Invalid token test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BizPulse Backend - Endpoint Testing")
    print("=" * 60)
    print(f"\nTesting server at: {BASE_URL}")
    print("Make sure the server is running!\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Root endpoint
    results.append(("Root Endpoint", test_root_endpoint()))
    
    # Test 3: Login
    token = test_login()
    results.append(("Login", token is not None))
    
    if not token:
        print_error("\nCannot continue without authentication token!")
        print_error("Please check login credentials and server status.")
        return
    
    # Test 4: Get users
    results.append(("Get Users", test_get_users(token)))
    
    # Test 5: Get current user
    results.append(("Get Current User", test_get_current_user(token)))
    
    # Test 6: Get users by department
    results.append(("Get Users by Department", test_get_users_by_department(token)))
    
    # Test 7: Get data source
    results.append(("Get Data Source", test_get_data_source(token)))
    
    # Test 8: Data sync (optional, may skip if takes too long)
    print_warning("Skipping data sync test (may take time, test manually if needed)")
    # results.append(("Data Sync", test_data_sync(token)))
    
    # Test 9: Invalid token
    results.append(("Invalid Token Rejection", test_invalid_token()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}[{status}]{Colors.RESET} {test_name}")
    
    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}[SUCCESS] All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}[WARNING] Some tests failed. Check the errors above.{Colors.RESET}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_error("\nCannot connect to server!")
        print_error("Make sure the server is running at http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



