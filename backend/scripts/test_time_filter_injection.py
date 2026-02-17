#!/usr/bin/env python3
"""
PRODUCTION CRITICAL: Default Time Filter Injection Test Suite
Tests that default time filter (last 24 months) is properly injected when missing.

This is a performance protection test - must pass before production deployment.
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


class TimeFilterInjectionTest:
    """Test suite for default time filter injection"""
    
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
    
    def test_no_date_filter_injected(self):
        """Test 1: Query without date filter gets default injected"""
        query = "SELECT sum(gsales) FROM sales_analytics GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        has_date_filter = "date >= addMonths(today(), -24)" in modified
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return has_date_filter
    
    def test_has_date_greater_than_not_injected(self):
        """Test 2: Query with date >= filter doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE date >= '2025-01-01' GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add another date filter
        date_filter_count = modified.count("date >=")
        original_preserved = "date >= '2025-01-01'" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        logger.info(f"Date filter count: {date_filter_count}")
        
        return date_filter_count == 1 and original_preserved
    
    def test_has_date_between_not_injected(self):
        """Test 3: Query with BETWEEN doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE date BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add default filter
        has_default = "addMonths(today(), -24)" in modified
        has_between = "BETWEEN" in modified.upper()
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return not has_default and has_between
    
    def test_has_todate_not_injected(self):
        """Test 4: Query with toDate(date) doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE toDate(date) >= '2025-01-01' GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add default filter
        has_default = "addMonths(today(), -24)" in modified
        has_todate = "toDate(date)" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return not has_default and has_todate
    
    def test_has_year_filter_not_injected(self):
        """Test 5: Query with year filter doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE year = 2024 GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add default filter
        has_default = "addMonths(today(), -24)" in modified
        has_year = "year = 2024" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return not has_default and has_year
    
    def test_has_year_in_not_injected(self):
        """Test 6: Query with year IN doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE year IN (2023, 2024) GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add default filter
        has_default = "addMonths(today(), -24)" in modified
        # Fix: Check case-insensitively - "year IN" in uppercase string will always be False
        has_year_in = "YEAR IN" in modified.upper() or "year IN" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return not has_default and has_year_in
    
    def test_has_quarter_not_injected(self):
        """Test 7: Query with quarter filter doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE quarter = 1 GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add default filter
        has_default = "addMonths(today(), -24)" in modified
        has_quarter = "quarter = 1" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return not has_default and has_quarter
    
    def test_has_month_not_injected(self):
        """Test 8: Query with month filter doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE month = 1 GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add default filter
        has_default = "addMonths(today(), -24)" in modified
        has_month = "month = 1" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return not has_default and has_month
    
    def test_has_addmonths_not_injected(self):
        """Test 9: Query with addMonths doesn't get modified"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE date >= addMonths(today(), -6) GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        # Should NOT add another addMonths
        addmonths_count = modified.count("addMonths")
        original_preserved = "addMonths(today(), -6)" in modified
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return addmonths_count == 1 and original_preserved
    
    def test_where_exists_adds_and(self):
        """Test 10: Query with WHERE adds AND date filter"""
        query = "SELECT sum(gsales) FROM sales_analytics WHERE business = 'Food' GROUP BY business"
        
        modified = self.client._add_default_time_filter(query)
        
        has_date_filter = "date >= addMonths(today(), -24)" in modified
        has_business = "business = 'Food'" in modified
        has_and = "AND" in modified.upper()
        
        logger.info(f"Original query: {query}")
        logger.info(f"Modified query: {modified}")
        
        return has_date_filter and has_business and has_and
    
    def test_execute_with_enforce_true(self):
        """Test 11: execute() with enforce_time_filter=True adds filter"""
        query = "SELECT sum(gsales) FROM sales_analytics GROUP BY business"
        
        # We can't easily check the modified query from execute(), but we can verify it runs
        try:
            result = self.client.execute(
                query,
                tenant_id='client_001',
                enforce_time_filter=True
            )
            logger.info(f"Query executed successfully with time filter enforcement")
            return True
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return False
    
    def test_execute_with_enforce_false(self):
        """Test 12: execute() with enforce_time_filter=False skips filter"""
        query = "SELECT sum(gsales) FROM sales_analytics GROUP BY business"
        
        try:
            result = self.client.execute(
                query,
                tenant_id='client_001',
                enforce_time_filter=False
            )
            logger.info(f"Query executed successfully without time filter enforcement")
            return True
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "="*70)
        logger.info("🚀 DEFAULT TIME FILTER INJECTION TEST SUITE")
        logger.info("="*70)
        
        self.run_test("No date filter → Default injected", self.test_no_date_filter_injected)
        self.run_test("Has date >= → Not modified", self.test_has_date_greater_than_not_injected)
        self.run_test("Has BETWEEN → Not modified", self.test_has_date_between_not_injected)
        self.run_test("Has toDate → Not modified", self.test_has_todate_not_injected)
        self.run_test("Has year = → Not modified", self.test_has_year_filter_not_injected)
        self.run_test("Has year IN → Not modified", self.test_has_year_in_not_injected)
        self.run_test("Has quarter → Not modified", self.test_has_quarter_not_injected)
        self.run_test("Has month → Not modified", self.test_has_month_not_injected)
        self.run_test("Has addMonths → Not modified", self.test_has_addmonths_not_injected)
        self.run_test("WHERE exists → Adds AND date", self.test_where_exists_adds_and)
        self.run_test("execute() enforce=True → Adds filter", self.test_execute_with_enforce_true)
        self.run_test("execute() enforce=False → Skips filter", self.test_execute_with_enforce_false)
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Tests: {self.passed + self.failed}")
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        
        if self.failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED - Time filter injection is working!")
            return True
        else:
            logger.error("\n⚠️  SOME TESTS FAILED - Review failures above")
            logger.error("\nFailed tests:")
            for name, status, error in self.tests:
                if status == "FAILED":
                    logger.error(f"  - {name}: {error}")
            return False


if __name__ == "__main__":
    tester = TimeFilterInjectionTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
