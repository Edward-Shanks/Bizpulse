#!/usr/bin/env python3
"""
MongoDB to ClickHouse Migration Script
Migrates data from MongoDB business_data collection to ClickHouse sales_analytics table
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import clickhouse_driver
from datetime import datetime, date
import pandas as pd
from tqdm import tqdm
import sys

# ==================== CONFIGURATION ====================
MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DB = "bizpulse"
MONGODB_COLLECTION = "business_data"

CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_PORT = 9000
CLICKHOUSE_DB = "bizpulse"
CLICKHOUSE_TABLE = "sales_analytics"

BATCH_SIZE = 10000  # Insert 10K rows at a time

# ==================== HELPER FUNCTIONS ====================

def parse_date(date_value):
    """Parse date from various formats"""
    if isinstance(date_value, datetime):
        return date_value.date()
    elif isinstance(date_value, date):
        return date_value
    elif isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        except:
            return datetime.now().date()
    else:
        return datetime.now().date()

def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value) if value is not None else default
    except:
        return default

def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(value) if value is not None else default
    except:
        return default

def calculate_quarter(month):
    """Calculate quarter from month (1-12)"""
    return (month - 1) // 3 + 1

# ==================== MAIN MIGRATION ====================

async def migrate_data():
    """Main migration function"""
    
    print("=" * 70)
    print("🚀 BIZPULSE - MongoDB to ClickHouse Migration")
    print("=" * 70)
    
    # Connect to MongoDB
    print("\n📊 Connecting to MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    mongo_db = mongo_client[MONGODB_DB]
    
    # Count total documents
    total_docs = await mongo_db[MONGODB_COLLECTION].count_documents({})
    print(f"✅ Found {total_docs:,} documents in MongoDB")
    
    if total_docs == 0:
        print("\n⚠️  No documents found in MongoDB!")
        print(f"   Collection: {MONGODB_DB}.{MONGODB_COLLECTION}")
        print("   Please check your MongoDB data.")
        return
    
    # Connect to ClickHouse
    print("\n🗄️  Connecting to ClickHouse...")
    try:
        ch_client = clickhouse_driver.Client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            database=CLICKHOUSE_DB
        )
    except Exception as e:
        print(f"\n❌ Error connecting to ClickHouse: {e}")
        print("   Make sure ClickHouse is running:")
        print("   docker ps | grep clickhouse")
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
    if (CLICKHOUSE_TABLE,) not in tables:
        print(f"\n❌ Table {CLICKHOUSE_TABLE} does not exist!")
        print(f"   Please create it first:")
        print(f"   Run: docker exec -it clickhouse-prod clickhouse-client --database={CLICKHOUSE_DB}")
        print(f"   Then paste the CREATE TABLE statement from create_schema.sql")
        return
    
    # Check current row count
    current_count = ch_client.execute(f'SELECT count() FROM {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE}')[0][0]
    if current_count > 0:
        print(f"\n⚠️  Table already has {current_count:,} rows!")
        response = input("   Do you want to append data? (yes/no): ")
        if response.lower() != 'yes':
            print("   Migration cancelled.")
            return
    
    # Start migration
    print(f"\n🔄 Starting migration...")
    print(f"   Batch size: {BATCH_SIZE:,}")
    print(f"   Target table: {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE}")
    
    cursor = mongo_db[MONGODB_COLLECTION].find({})
    batch = []
    total_migrated = 0
    errors = 0
    
    # Progress bar
    with tqdm(total=total_docs, desc="Migrating", unit="docs") as pbar:
        async for doc in cursor:
            # Transform document to ClickHouse format
            try:
                # Parse date
                doc_date = parse_date(doc.get('date') or doc.get('Date'))
                year = safe_int(doc.get('Year') or doc.get('year') or doc_date.year)
                month = safe_int(doc.get('Month') or doc.get('month') or doc_date.month)
                
                # Month name
                month_names = ["", "January", "February", "March", "April", "May", 
                             "June", "July", "August", "September", "October", 
                             "November", "December"]
                month_name = doc.get('Month_Name') or (month_names[month] if 1 <= month <= 12 else "Unknown")
                
                row = (
                    doc_date,
                    year,
                    month,
                    month_name,
                    calculate_quarter(month),
                    
                    # Business dimensions
                    str(doc.get('Business') or 'Unknown'),
                    str(doc.get('Channel') or 'Unknown'),
                    str(doc.get('Brand') or 'Unknown'),
                    str(doc.get('Category') or 'Unknown'),
                    str(doc.get('Sub_Category') or 'Unknown'),
                    str(doc.get('Customer') or 'Unknown'),
                    str(doc.get('SKU') or 'Unknown'),
                    
                    # Metrics
                    safe_float(doc.get('Revenue') or doc.get('gSales') or doc.get('Gross_Sales')),
                    safe_float(doc.get('Units') or doc.get('Cases')),
                    safe_float(doc.get('Gross_Profit') or doc.get('fGP')),
                    safe_float(doc.get('Price_Downs')),
                    safe_float(doc.get('Perm_Disc')),
                    safe_float(doc.get('Group_Cost')),
                    safe_float(doc.get('LTA')),
                    safe_float(doc.get('Transfer_Cost')),
                    
                    # Metadata
                    datetime.now(),
                    datetime.now()
                )
                
                batch.append(row)
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only show first 5 errors
                    print(f"\n⚠️  Error processing document: {e}")
                continue
            
            # Insert batch when full
            if len(batch) >= BATCH_SIZE:
                try:
                    ch_client.execute(
                        f'INSERT INTO {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE} VALUES',
                        batch
                    )
                    total_migrated += len(batch)
                    pbar.update(len(batch))
                    batch = []
                except Exception as e:
                    print(f"\n❌ Error inserting batch: {e}")
                    batch = []
    
    # Insert remaining rows
    if batch:
        try:
            ch_client.execute(
                f'INSERT INTO {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE} VALUES',
                batch
            )
            total_migrated += len(batch)
            pbar.update(len(batch))
        except Exception as e:
            print(f"\n❌ Error inserting final batch: {e}")
    
    # Verify migration
    print("\n📊 Verifying migration...")
    count = ch_client.execute(f'SELECT count() FROM {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE}')[0][0]
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print(f"   MongoDB documents:  {total_docs:,}")
    print(f"   Migrated rows:      {total_migrated:,}")
    print(f"   ClickHouse count:   {count:,}")
    print(f"   Errors encountered: {errors}")
    
    if errors > 0:
        print(f"   ⚠️  {errors} documents had errors and were skipped")
    
    if count < total_migrated:
        print(f"   ⚠️  Warning: ClickHouse count is less than migrated count!")
    else:
        print(f"   ✅ Data verified successfully!")
    
    # Show sample data
    print("\n📊 Sample data (first 5 rows):")
    sample = ch_client.execute(f'SELECT date, business, channel, gsales, fgp FROM {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE} LIMIT 5')
    for i, row in enumerate(sample, 1):
        print(f"   {i}. Date: {row[0]}, Business: {row[1]}, Channel: {row[2]}, Sales: €{row[3]}, Profit: €{row[4]}")
    
    # Show statistics
    print("\n📊 Data Statistics:")
    stats = ch_client.execute(f'''
        SELECT 
            count() as total_rows,
            countDistinct(business) as businesses,
            countDistinct(channel) as channels,
            countDistinct(brand) as brands,
            countDistinct(customer) as customers,
            sum(gsales) as total_sales,
            sum(fgp) as total_profit
        FROM {CLICKHOUSE_DB}.{CLICKHOUSE_TABLE}
    ''')[0]
    
    print(f"   Total Rows:      {stats[0]:,}")
    print(f"   Businesses:      {stats[1]}")
    print(f"   Channels:        {stats[2]}")
    print(f"   Brands:          {stats[3]}")
    print(f"   Customers:       {stats[4]}")
    print(f"   Total Sales:     €{stats[5]:,.2f}")
    print(f"   Total Profit:    €{stats[6]:,.2f}")
    
    print("\n" + "=" * 70)
    print("🎉 Migration successful! You can now query your data in ClickHouse.")
    print("=" * 70)

# ==================== RUN MIGRATION ====================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("BIZPULSE - MongoDB to ClickHouse Migration Script")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Connect to your MongoDB database")
    print("2. Read all documents from business_data collection")
    print("3. Transform and insert them into ClickHouse")
    print("\nPress Ctrl+C to cancel...")
    print("=" * 70 + "\n")
    
    try:
        asyncio.run(migrate_data())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
