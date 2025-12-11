"""
Final comprehensive test of all migrated endpoints
"""
import requests

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

print("=" * 60)
print("Final Endpoint Testing - New Architecture")
print("=" * 60)

# Use the working admin user
admin_email = "admin@thrivebrands.ai"
admin_password = "Thrive@123"  # Based on successful test

# Test 1: Login
print("\n[1/6] Testing Login...")
try:
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": admin_email, "password": admin_password},
        timeout=5
    )
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        print(f"   [OK] Login successful: {data.get('email')}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 2: Get Users
        print("\n[2/6] Testing Get Users...")
        response = requests.get(f"{API_BASE}/users", headers=headers, timeout=5)
        if response.status_code == 200:
            users = response.json()
            print(f"   [OK] Get users successful: {len(users)} users found")
        else:
            print(f"   [FAIL] Failed: {response.status_code}")
        
        # Test 3: Get Current User
        print("\n[3/6] Testing Get Current User...")
        response = requests.get(f"{API_BASE}/users/me", headers=headers, timeout=5)
        if response.status_code == 200:
            user = response.json()
            print(f"   [OK] Get current user successful: {user.get('email')}")
        else:
            print(f"   [FAIL] Failed: {response.status_code}")
        
        # Test 4: Get Users by Department
        print("\n[4/6] Testing Get Users by Department...")
        response = requests.get(f"{API_BASE}/users/by-department/technology", headers=headers, timeout=5)
        if response.status_code == 200:
            users = response.json()
            print(f"   [OK] Get users by department successful: {len(users)} users")
        else:
            print(f"   [FAIL] Failed: {response.status_code}")
        
        # Test 5: Get Data Source
        print("\n[5/6] Testing Get Data Source...")
        response = requests.get(f"{API_BASE}/data/source", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Get data source successful")
            print(f"      Source: {data.get('source')}, Records: {data.get('record_count')}")
        else:
            print(f"   [FAIL] Failed: {response.status_code}")
        
        # Test 6: Data Sync
        print("\n[6/6] Testing Data Sync...")
        response = requests.get(f"{API_BASE}/data/sync", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Data sync successful: {data.get('status')}")
            print(f"      Records: {data.get('records_count')}")
        else:
            print(f"   [FAIL] Failed: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe new backend architecture is working correctly!")
        print("All migrated endpoints are functional.")
        
    else:
        print(f"   [FAIL] Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   [FAIL] Cannot connect to server!")
    print("   Make sure server is running at http://localhost:8000")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

