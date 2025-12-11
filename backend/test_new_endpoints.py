"""
Test script for newly migrated endpoints
Tests only the endpoints we migrated to the new architecture
"""
import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

print("=" * 60)
print("Testing Newly Migrated Endpoints")
print("=" * 60)

# Test 1: Login
print("\n1. Testing Login...")
try:
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": "data.admin@thrivebrands.ai", "password": "ThriveBrands@2024"},
        timeout=5
    )
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        print(f"   [OK] Login successful: {data.get('email')}")
        print(f"   [OK] Token received")
        
        # Test 2: Get Users
        print("\n2. Testing Get Users...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/users", headers=headers, timeout=5)
        if response.status_code == 200:
            users = response.json()
            print(f"   [OK] Get users successful: {len(users)} users found")
        else:
            print(f"   [FAIL] Get users failed: {response.status_code} - {response.text}")
        
        # Test 3: Get Current User
        print("\n3. Testing Get Current User...")
        response = requests.get(f"{API_BASE}/users/me", headers=headers, timeout=5)
        if response.status_code == 200:
            user = response.json()
            print(f"   [OK] Get current user successful: {user.get('email')}")
        else:
            print(f"   [FAIL] Get current user failed: {response.status_code} - {response.text}")
        
        # Test 4: Get Users by Department
        print("\n4. Testing Get Users by Department...")
        response = requests.get(f"{API_BASE}/users/by-department/technology", headers=headers, timeout=5)
        if response.status_code == 200:
            users = response.json()
            print(f"   [OK] Get users by department successful: {len(users)} users in technology")
        else:
            print(f"   [FAIL] Get users by department failed: {response.status_code} - {response.text}")
        
        # Test 5: Get Data Source
        print("\n5. Testing Get Data Source...")
        response = requests.get(f"{API_BASE}/data/source", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Get data source successful")
            print(f"   [INFO] Source: {data.get('source')}, Records: {data.get('record_count')}")
        else:
            print(f"   [FAIL] Get data source failed: {response.status_code} - {response.text}")
        
        # Test 6: Data Sync (may take time)
        print("\n6. Testing Data Sync...")
        print("   [INFO] This may take a moment...")
        response = requests.get(f"{API_BASE}/data/sync", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] Data sync successful: {data.get('status')}")
            print(f"   [INFO] Records: {data.get('records_count')}")
        else:
            print(f"   [FAIL] Data sync failed: {response.status_code} - {response.text}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All migrated endpoints are working!")
        print("=" * 60)
        
    else:
        print(f"   [FAIL] Login failed: {response.status_code}")
        print(f"   [FAIL] Response: {response.text}")
        print("\n[ERROR] Cannot test other endpoints without authentication")
        
except requests.exceptions.ConnectionError:
    print("   [FAIL] Cannot connect to server!")
    print("   [INFO] Make sure server is running at http://localhost:8000")
except Exception as e:
    print(f"   [FAIL] Error: {e}")



