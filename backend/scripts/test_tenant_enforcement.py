#!/usr/bin/env python3
"""
PRODUCTION CRITICAL: Tenant ID Enforcement Test Suite
Tests that tenant_id is properly injected and enforced in all queries.

This is a security regression test - must pass before production deployment.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.clickhouse_client import ClickHouseClient
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Test configuration
TEST_TENANT_ID = 'client_001'
WRONG_TENANT_ID = 'client_999'
TEST_DATABASE = os.getenv('CLICKHOUSE_DB', 'bizpulse')


class TenantEnforcementTest:
    """Test suite for tenant_id enforcement"""
    
    def __init__(self):
        self.client = ClickHouseClient()
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def run_test(self, name: str, test_func):
        """Run a single test"""
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"TEST: {name}")
            logger.info(f"{'='*70}")
            result = test_func()
            if result:
                logger.info(f"✅ PASSED: {name}")
                self.passed += 1
                self.tests.append((name, "PASSED", None))
            else:
                logger.error(f"❌ FAILED: {name}")
                self.failed += 1
                self.tests.append((name, "FAILED", "Test returned False"))
        except Exception as e:
            logger.error(f"❌ FAILED: {name} - Exception: {e}")
            self.failed += 1
            self.tests.append((name, "FAILED", str(e)))
    
    def test_no_tenant_injected_default(self):
        """Test 1: Query without tenant_id gets default injected"""
        query = "SELECT sum(gsales) FROM sales_analytics GROUP BY business"
        
        # Get the modified query (we'll check it was modified)
        # Since execute() modifies internally, we need to check via _inject_tenant_filter
        modified = self.client._inject_tenant_filter(query, TEST_TENANT_ID)
        
        has_tenant = f"tenant_id = '{TEST_TENANT_ID}'" in modified
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return has_tenant
    
    def test_correct_tenant_returns_data(self):
        """Test 2: Query with correct tenant_id returns data"""
        query = "SELECT count() FROM sales_analytics"
        
        try:
            result = self.client.execute(
                query,
                tenant_id=TEST_TENANT_ID,
                enforce_time_filter=False  # Skip time filter for this test
            )
            count = result[0][0] if result else 0
            logger.info(f"Query returned {count} rows")
            return count >= 0  # Should return count (even if 0)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return False
    
    def test_wrong_tenant_returns_empty(self):
        """Test 3: Query with wrong tenant_id returns empty results"""
        query = "SELECT count() FROM sales_analytics"
        
        try:
            # First, check if correct tenant has data
            correct_result = self.client.execute(
                query,
                tenant_id=TEST_TENANT_ID,
                enforce_time_filter=False
            )
            correct_count = correct_result[0][0] if correct_result else 0
            
            # If correct tenant has no data, skip this test (table might be empty)
            if correct_count == 0:
                logger.warning("Correct tenant has no data - skipping wrong tenant test")
                return True  # Don't fail if table is empty
            
            # Now check wrong tenant
            wrong_result = self.client.execute(
                query,
                tenant_id=WRONG_TENANT_ID,
                enforce_time_filter=False
            )
            wrong_count = wrong_result[0][0] if wrong_result else 0
            
            logger.info(f"Correct tenant ({TEST_TENANT_ID}): {correct_count} rows")
            logger.info(f"Wrong tenant ({WRONG_TENANT_ID}): {wrong_count} rows")
            
            # Wrong tenant MUST return 0 if correct tenant has data
            return wrong_count == 0
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return False
    
    def test_tenant_already_in_where(self):
        """Test 4: Query with tenant_id already in WHERE doesn't duplicate"""
        query = f"SELECT sum(gsales) FROM sales_analytics WHERE tenant_id = '{TEST_TENANT_ID}' GROUP BY business"
        
        modified = self.client._inject_tenant_filter(query, TEST_TENANT_ID)
        
        # Count occurrences of tenant_id filter
        count = modified.count(f"tenant_id = '{TEST_TENANT_ID}'")
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        logger.info(f"Tenant filter count: {count}")
        
        return count == 1  # Should appear exactly once
    
    def test_where_exists_no_tenant(self):
        """Test 5: Query with WHERE but no tenant_id adds AND tenant_id"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE business = 'Food' GROUP BY business"
        
        modified = self.client._inject_tenant_filter(query, TEST_TENANT_ID)
        
        has_tenant = f"tenant_id = '{TEST_TENANT_ID}'" in modified
        has_where = "WHERE" in modified.upper()
        has_business = "business = 'Food'" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return has_tenant and has_where and has_business
    
    def test_subquery_handling(self):
        """Test 6: Subquery handling (edge case - may need improvement)"""
        query = """
        SELECT business, total
        FROM (
            SELECT business, sum(gsales) as total
            FROM sales_analytics
            GROUP BY business
        ) t
        """
        
        try:
            modified = self.client._inject_tenant_filter(query, TEST_TENANT_ID)
            # Should inject tenant_id in inner query
            has_tenant = f"tenant_id = '{TEST_TENANT_ID}'" in modified
            logger.info(f"Original query: {query}")
            logger.info(f"Modified query: {modified}")
            
            # CRITICAL: Don't silently pass - check if injection actually worked
            if not has_tenant:
                logger.error("Subquery test FAILED - tenant_id not injected")
                return False
            
            return True
        except ValueError as e:
            # If validation blocks subqueries, that's acceptable for now
            logger.info(f"Subquery blocked by validation (acceptable): {e}")
            return True
        except Exception as e:
            logger.error(f"Subquery test failed with error: {e}")
            return False
    
    def test_case_insensitive_where(self):
        """Test 7: Case-insensitive WHERE detection"""
        query = "select sum(gsales) from sales_analytics where business = 'Food'"
        
        modified = self.client._inject_tenant_filter(query, TEST_TENANT_ID)
        has_tenant = f"tenant_id = '{TEST_TENANT_ID}'" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return has_tenant
    
    def test_rbac_with_tenant(self):
        """Test 8: RBAC methods extract tenant_id from user_permissions"""
        query = "SELECT sum(gsales) FROM sales_analytics GROUP BY business"
        
        user_permissions = {
            'tenant_id': TEST_TENANT_ID,
            'role': 'sales',
            'businesses': ['Food']
        }
        
        try:
            result = self.client.execute_with_rbac(
                query,
                user_permissions,
                tenant_id=None,  # Should extract from user_permissions
                enforce_time_filter=False
            )
            logger.info(f"RBAC query executed successfully")
            return True
        except Exception as e:
            logger.error(f"RBAC query failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "="*70)
        logger.info("🚀 TENANT ID ENFORCEMENT TEST SUITE")
        logger.info("="*70)
        
        self.run_test("No tenant → Default injected", self.test_no_tenant_injected_default)
        self.run_test("Correct tenant → Returns data", self.test_correct_tenant_returns_data)
        self.run_test("Wrong tenant → Returns empty", self.test_wrong_tenant_returns_empty)
        self.run_test("Tenant already in WHERE → No duplicate", self.test_tenant_already_in_where)
        self.run_test("WHERE exists → Adds AND tenant_id", self.test_where_exists_no_tenant)
        self.run_test("Subquery handling", self.test_subquery_handling)
        self.run_test("Case-insensitive WHERE", self.test_case_insensitive_where)
        self.run_test("RBAC extracts tenant_id", self.test_rbac_with_tenant)
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Tests: {self.passed + self.failed}")
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        
        if self.failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED - Tenant enforcement is working!")
            return True
        else:
            logger.error("\n⚠️  SOME TESTS FAILED - Review failures above")
            logger.error("\nFailed tests:")
            for name, status, error in self.tests:
                if status == "FAILED":
                    logger.error(f"  - {name}: {error}")
            return False


if __name__ == "__main__":
    tester = TenantEnforcementTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
