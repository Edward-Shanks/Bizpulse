"""
ClickHouse Database Client for BizPulse
Provides connection, query execution, and RBAC support
"""

from clickhouse_driver import Client
from typing import List, Dict, Any, Optional, Tuple
import os
from datetime import datetime, date, timedelta
import re
import logging
import time
from dotenv import load_dotenv

# CRITICAL: Load .env file BEFORE reading environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Default tenant ID (can be overridden per request)
DEFAULT_TENANT_ID = os.getenv('TENANT_ID', 'client_001')

# Default time filter: last 24 months
DEFAULT_TIME_MONTHS = int(os.getenv('DEFAULT_TIME_MONTHS', '24'))


class ClickHouseClient:
    """
    ClickHouse database client with RBAC support
    
    Features:
    - Connection pooling
    - RBAC view mapping
    - Query execution
    - Error handling
    - Type conversion
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None
    ):
        """
        Initialize ClickHouse client
        
        Args:
            host: ClickHouse host (default from env)
            port: ClickHouse port (default from env)
            database: Database name (default from env)
            user: Username (default from env)
            password: Password (default from env)
        """
        self.host = host or os.getenv('CLICKHOUSE_HOST', 'localhost')
        self.port = int(port or os.getenv('CLICKHOUSE_PORT', 9000))
        self.database = database or os.getenv('CLICKHOUSE_DB', 'bizpulse')
        self.user = user or os.getenv('CLICKHOUSE_USER', 'bizpulse_admin')
        self.password = password or os.getenv('CLICKHOUSE_PASSWORD', 'Admin@123!Secure')
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to ClickHouse"""
        try:
            self.client = Client(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                settings={
                    'use_numpy': False,
                    'max_execution_time': 30,  # 30 seconds timeout
                }
            )
            logger.info(f"Connected to ClickHouse at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    def _validate_query_safety(self, query: str) -> None:
        """
        Validate query is safe to execute - blocks dangerous SQL constructs
        
        Args:
            query: SQL query to validate
            
        Raises:
            ValueError: If query contains unsafe constructs
        """
        # CRITICAL: Strip SQL comments before validation
        # Remove /* ... */ style comments
        clean_query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        # Remove -- style comments
        clean_query = re.sub(r'--.*?$', '', clean_query, flags=re.MULTILINE)
        # Strip whitespace
        clean_query = clean_query.strip()
        
        query_upper = clean_query.upper()
        
        # CRITICAL: Only allow SELECT queries (after comment stripping)
        if not query_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed. Non-SELECT queries are blocked for security.")
        
        # CRITICAL: Block dangerous SQL constructs
        dangerous_patterns = [
            (r'\bINSERT\b', 'INSERT statements are not allowed'),
            (r'\bUPDATE\b', 'UPDATE statements are not allowed'),
            (r'\bDELETE\b', 'DELETE statements are not allowed'),
            (r'\bDROP\b', 'DROP statements are not allowed'),
            (r'\bALTER\b', 'ALTER statements are not allowed'),
            (r'\bTRUNCATE\b', 'TRUNCATE statements are not allowed'),
            (r'\bCREATE\b', 'CREATE statements are not allowed'),
            (r'\bSYSTEM\s+', 'SYSTEM commands are not allowed'),
            (r'\bEXEC\b', 'EXEC statements are not allowed'),
            (r'\bEXECUTE\b', 'EXECUTE statements are not allowed'),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, query_upper):
                raise ValueError(f"Unsafe SQL detected: {message}")
        
        # CRITICAL: Block subqueries completely (raise error, don't just warn)
        # Subqueries make tenant injection unreliable and are unnecessary for BI queries
        select_pos = query_upper.find('SELECT')
        if select_pos >= 0:
            after_select = query_upper[select_pos + 6:]
            # Check for subquery pattern: SELECT ... (SELECT ...)
            # This matches: (SELECT ...), FROM (SELECT ...), etc.
            if re.search(r'\([^)]*\bSELECT\b', after_select, re.IGNORECASE):
                raise ValueError("Subqueries are not supported. Use simple SELECT queries with JOINs if needed.")
    
    def _inject_tenant_filter(self, query: str, tenant_id: str) -> str:
        """
        Inject tenant_id filter into WHERE clause
        
        SECURITY: This uses regex-based SQL rewriting which has limitations.
        For production, consider using ClickHouse Row Policies for database-level enforcement.
        
        Args:
            query: SQL query
            tenant_id: Tenant identifier
            
        Returns:
            Modified query with tenant_id filter
            
        Raises:
            ValueError: If query structure cannot be safely modified
        """
        query_upper = query.upper()
        
        # CRITICAL: Check if tenant_id filter already exists as actual equality condition
        # Not just presence of string, but actual filter condition
        tenant_filter_pattern = re.compile(
            r'\btenant_id\s*=\s*[\'"]([^\'"]+)[\'"]',
            re.IGNORECASE
        )
        existing_tenant_match = tenant_filter_pattern.search(query)
        
        if existing_tenant_match:
            existing_tenant = existing_tenant_match.group(1)
            if existing_tenant == tenant_id:
                logger.debug(f"tenant_id filter already present with correct value: {tenant_id}")
                return query
            else:
                # Different tenant_id in query - this is a security issue
                logger.warning(f"Query contains different tenant_id ({existing_tenant}) than requested ({tenant_id})")
                raise ValueError(f"Query contains tenant_id filter for different tenant: {existing_tenant}")
        
        # CRITICAL: Skip tenant injection for system queries without FROM clause
        # Examples: SELECT version(), SELECT now(), SELECT 1, etc.
        if not re.search(r'\bFROM\b', query_upper):
            logger.debug("No FROM clause found - skipping tenant injection (system query)")
            return query
        
        # Find WHERE clause position (case-insensitive)
        where_match = re.search(r'\bWHERE\b', query_upper)
        
        if where_match:
            # WHERE clause exists - add tenant_id filter at the beginning
            where_pos = where_match.start()
            insert_pos = where_match.end()
            # Add tenant_id filter at start of WHERE clause
            tenant_filter = f" tenant_id = '{tenant_id}' AND"
            query = query[:insert_pos] + tenant_filter + query[insert_pos:]
            logger.debug(f"Injected tenant_id filter: tenant_id = '{tenant_id}'")
        else:
            # No WHERE clause - find FROM clause and add WHERE after it
            # Handle both: FROM table and FROM database.table
            from_match = re.search(r'\bFROM\b\s+([\w.]+)', query_upper)
            if from_match:
                # Find end of FROM clause (including potential alias)
                from_end_match = re.search(r'\bFROM\b\s+[\w.]+\s*(?:AS\s+\w+)?', query_upper)
                if from_end_match:
                    from_pos = from_end_match.end()
                else:
                    from_pos = from_match.end()
                
                # Trailing space so "GROUP BY" etc. is not concatenated without space
                query = query[:from_pos] + f" WHERE tenant_id = '{tenant_id}' " + query[from_pos:]
                logger.debug(f"Added WHERE clause with tenant_id filter: tenant_id = '{tenant_id}'")
            else:
                logger.error("Could not find FROM clause - tenant_id filter not injected")
                raise ValueError("Query structure invalid: cannot find FROM clause for tenant_id injection")
        
        return query
    
    def _add_default_time_filter(self, query: str) -> str:
        """
        Check if query has date/time filters and add default if missing
        
        Uses safer appending approach instead of inserting in middle of SQL.
        
        Args:
            query: SQL query
            
        Returns:
            Modified query with default time filter if needed
        """
        query_upper = query.upper()
        
        # CRITICAL: Check for existing date/time filters (improved patterns)
        # Must check for actual operators, not just characters
        date_patterns = [
            r'\bdate\s*>=',              # date >=
            r'\bdate\s*<=',              # date <=
            r'\bdate\s*=',               # date =
            r'\bdate\s*<',               # date <
            r'\bdate\s*>',               # date >
            r'\bdate\s+BETWEEN',         # date BETWEEN
            r'\byear\s*=',               # year =
            r'\byear\s+IN\s*\(',         # year IN (...)
            r'\bmonth\s*=',              # month =
            r'\bquarter\s*=',            # quarter =
            r'\bquarter\s+IN\s*\(',     # quarter IN (...)
            r'\byear_month\s*=',         # year_month =
            r'toYYYYMM\s*\(',            # toYYYYMM(...)
            r'toStartOfMonth\s*\(',      # toStartOfMonth(...)
            r'toDate\s*\(',              # toDate(...)
            r'addMonths\s*\(',           # addMonths(...)
            r'addYears\s*\(',            # addYears(...)
            r'today\s*\(',               # today()
            r'yesterday\s*\(',           # yesterday()
        ]
        
        has_date_filter = any(re.search(pattern, query_upper, re.IGNORECASE) for pattern in date_patterns)
        
        if has_date_filter:
            logger.debug("Query already has date/time filter - skipping default")
            return query
        
        # SAFER APPROACH: Append WHERE clause instead of inserting in middle
        # Find WHERE clause
        where_match = re.search(r'\bWHERE\b', query_upper)
        
        if where_match:
            # WHERE clause exists - append AND condition at the end of WHERE clause
            # Find end of WHERE clause (before GROUP BY, ORDER BY, LIMIT, etc.)
            where_end_patterns = [
                r'\bGROUP\s+BY\b',
                r'\bORDER\s+BY\b',
                r'\bHAVING\b',
                r'\bLIMIT\b',
                r'\bUNION\b',
            ]
            
            where_end_pos = len(query)
            for pattern in where_end_patterns:
                match = re.search(pattern, query_upper)
                if match and match.start() < where_end_pos:
                    where_end_pos = match.start()
            
            # Insert AND condition before GROUP BY/ORDER BY/etc.
            time_filter = f" AND date >= addMonths(today(), -{DEFAULT_TIME_MONTHS})"
            query = query[:where_end_pos] + time_filter + query[where_end_pos:]
            logger.info(f"Added default time filter: last {DEFAULT_TIME_MONTHS} months")
        else:
            # No WHERE clause - find FROM clause and append WHERE
            # Handle: FROM table, FROM database.table, FROM table AS alias
            from_match = re.search(r'\bFROM\b\s+([\w.]+)', query_upper)
            if from_match:
                # Find end of FROM clause (including potential alias)
                from_end_match = re.search(r'\bFROM\b\s+[\w.]+\s*(?:AS\s+\w+)?', query_upper)
                if from_end_match:
                    from_pos = from_end_match.end()
                else:
                    from_pos = from_match.end()
                
                # Find where to insert (before GROUP BY, ORDER BY, etc.)
                insert_pos = from_pos
                for pattern in [r'\bGROUP\s+BY\b', r'\bORDER\s+BY\b', r'\bLIMIT\b']:
                    match = re.search(pattern, query_upper)
                    if match and match.start() > from_pos:
                        insert_pos = min(insert_pos, match.start())
                
                # Trailing space so "GROUP BY" etc. is not concatenated without space
                query = query[:insert_pos] + f" WHERE date >= addMonths(today(), -{DEFAULT_TIME_MONTHS}) " + query[insert_pos:]
                logger.info(f"Added WHERE clause with default time filter: last {DEFAULT_TIME_MONTHS} months")
            else:
                logger.warning("Could not find FROM clause - default time filter not added")
        
        return query
    
    def execute(
        self,
        query: str,
        params: tuple = None,
        with_column_types: bool = False,
        tenant_id: Optional[str] = None,
        enforce_time_filter: bool = True
    ) -> List[tuple]:
        """
        Execute a query and return results
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            with_column_types: Return column types with results
            tenant_id: Tenant ID to enforce (if None, uses DEFAULT_TENANT_ID)
            enforce_time_filter: If True, adds default time filter when missing
            
        Returns:
            List of tuples (rows)
        """
        # CRITICAL: Validate query safety first
        self._validate_query_safety(query)
        
        # CRITICAL: Enforce tenant_id (always use _inject_tenant_filter for semantic checks)
        # If tenant_id is None, fall back to DEFAULT_TENANT_ID
        if tenant_id is None:
            logger.warning("No tenant_id specified - using default tenant_id enforcement")
            tenant_to_use = DEFAULT_TENANT_ID
        else:
            tenant_to_use = tenant_id

        query = self._inject_tenant_filter(query, tenant_to_use)
        
        # CRITICAL: Add default time filter if missing
        if enforce_time_filter:
            query = self._add_default_time_filter(query)
        
        try:
            logger.info(f"DATA_SOURCE=ClickHouse | executing query at {self.host}:{self.port} (Mac Studio)")
            t0 = time.perf_counter()
            result = self.client.execute(
                query,
                params,
                with_column_types=with_column_types
            )
            query_ms = int((time.perf_counter() - t0) * 1000)
            row_count = len(result) if not with_column_types else len(result[0])
            logger.info(f"DATA_SOURCE=ClickHouse | query_ms={query_ms} | rows={row_count}")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def execute_dict(
        self,
        query: str,
        params: tuple = None,
        tenant_id: Optional[str] = None,
        enforce_time_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute query and return results as list of dictionaries
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            tenant_id: Tenant ID to enforce
            enforce_time_filter: Add default time filter if missing
            
        Returns:
            List of dictionaries with column names as keys
        """
        result, columns = self.execute(
            query, 
            params, 
            with_column_types=True,
            tenant_id=tenant_id,
            enforce_time_filter=enforce_time_filter
        )
        column_names = [col[0] for col in columns]
        
        return [
            dict(zip(column_names, row))
            for row in result
        ]
    
    def execute_with_rbac(
        self,
        query: str,
        user_permissions: Dict[str, Any],
        params: tuple = None,
        tenant_id: Optional[str] = None,
        enforce_time_filter: bool = True
    ) -> List[tuple]:
        """
        Execute query using user's RBAC view
        
        Args:
            query: SQL query (uses sales_analytics table name)
            user_permissions: User permission dict (from MongoDB)
            params: Query parameters (optional)
            tenant_id: Tenant ID to enforce
            enforce_time_filter: Add default time filter if missing
            
        Returns:
            List of tuples (rows)
        """
        # Extract tenant_id from user_permissions if not provided
        if not tenant_id:
            tenant_id = user_permissions.get('tenant_id', DEFAULT_TENANT_ID)
        
        # Determine which view user should use
        view_name = self._get_user_view(user_permissions)
        
        # CRITICAL: Use regex word boundary to replace table name safely
        # This prevents replacing substrings inside column names, comments, string literals, etc.
        rbac_query = re.sub(
            r'\bsales_analytics\b',
            view_name,
            query,
            flags=re.IGNORECASE
        )
        
        logger.info(f"Executing query with RBAC view: {view_name}, tenant_id: {tenant_id}")
        return self.execute(
            rbac_query, 
            params,
            tenant_id=tenant_id,
            enforce_time_filter=enforce_time_filter
        )
    
    def execute_dict_with_rbac(
        self,
        query: str,
        user_permissions: Dict[str, Any],
        params: tuple = None,
        tenant_id: Optional[str] = None,
        enforce_time_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute query with RBAC and return dictionaries
        
        Args:
            query: SQL query
            user_permissions: User permission dict
            params: Query parameters (optional)
            tenant_id: Tenant ID to enforce
            enforce_time_filter: Add default time filter if missing
            
        Returns:
            List of dictionaries
        """
        # Extract tenant_id from user_permissions if not provided
        if not tenant_id:
            tenant_id = user_permissions.get('tenant_id', DEFAULT_TENANT_ID)
        
        view_name = self._get_user_view(user_permissions)
        # CRITICAL: Use regex word boundary for safe replacement
        rbac_query = re.sub(
            r'\bsales_analytics\b',
            view_name,
            query,
            flags=re.IGNORECASE
        )
        
        return self.execute_dict(
            rbac_query, 
            params,
            tenant_id=tenant_id,
            enforce_time_filter=enforce_time_filter
        )
    
    def _get_user_view(self, user_permissions: Dict[str, Any]) -> str:
        """
        Determine which view to use based on user permissions
        
        Args:
            user_permissions: Dict containing user's access rights
                {
                    'businesses': ['Food', 'Beauty'],
                    'channels': ['Convenience'],
                    'brands': ['Heinz'],
                    'data_types': ['revenue', 'profit']
                }
        
        Returns:
            View name to use
        """
        businesses = user_permissions.get('businesses', [])
        channels = user_permissions.get('channels', [])
        brands = user_permissions.get('brands', [])
        data_types = user_permissions.get('data_types', [])
        
        # Admin: Full access
        if user_permissions.get('is_admin', False):
            return 'sales_analytics'
        
        # Finance: All data
        if user_permissions.get('role') == 'finance':
            return 'sales_analytics'
        
        # Brand-specific access
        if brands and len(brands) == 1:
            brand = brands[0].lower().replace(' ', '_')
            return f'sales_{brand}_view'
        
        # Channel-specific access
        if channels and len(channels) == 1:
            channel = channels[0].lower().replace(' ', '_')
            return f'sales_{channel}_view'
        
        # Business-specific access
        if businesses:
            if len(businesses) == 1 and businesses[0] == 'Food':
                return 'sales_food_view'
            elif set(businesses) == {'Food', 'Beauty'}:
                return 'manager_multi_business_view'
        
        # Default: Most restricted view
        logger.warning(f"No specific view found for permissions: {user_permissions}")
        return 'sales_food_view'  # Default to most restricted
    
    def test_connection(self) -> bool:
        """
        Test connection to ClickHouse
        
        Returns:
            True if connection is successful
        """
        try:
            version = self.execute('SELECT version()')[0][0]
            logger.info(f"ClickHouse version: {version}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_table_info(self, table_name: str = 'sales_analytics') -> Dict[str, Any]:
        """
        Get information about a table
        
        Args:
            table_name: Name of table
            
        Returns:
            Dict with table info (columns, row count, size, etc.)
        """
        try:
            # Get column info
            columns_query = f"DESCRIBE TABLE {self.database}.{table_name}"
            columns = self.execute_dict(columns_query)
            
            # Get row count
            count_query = f"SELECT count() FROM {self.database}.{table_name}"
            row_count = self.execute(count_query)[0][0]
            
            # Get table size
            size_query = f"""
                SELECT 
                    formatReadableSize(sum(bytes)) as size,
                    sum(rows) as rows,
                    count() as partitions
                FROM system.parts
                WHERE database = '{self.database}' AND table = '{table_name}'
            """
            size_info = self.execute(size_query)[0]
            
            return {
                'table_name': table_name,
                'columns': columns,
                'row_count': row_count,
                'size': size_info[0],
                'partitions': size_info[2]
            }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise
    
    def get_distinct_values(
        self,
        column: str,
        table_name: str = 'sales_analytics',
        user_permissions: Dict[str, Any] = None
    ) -> List[str]:
        """
        Get distinct values for a column
        
        Args:
            column: Column name
            table_name: Table name
            user_permissions: User permissions (for RBAC)
            
        Returns:
            List of distinct values
        """
        query = f"""
            SELECT DISTINCT {column}
            FROM {table_name}
            WHERE {column} != ''
            ORDER BY {column}
        """
        
        if user_permissions:
            results = self.execute_with_rbac(query, user_permissions)
        else:
            results = self.execute(query)
        
        return [row[0] for row in results]
    
    def close(self):
        """Close connection to ClickHouse"""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from ClickHouse")


# ==================== USAGE EXAMPLES ====================

async def example_usage():
    """Example usage of ClickHouseClient"""
    
    # Initialize client
    ch = ClickHouseClient()
    
    # Test connection
    if not ch.test_connection():
        print("Failed to connect to ClickHouse")
        return
    
    # Example 1: Simple query
    print("\n=== Example 1: Total Sales by Business ===")
    query = """
        SELECT 
            business,
            sum(gsales) as total_sales,
            sum(fgp) as total_profit
        FROM sales_analytics
        GROUP BY business
        ORDER BY total_sales DESC
    """
    results = ch.execute_dict(query)
    for row in results:
        print(f"{row['business']}: €{row['total_sales']:,.2f} (Profit: €{row['total_profit']:,.2f})")
    
    # Example 2: Query with RBAC
    print("\n=== Example 2: Query with RBAC (Sales User) ===")
    user_permissions = {
        'role': 'sales',
        'businesses': ['Food'],
        'data_types': ['revenue']
    }
    
    results = ch.execute_dict_with_rbac(query, user_permissions)
    for row in results:
        print(f"{row['business']}: €{row['total_sales']:,.2f}")
    
    # Example 3: Get table info
    print("\n=== Example 3: Table Info ===")
    info = ch.get_table_info('sales_analytics')
    print(f"Table: {info['table_name']}")
    print(f"Rows: {info['row_count']:,}")
    print(f"Size: {info['size']}")
    print(f"Partitions: {info['partitions']}")
    
    # Example 4: Get distinct values
    print("\n=== Example 4: Distinct Businesses ===")
    businesses = ch.get_distinct_values('business')
    print(f"Businesses: {', '.join(businesses)}")
    
    # Close connection
    ch.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
