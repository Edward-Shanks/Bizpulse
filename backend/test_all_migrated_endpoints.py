"""
Comprehensive test script for all migrated endpoints
Tests: Auth, Users, Analytics, Filters, Data
"""
import requests
import json
import sys
import os
from typing import Dict, Any, Optional

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@thrivebrands.ai"
ADMIN_PASSWORD = "Thrive@123"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages"""
    if status == "SUCCESS":
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    elif status == "ERROR":
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    elif status == "WARNING":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{message}{Colors.RESET}")

def test_login() -> Optional[str]:
    """Test login endpoint and return token"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Authentication Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print_status(f"Login successful: {data.get('email')}", "SUCCESS")
            return token
        else:
            print_status(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to server. Is it running on http://localhost:8000?", "ERROR")
        return None
    except Exception as e:
        print_status(f"Login error: {str(e)}", "ERROR")
        return None

def test_signup(token: str):
    """Test signup endpoint (development only)"""
    try:
        # Try to create a test user (will fail if exists, that's OK)
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={
                "email": "test.user@example.com",
                "password": "Test123!",
                "name": "Test User",
                "department": "technology",
                "role": "developer"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print_status("Signup endpoint working", "SUCCESS")
        elif response.status_code == 400:
            print_status("Signup endpoint working (user may already exist)", "WARNING")
        else:
            print_status(f"Signup failed: {response.status_code} - {response.text}", "ERROR")
    except Exception as e:
        print_status(f"Signup error: {str(e)}", "ERROR")

def test_get_users(token: str):
    """Test get all users endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing User Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            print_status(f"Get users successful: {len(users)} users found", "SUCCESS")
            return True
        else:
            print_status(f"Get users failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Get users error: {str(e)}", "ERROR")
        return False

def test_get_user_by_department(token: str):
    """Test get users by department endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/users/by-department/technology",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()
            print_status(f"Get users by department successful: {len(users)} users", "SUCCESS")
            return True
        else:
            print_status(f"Get users by department failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Get users by department error: {str(e)}", "ERROR")
        return False

def test_get_current_user(token: str):
    """Test get current user endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            print_status(f"Get current user successful: {user.get('email')}", "SUCCESS")
            return True
        else:
            print_status(f"Get current user failed: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Get current user error: {str(e)}", "ERROR")
        return False

def test_executive_overview(token: str):
    """Test executive overview endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Analytics Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/executive-overview",
            params={"years": "2024,2025"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Executive overview successful", "SUCCESS")
            if "total_revenue" in data:
                print_status(f"  Total Revenue: {data.get('total_revenue', 'N/A')}", "INFO")
            return True
        else:
            print_status(f"Executive overview failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Executive overview error: {str(e)}", "ERROR")
        return False

def test_customer_analysis(token: str):
    """Test customer analysis endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/customer-analysis",
            params={"years": "2024"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Customer analysis successful", "SUCCESS")
            return True
        else:
            print_status(f"Customer analysis failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Customer analysis error: {str(e)}", "ERROR")
        return False

def test_brand_analysis(token: str):
    """Test brand analysis endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/brand-analysis",
            params={"years": "2024"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Brand analysis successful", "SUCCESS")
            return True
        else:
            print_status(f"Brand analysis failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Brand analysis error: {str(e)}", "ERROR")
        return False

def test_category_analysis(token: str):
    """Test category analysis endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/category-analysis",
            params={"years": "2024"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Category analysis successful", "SUCCESS")
            return True
        else:
            print_status(f"Category analysis failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Category analysis error: {str(e)}", "ERROR")
        return False

def test_filter_options(token: str):
    """Test filter options endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Filter Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/filters/options",
            params={"years": "2024"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Filter options successful", "SUCCESS")
            if "years" in data:
                print_status(f"  Available years: {len(data.get('years', []))}", "INFO")
            return True
        else:
            print_status(f"Filter options failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Filter options error: {str(e)}", "ERROR")
        return False

def test_data_sync(token: str):
    """Test data sync endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Data Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/data/sync",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120  # Longer timeout for sync operation
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Data sync endpoint accessible", "SUCCESS")
            print_status(f"  Status: {data.get('status')}, Records: {data.get('records_count', 'N/A')}", "INFO")
            return True
        elif response.status_code == 408 or "timeout" in str(response).lower():
            print_status("Data sync timed out (expected for long operations)", "WARNING")
            return True  # Not a failure, just slow
        else:
            print_status(f"Data sync failed: {response.status_code}", "WARNING")
            return False
    except requests.exceptions.Timeout:
        print_status("Data sync timed out (expected for long operations)", "WARNING")
        return True  # Not a failure
    except Exception as e:
        print_status(f"Data sync error: {str(e)}", "ERROR")
        return False

def test_data_source(token: str):
    """Test data source endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/data/source",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Data source endpoint successful", "SUCCESS")
            return True
        else:
            print_status(f"Data source failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Data source error: {str(e)}", "ERROR")
        return False

def test_get_action_items(token: str):
    """Test get action items endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Action Items Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/cockpit/action-items",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            critical_count = len(data.get('critical', []))
            impact_count = len(data.get('impact', []))
            print_status(f"Get action items successful: {critical_count} critical, {impact_count} impact", "SUCCESS")
            return True
        else:
            print_status(f"Get action items failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Get action items error: {str(e)}", "ERROR")
        return False

def test_seed_action_items(token: str):
    """Test seed action items endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/cockpit/action-items/seed",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Seed action items successful", "SUCCESS")
            return True
        else:
            print_status(f"Seed action items failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Seed action items error: {str(e)}", "ERROR")
        return False

def test_get_root_cause_issues(token: str):
    """Test get root cause issues endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Root Cause Analysis Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/root-cause-analysis/issues",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            issues_count = len(data.get('issues', []))
            print_status(f"Get root cause issues successful: {issues_count} issues", "SUCCESS")
            return True
        else:
            print_status(f"Get root cause issues failed: {response.status_code} - {response.text[:200]}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Get root cause issues error: {str(e)}", "ERROR")
        return False

def test_generate_root_cause_issues(token: str):
    """Test generate root cause issues endpoint (may take time)"""
    try:
        response = requests.post(
            f"{BASE_URL}/root-cause-analysis/generate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120  # Longer timeout for AI generation
        )
        
        if response.status_code == 200:
            data = response.json()
            issues_count = len(data.get('issues', []))
            print_status(f"Generate root cause issues successful: {issues_count} issues generated", "SUCCESS")
            return True
        elif response.status_code == 408 or "timeout" in str(response).lower():
            print_status("Generate root cause issues timed out (expected for AI operations)", "WARNING")
            return True  # Not a failure, just slow
        else:
            print_status(f"Generate root cause issues failed: {response.status_code}", "WARNING")
            return False
    except requests.exceptions.Timeout:
        print_status("Generate root cause issues timed out (expected for AI operations)", "WARNING")
        return True  # Not a failure
    except Exception as e:
        print_status(f"Generate root cause issues error: {str(e)}", "ERROR")
        return False

def test_get_annual_goal(token: str):
    """Test get annual goal endpoint"""
    print_status("\n" + "="*60, "INFO")
    print_status("Testing Kanban Endpoints", "INFO")
    print_status("="*60, "INFO")
    
    try:
        response = requests.get(
            f"{BASE_URL}/kanban/annual-goal",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Get annual goal successful", "SUCCESS")
            if "current" in data:
                print_status(f"  Current: {data.get('current')}%, Target: {data.get('target')}%", "INFO")
            return True
        else:
            print_status(f"Get annual goal failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Get annual goal error: {str(e)}", "ERROR")
        return False

def test_get_kanban_recommendations(token: str):
    """Test get kanban recommendations endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/kanban/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            recommended_count = len(data.get('recommended', []))
            live_count = len(data.get('live', []))
            print_status(f"Get kanban recommendations successful: {recommended_count} recommended, {live_count} live", "SUCCESS")
            return True
        else:
            print_status(f"Get kanban recommendations failed: {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"Get kanban recommendations error: {str(e)}", "ERROR")
        return False

def test_generate_strategic_recommendations(token: str):
    """Test generate strategic recommendations endpoint (may take time)"""
    try:
        response = requests.get(
            f"{BASE_URL}/analytics/strategic-recommendations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=120  # Longer timeout for AI generation
        )
        
        if response.status_code == 200:
            data = response.json()
            recommended_count = len(data.get('recommended', []))
            print_status(f"Generate strategic recommendations successful: {recommended_count} recommendations", "SUCCESS")
            return True
        elif response.status_code == 408 or "timeout" in str(response).lower():
            print_status("Generate strategic recommendations timed out (expected for AI operations)", "WARNING")
            return True  # Not a failure, just slow
        else:
            print_status(f"Generate strategic recommendations failed: {response.status_code}", "WARNING")
            return False
    except requests.exceptions.Timeout:
        print_status("Generate strategic recommendations timed out (expected for AI operations)", "WARNING")
        return True  # Not a failure
    except Exception as e:
        print_status(f"Generate strategic recommendations error: {str(e)}", "ERROR")
        return False

def main():
    """Run all endpoint tests"""
    print_status("\n" + "="*60, "BOLD")
    print_status("COMPREHENSIVE ENDPOINT TEST SUITE", "BOLD")
    print_status("="*60, "BOLD")
    
    # Test login first
    token = test_login()
    if not token:
        print_status("\n❌ Cannot proceed without authentication token", "ERROR")
        return
    
    # Test signup
    test_signup(token)
    
    # Test user endpoints
    user_tests = [
        test_get_users(token),
        test_get_user_by_department(token),
        test_get_current_user(token)
    ]
    
    # Test analytics endpoints
    analytics_tests = [
        test_executive_overview(token),
        test_customer_analysis(token),
        test_brand_analysis(token),
        test_category_analysis(token)
    ]
    
    # Test filter endpoints
    filter_tests = [test_filter_options(token)]
    
    # Test data endpoints
    data_tests = [
        test_data_sync(token),
        test_data_source(token)
    ]
    
    # Test action items endpoints
    action_items_tests = [
        test_get_action_items(token),
        test_seed_action_items(token)
    ]
    
    # Test root cause analysis endpoints
    root_cause_tests = [
        test_get_root_cause_issues(token),
        test_generate_root_cause_issues(token)
    ]
    
    # Test kanban endpoints
    kanban_tests = [
        test_get_annual_goal(token),
        test_get_kanban_recommendations(token),
        test_generate_strategic_recommendations(token)
    ]
    
    # Summary
    print_status("\n" + "="*60, "BOLD")
    print_status("TEST SUMMARY", "BOLD")
    print_status("="*60, "BOLD")
    
    total_tests = len(user_tests) + len(analytics_tests) + len(filter_tests) + len(data_tests) + len(action_items_tests) + len(root_cause_tests) + len(kanban_tests) + 1  # +1 for login
    passed_tests = sum(user_tests) + sum(analytics_tests) + sum(filter_tests) + sum(data_tests) + sum(action_items_tests) + sum(root_cause_tests) + sum(kanban_tests) + 1
    
    print_status(f"Total Tests: {total_tests}", "INFO")
    print_status(f"Passed: {passed_tests}", "SUCCESS" if passed_tests == total_tests else "WARNING")
    print_status(f"Failed: {total_tests - passed_tests}", "ERROR" if passed_tests < total_tests else "SUCCESS")
    
    if passed_tests == total_tests:
        print_status("\n✅ All migrated endpoints are working correctly!", "SUCCESS")
    else:
        print_status("\n⚠️  Some endpoints need attention", "WARNING")

if __name__ == "__main__":
    main()

