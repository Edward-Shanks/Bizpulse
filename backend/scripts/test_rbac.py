#!/usr/bin/env python3
"""
ClickHouse RBAC Testing Script
Tests that RBAC users can only access data they're permitted to see
"""

import clickhouse_driver
from typing import Dict, List, Tuple
import sys

# Configuration
CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DB = "bizpulse"

# User credentials
USERS = {
    "admin": {
        "username": "bizpulse_admin",
        "password": "Admin@123!Secure",
        "description": "Full access to all data",
        "tests": [
            ("SELECT count() FROM sales_analytics", True),
            ("SELECT DISTINCT business FROM sales_analytics", True),
        ]
    },
    "manager": {
        "username": "manager_user",
        "password": "Manager@123",
        "description": "Food + Beauty businesses with profit",
        "tests": [
            ("SELECT count() FROM manager_multi_business_view", True),
            ("SELECT DISTINCT business FROM manager_multi_business_view", True),
            ("SELECT count() FROM sales_analytics", True),  # Has direct access
        ]
    },
    "sales": {
        "username": "sales_user",
        "password": "Sales@123",
        "description": "Food business only, revenue only",
        "tests": [
            ("SELECT count() FROM sales_food_view", True),
            ("SELECT DISTINCT business FROM sales_food_view", True),
            ("SELECT count() FROM sales_analytics", False),  # Should FAIL
            ("SELECT count() FROM manager_multi_business_view", False),  # Should FAIL
        ]
    },
    "finance": {
        "username": "finance_user",
        "password": "Finance@123",
        "description": "All financial data",
        "tests": [
            ("SELECT count() FROM sales_analytics", True),
            ("SELECT sum(gsales), sum(fgp), sum(group_cost) FROM sales_analytics", True),
        ]
    },
    "convenience": {
        "username": "convenience_user",
        "password": "Conv@123",
        "description": "Convenience channel only",
        "tests": [
            ("SELECT count() FROM sales_convenience_view", True),
            ("SELECT DISTINCT channel FROM sales_convenience_view", True),
            ("SELECT count() FROM sales_analytics", False),  # Should FAIL
        ]
    },
}


def test_user(user_info: Dict) -> Tuple[int, int, List[str]]:
    """
    Test a single user's access
    
    Returns:
        (passed, failed, errors)
    """
    username = user_info["username"]
    password = user_info["password"]
    tests = user_info["tests"]
    
    print(f"\n{'='*70}")
    print(f"Testing: {username}")
    print(f"Description: {user_info['description']}")
    print(f"{'='*70}")
    
    # Connect as user
    try:
        client = clickhouse_driver.Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            database=CLICKHOUSE_DB,
            user=username,
            password=password
        )
    except Exception as e:
        print(f"❌ FAILED to connect: {e}")
        return (0, len(tests), [str(e)])
    
    passed = 0
    failed = 0
    errors = []
    
    # Run each test
    for query, should_succeed in tests:
        try:
            result = client.execute(query)
            
            if should_succeed:
                print(f"✅ PASS: {query[:60]}...")
                if result:
                    print(f"   Result: {result[0]}")
                passed += 1
            else:
                print(f"❌ FAIL: Query should have been blocked but succeeded!")
                print(f"   Query: {query}")
                failed += 1
                errors.append(f"Query should have been blocked: {query}")
        
        except Exception as e:
            if not should_succeed:
                print(f"✅ PASS: Query correctly blocked")
                print(f"   Query: {query[:60]}...")
                print(f"   Error: {str(e)[:80]}...")
                passed += 1
            else:
                print(f"❌ FAIL: Query should have succeeded but failed!")
                print(f"   Query: {query}")
                print(f"   Error: {e}")
                failed += 1
                errors.append(f"Query failed: {query} - {e}")
    
    # Close connection
    client.disconnect()
    
    return (passed, failed, errors)


def main():
    """Run all RBAC tests"""
    
    print("\n" + "="*70)
    print("BIZPULSE - ClickHouse RBAC Testing")
    print("="*70)
    print("\nThis script tests that RBAC is working correctly.")
    print("Users should only see data they have permission for.")
    print("="*70)
    
    total_passed = 0
    total_failed = 0
    all_errors = []
    
    # Test each user
    for user_type, user_info in USERS.items():
        passed, failed, errors = test_user(user_info)
        total_passed += passed
        total_failed += failed
        all_errors.extend(errors)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"✅ Passed:   {total_passed}")
    print(f"❌ Failed:   {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("RBAC is working correctly.")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nErrors:")
        for i, error in enumerate(all_errors, 1):
            print(f"{i}. {error}")
        print("\nPlease check:")
        print("1. All users exist (run setup_rbac.sql)")
        print("2. All views exist (SHOW TABLES FROM bizpulse)")
        print("3. Grants are correct (SHOW GRANTS FOR username)")
    
    print("="*70)
    
    # Exit code
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
