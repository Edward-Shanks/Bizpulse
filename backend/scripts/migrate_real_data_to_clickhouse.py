#!/usr/bin/env python3
"""
REAL DATA Migration: MongoDB business_data → ClickHouse sales_analytics
This script migrates your ACTUAL business data with proper column mapping

IMPORTANT NOTES:
- This script supports FULL mode (clear and reload) and INCREMENTAL mode (add new data)
- INCREMENTAL mode will ADD rows - it does NOT perform true UPSERT (no deduplication)
- If you need deduplication, use ReplacingMergeTree engine or implement deduplication logic
- MergeTree engine does NOT support UPSERT - duplicates will accumulate
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import clickhouse_driver
from datetime import datetime, date
import pandas as pd
from tqdm import tqdm
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================
# MongoDB (LOCAL on Laptop)
MONGODB_URI = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
MONGODB_DB = os.getenv('DB_NAME', 'bizpulse')
MONGODB_COLLECTION = "business_data"  # Your actual business data

# ClickHouse (REMOTE on Mac Studio)
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', '192.168.50.29')  # Mac Studio IP
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 9000))
CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'bizpulse')
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'bizpulse_admin')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', 'Admin@123!Secure')

# Multi-tenant configuration
TENANT_ID = os.getenv('TENANT_ID', 'client_001')  # Default tenant ID

BATCH_SIZE = 10000  # Insert 10K rows at a time

# ==================== HELPER FUNCTIONS ====================

def parse_date(year_val, month_name_val):
    """Parse date from Year and Month_Name"""
    try:
        if pd.isna(year_val) or pd.isna(month_name_val):
            return None
        
        year = int(year_val)
        
        # Convert month name to number
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month_name = str(month_name_val).strip()
        month = month_map.get(month_name)
        
        if not month:
            return None
        
        return date(year, month, 1)
    except:
        return None

def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return float(value)
    except:
        return default

def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return int(value)
    except:
        return default

def safe_string(value, default='Unknown'):
    """Safely convert to string"""
    if value is None or (isinstance(value, float) and pd.isna(value)) or value == '':
        return default
    return str(value).strip()

def calculate_quarter(month):
    """Calculate quarter from month (1-12)"""
    if month is None or month == 0:
        return 1
    return (month - 1) // 3 + 1

# ==================== MAIN MIGRATION ====================

async def migrate_data(mode='full'):
    """
    Main migration function
    
    Args:
        mode: 'full' = clear and reload all data
              'incremental' = only add/update new data
    """
    
    print("=" * 70)
    print("🚀 BIZPULSE - REAL DATA Migration (MongoDB → ClickHouse)")
    print("=" * 70)
    print(f"Mode: {mode.upper()}")
    print("=" * 70)
    
    # Connect to MongoDB
    print("\n📊 Connecting to MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    mongo_db = mongo_client[MONGODB_DB]
    
    # Count total documents
    total_docs = await mongo_db[MONGODB_COLLECTION].count_documents({})
    print(f"✅ Found {total_docs:,} documents in MongoDB.{MONGODB_COLLECTION}")
    
    if total_docs == 0:
        print("\n⚠️  No documents found in MongoDB!")
        print(f"   Collection: {MONGODB_DB}.{MONGODB_COLLECTION}")
        print("   Please check your MongoDB data.")
        return
    
    # Connect to ClickHouse
    print(f"\n🗄️  Connecting to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}...")
    try:
        ch_client = clickhouse_driver.Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            database=CLICKHOUSE_DB,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD
        )
    except Exception as e:
        print(f"\n❌ Error connecting to ClickHouse: {e}")
        print("   Make sure ClickHouse is running on Mac Studio")
        print(f"   Try: ssh {CLICKHOUSE_USER}@{CLICKHOUSE_HOST} 'docker ps | grep clickhouse'")
        return
    
    # Verify connection
    try:
        version = ch_client.execute('SELECT version()')[0][0]
        print(f"✅ Connected to ClickHouse {version}")
    except Exception as e:
        print(f"\n❌ Error verifying ClickHouse connection: {e}")
        return
    
    # Check if table exists
    tables = ch_client.execute(f'SHOW TABLES FROM {CLICKHOUSE_DB}')
    if ('sales_analytics',) not in tables:
        print(f"\n❌ Table {CLICKHOUSE_DB}.sales_analytics does not exist!")
        print(f"   Please create it first using create_schema.sql")
        return
    
    # Check current row count
    current_count = ch_client.execute(f'SELECT count() FROM {CLICKHOUSE_DB}.sales_analytics')[0][0]
    print(f"   Current rows in ClickHouse: {current_count:,}")
    
    # Handle mode
    if mode == 'full' and current_count > 0:
        response = input(f"\n⚠️  Table has {current_count:,} rows. Clear and reload? (yes/no): ")
        if response.lower() == 'yes':
            print("🗑️  Truncating table...")
            ch_client.execute(f'TRUNCATE TABLE {CLICKHOUSE_DB}.sales_analytics')
            print("✅ Table cleared")
        else:
            print("   Switching to incremental mode...")
            mode = 'incremental'
    
    # Start migration
    print(f"\n🔄 Starting {mode} migration...")
    print(f"   Batch size: {BATCH_SIZE:,}")
    print(f"   Source: MongoDB.{MONGODB_DB}.{MONGODB_COLLECTION}")
    print(f"   Target: ClickHouse.{CLICKHOUSE_DB}.sales_analytics")
    
    # Sample one document to show column mapping
    sample = await mongo_db[MONGODB_COLLECTION].find_one({})
    if sample:
        print("\n📋 Column Mapping (MongoDB → ClickHouse):")
        print(f"   Year → year: {sample.get('Year')}")
        print(f"   Month_Name → month_name: {sample.get('Month_Name')}")
        print(f"   Business → business: {sample.get('Business')}")
        print(f"   Channel → channel: {sample.get('Channel')}")
        print(f"   Brand → brand: {sample.get('Brand')}")
        print(f"   Category → category: {sample.get('Category')}")
        print(f"   Sub_Cat → sub_category: {sample.get('Sub_Cat')}")
        print(f"   Customer → customer: {sample.get('Customer')}")
        print(f"   Revenue → gsales: {sample.get('Revenue')}")
        print(f"   Gross_Profit → fgp: {sample.get('Gross_Profit')}")
        print(f"   Units → cases: {sample.get('Units')}")
    
    cursor = mongo_db[MONGODB_COLLECTION].find({})
    batch = []
    total_migrated = 0
    errors = 0
    skipped = 0
    
    # Progress bar
    with tqdm(total=total_docs, desc="Migrating", unit="docs") as pbar:
        async for doc in cursor:
            # Transform document to ClickHouse format
            try:
                # Extract values from MongoDB document
                year = safe_int(doc.get('Year'))
                month_name_raw = safe_string(doc.get('Month_Name'), 'Unknown')
                
                # Calculate month number from month name
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12,
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                    'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                month = month_map.get(month_name_raw, 1)
                
                # Parse date
                doc_date = parse_date(year, month_name_raw)
                if not doc_date:
                    # Skip if date is invalid
                    skipped += 1
                    pbar.update(1)
                    continue
                
                # Normalize month_name to full month name (January, February, etc.)
                # ClickHouse doesn't support %B in formatDateTime, so we calculate it in Python
                full_month_names = {
                    'January': 'January', 'February': 'February', 'March': 'March', 'April': 'April',
                    'May': 'May', 'June': 'June', 'July': 'July', 'August': 'August',
                    'September': 'September', 'October': 'October', 'November': 'November', 'December': 'December',
                    'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
                    'Jun': 'June', 'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                    'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
                }
                month_name = full_month_names.get(month_name_raw, 'January')  # Default to January if unknown
                
                # Build row matching new schema order:
                # tenant_id, date, month_name, business, channel, customer, brand, category, sub_category, sku,
                # cases, gsales, price_downs, perm_disc, transfer_cost, group_cost, lta, fgp
                # Note: year, month, quarter, year_month are MATERIALIZED (auto-calculated from date)
                # month_name is now a regular column (calculated in Python)
                # created_at has DEFAULT now() so we skip it - ClickHouse will auto-populate
                row = (
                    # Multi-tenant
                    TENANT_ID,
                    
                    # Time (date + month_name - others are MATERIALIZED)
                    doc_date,
                    month_name,  # Insert month_name directly (not MATERIALIZED anymore)
                    
                    # Business dimensions (matching ORDER BY order)
                    safe_string(doc.get('Business'), 'Unknown'),
                    safe_string(doc.get('Channel'), 'Unknown'),
                    safe_string(doc.get('Customer'), 'Unknown'),
                    safe_string(doc.get('Brand'), 'Unknown'),
                    safe_string(doc.get('Category'), 'Unknown'),
                    safe_string(doc.get('Sub_Cat') or doc.get('Sub_Category'), 'Unknown'),
                    safe_string(doc.get('SKU') or doc.get('Product'), 'Unknown'),
                    
                    # Metrics (matching schema order)
                    safe_float(doc.get('Units') or doc.get('Cases'), 0.0),      # cases
                    safe_float(doc.get('Revenue') or doc.get('gSales'), 0.0),   # gsales
                    safe_float(doc.get('Price_Downs'), 0.0),                     # price_downs
                    safe_float(doc.get('Perm_Disc'), 0.0),                       # perm_disc
                    safe_float(doc.get('Transfer_Cost'), 0.0),                   # transfer_cost
                    safe_float(doc.get('Group_Cost'), 0.0),                      # group_cost
                    safe_float(doc.get('LTA'), 0.0),                             # lta
                    safe_float(doc.get('Gross_Profit') or doc.get('fGP'), 0.0)  # fgp
                    # created_at skipped - ClickHouse will use DEFAULT now()
                )
                
                batch.append(row)
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only show first 5 errors
                    print(f"\n⚠️  Error processing document: {e}")
                pbar.update(1)
                continue
            
            # Insert batch when full
            if len(batch) >= BATCH_SIZE:
                try:
                    # CRITICAL: Use explicit column names for safety
                    # This prevents data corruption if schema changes
                    # Note: created_at has DEFAULT now() so we skip it - ClickHouse will auto-populate
                    insert_query = f"""
                    INSERT INTO {CLICKHOUSE_DB}.sales_analytics (
                        tenant_id,
                        date,
                        month_name,
                        business,
                        channel,
                        customer,
                        brand,
                        category,
                        sub_category,
                        sku,
                        cases,
                        gsales,
                        price_downs,
                        perm_disc,
                        transfer_cost,
                        group_cost,
                        lta,
                        fgp
                    ) VALUES
                    """
                    ch_client.execute(insert_query, batch)
                    total_migrated += len(batch)
                    pbar.update(len(batch))
                    batch = []
                except Exception as e:
                    print(f"\n❌ Error inserting batch: {e}")
                    batch = []
    
    # Insert remaining rows
    if batch:
        try:
            # CRITICAL: Use explicit column names
            # Note: created_at has DEFAULT now() so we skip it - ClickHouse will auto-populate
            insert_query = f"""
            INSERT INTO {CLICKHOUSE_DB}.sales_analytics (
                tenant_id,
                date,
                month_name,
                business,
                channel,
                customer,
                brand,
                category,
                sub_category,
                sku,
                cases,
                gsales,
                price_downs,
                perm_disc,
                transfer_cost,
                group_cost,
                lta,
                fgp
            ) VALUES
            """
            ch_client.execute(insert_query, batch)
            total_migrated += len(batch)
            pbar.update(len(batch))
        except Exception as e:
            print(f"\n❌ Error inserting final batch: {e}")
    
    # Verify migration
    print("\n📊 Verifying migration...")
    count = ch_client.execute(f'SELECT count() FROM {CLICKHOUSE_DB}.sales_analytics')[0][0]
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print(f"   MongoDB documents:  {total_docs:,}")
    print(f"   Migrated rows:      {total_migrated:,}")
    print(f"   ClickHouse count:   {count:,}")
    print(f"   Errors encountered: {errors}")
    print(f"   Skipped (no date):  {skipped}")
    
    if errors > 0:
        print(f"   ⚠️  {errors} documents had errors and were skipped")
    
    if skipped > 0:
        print(f"   ⚠️  {skipped} documents skipped (invalid date)")
    
    # Show statistics
    print("\n📊 Data Statistics:")
    stats = ch_client.execute(f'''
        SELECT 
            count() as total_rows,
            countDistinct(business) as businesses,
            countDistinct(channel) as channels,
            countDistinct(brand) as brands,
            countDistinct(customer) as customers,
            countDistinct(category) as categories,
            sum(gsales) as total_sales,
            sum(fgp) as total_profit
        FROM {CLICKHOUSE_DB}.sales_analytics
    ''')[0]
    
    print(f"   Total Rows:      {stats[0]:,}")
    print(f"   Businesses:      {stats[1]}")
    print(f"   Channels:        {stats[2]}")
    print(f"   Brands:          {stats[3]}")
    print(f"   Customers:       {stats[4]}")
    print(f"   Categories:      {stats[5]}")
    print(f"   Total Sales:     €{stats[6]:,.2f}")
    print(f"   Total Profit:    €{stats[7]:,.2f}")
    
    # Show sample by business
    print("\n📊 Sample Data by Business:")
    business_stats = ch_client.execute(f'''
        SELECT 
            business,
            count() as rows,
            sum(gsales) as total_sales
        FROM {CLICKHOUSE_DB}.sales_analytics
        GROUP BY business
        ORDER BY total_sales DESC
        LIMIT 10
    ''')
    
    for business, rows, sales in business_stats:
        print(f"   {business:20s}: {rows:8,} rows, €{sales:12,.2f}")
    
    print("\n" + "=" * 70)
    print("🎉 Your REAL data is now in ClickHouse!")
    print("=" * 70)
    
    # Close connection
    mongo_client.close()

# ==================== RUN MIGRATION ====================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("BIZPULSE - REAL DATA Migration Script")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Connect to your MongoDB business_data collection")
    print("2. Read all real business data")
    print("3. Map columns to ClickHouse schema")
    print("4. Insert into ClickHouse sales_analytics table")
    print("\nMake sure:")
    print("  ✓ Mac Studio ClickHouse is running")
    print("  ✓ .env file has correct Mac Studio IP")
    print("  ✓ sales_analytics table is created")
    print("=" * 70 + "\n")
    
    mode = 'full'  # Change to 'incremental' for updates only
    
    try:
        asyncio.run(migrate_data(mode))
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
