"""
Load Shopify Customer Data from CSV to MongoDB
This script loads data from Shopify_customer_df_new2.csv into bizpulse.shopify_data collection
⚠️ WARNING: This will DELETE all existing data in shopify_data collection
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ROOT_DIR = Path(__file__).parent

def clean_numeric_value(value):
    """Clean numeric values - handle strings, NaN, None"""
    if pd.isna(value) or value is None or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return 0.0
        return float(value)
    if isinstance(value, str):
        # Remove commas, currency symbols, etc.
        cleaned = value.replace(',', '').replace('€', '').replace('$', '').replace('£', '').strip()
        if cleaned == '' or cleaned.lower() in ['nan', 'none', 'null', '-']:
            return 0.0
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    return 0.0

async def load_shopify_data_to_mongodb():
    """
    Load Shopify customer data from CSV into MongoDB
    """
    # MongoDB connection - read database name from .env file
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')  # Read from .env, default to 'bizpulse'
    
    if not MONGO_URL:
        logger.error("❌ MONGO_URL not found in environment variables!")
        return
    
    logger.info("=" * 70)
    logger.info("📊 Loading Shopify Customer Data to MongoDB")
    logger.info("=" * 70)
    logger.info(f"📊 Target Database: {DB_NAME} (from .env file)")
    logger.info(f"📊 Collection: shopify_data")
    logger.info(f"⚠️  This will DELETE all existing data in {DB_NAME}.shopify_data")
    logger.info("=" * 70)
    
    # Connect to MongoDB
    logger.info(f"📊 Connecting to MongoDB database: {DB_NAME}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Test connection
    try:
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Load CSV file
    csv_path = ROOT_DIR / 'Shopify_customer_df_new2.csv'
    if not csv_path.exists():
        logger.error(f"❌ CSV file not found: {csv_path}")
        logger.error("   Please ensure Shopify_customer_df_new2.csv exists in the backend folder")
        return
    
    logger.info(f"📥 Loading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        logger.info(f"   Columns: {len(df.columns)} columns")
        logger.info(f"   Sample columns: {list(df.columns[:10])}")
    except Exception as e:
        logger.error(f"❌ Failed to load CSV: {e}")
        return
    
    if df.empty:
        logger.error("❌ CSV file is empty!")
        return
    
    # Clean numeric columns
    numeric_cols = [
        'Net sales', 'Gross sales', 'Total sales', 'Orders', 
        'Orders (first-time)', 'Orders (returning)', 
        'Quantity ordered', 'Customer number of orders',
        'Net returns', 'Total returns'
    ]
    
    logger.info("🧹 Cleaning numeric columns...")
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric_value)
    
    # Parse date columns (same logic as server.py)
    logger.info("📅 Parsing date columns...")
    if 'Month' in df.columns:
        df['Month_Column'] = df['Month'].copy()
    
    if 'Month_Column' in df.columns:
        month_col = df['Month_Column'].astype(str)
        valid_mask = month_col.notna() & (month_col != 'nan') & month_col.str.contains('-', na=False)
        
        if valid_mask.any():
            split_parts = month_col[valid_mask].str.split('-', expand=True)
            if len(split_parts.columns) >= 2:
                try:
                    df.loc[valid_mask, 'Year'] = pd.to_numeric(split_parts[0], errors='coerce')
                    df.loc[valid_mask, 'Month'] = pd.to_numeric(split_parts[1], errors='coerce')
                    valid_dates = df.loc[valid_mask, ['Year', 'Month']].dropna()
                    if not valid_dates.empty:
                        date_series = pd.to_datetime(valid_dates.assign(Day=1), errors='coerce')
                        df.loc[valid_dates.index, 'MonthName'] = date_series.dt.strftime('%B')
                except Exception as e:
                    logger.warning(f"Error in date parsing: {str(e)}")
    
    # Also parse Day column if available
    if 'Day' in df.columns:
        try:
            df['Day'] = pd.to_datetime(df['Day'], errors='coerce')
            missing_mask = df['Year'].isna() | df['Month'].isna()
            if missing_mask.any():
                df.loc[missing_mask & df['Day'].notna(), 'Year'] = df.loc[missing_mask & df['Day'].notna(), 'Day'].dt.year
                df.loc[missing_mask & df['Day'].notna(), 'Month'] = df.loc[missing_mask & df['Day'].notna(), 'Day'].dt.month
                df.loc[missing_mask & df['Day'].notna(), 'MonthName'] = df.loc[missing_mask & df['Day'].notna(), 'Day'].dt.strftime('%B')
        except Exception as e:
            logger.warning(f"Error processing Day column: {str(e)}")
    
    logger.info(f"✅ Date parsing complete. Valid Year/Month: {(df['Year'].notna() & df['Month'].notna()).sum()}/{len(df)}")
    
    # Convert DataFrame to list of dictionaries
    logger.info("🔄 Converting DataFrame to records...")
    records = df.to_dict('records')
    
    # Clean records - handle NaN, None, and ensure proper types
    logger.info("🧹 Cleaning records...")
    cleaned_records = []
    for record in records:
        cleaned = {}
        for key, value in record.items():
            # Handle NaN, None, empty strings
            if pd.isna(value) or value is None:
                cleaned[key] = None
            elif isinstance(value, (int, float)) and pd.isna(value):
                cleaned[key] = None
            elif isinstance(value, str) and value.strip() == '':
                cleaned[key] = None
            elif isinstance(value, pd.Timestamp):
                # Convert pandas Timestamp to ISO string
                cleaned[key] = value.isoformat() if pd.notna(value) else None
            elif key in ['Year', 'Month'] and pd.notna(value):
                # Ensure Year and Month are integers
                try:
                    cleaned[key] = int(float(value)) if pd.notna(value) else None
                except (ValueError, TypeError):
                    cleaned[key] = None
            else:
                cleaned[key] = value
        cleaned_records.append(cleaned)
    
    # Delete existing data
    logger.warning(f"🗑️  Clearing existing data in {DB_NAME}.shopify_data...")
    try:
        result = await db.shopify_data.delete_many({})
        logger.info(f"   Deleted {result.deleted_count} existing records")
    except Exception as e:
        logger.error(f"❌ Error deleting existing data: {e}")
        return
    
    # Insert new data in batches
    batch_size = 1000
    total = len(cleaned_records)
    logger.info(f"💾 Inserting {total} records into {DB_NAME}.shopify_data...")
    
    inserted_count = 0
    for i in range(0, total, batch_size):
        batch = cleaned_records[i:i + batch_size]
        try:
            result = await db.shopify_data.insert_many(batch, ordered=False)
            inserted_count += len(result.inserted_ids)
            logger.info(f"   Inserted batch {i//batch_size + 1}: {len(batch)} records (Total: {inserted_count}/{total})")
        except Exception as e:
            logger.error(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            # Continue with next batch
    
    logger.info("=" * 70)
    logger.info(f"🎉 Successfully loaded {inserted_count} records into {DB_NAME}.shopify_data!")
    logger.info("=" * 70)
    
    # Verify data
    logger.info("🔍 Verifying loaded data...")
    count = await db.shopify_data.count_documents({})
    logger.info(f"   Total records in MongoDB: {count:,}")
    
    if count != inserted_count:
        logger.warning(f"⚠️  Record count mismatch: Expected {inserted_count}, Found {count}")
    else:
        logger.info("✅ Record count matches!")
    
    # Show sample record
    sample = await db.shopify_data.find_one({})
    if sample:
        logger.info("📄 Sample record keys:")
        for key in list(sample.keys())[:10]:
            logger.info(f"   - {key}")
    
    # Close connection
    client.close()
    logger.info("✅ Data loading complete!")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Shopify Customer Data Loader")
    print("=" * 70)
    print("This script will:")
    print("  1. Load data from Shopify_customer_df_new2.csv")
    print("  2. Clean and normalize the data")
    print("  3. Delete existing data in shopify_data collection")
    print("  4. Insert all records into MongoDB")
    print("=" * 70 + "\n")
    
    asyncio.run(load_shopify_data_to_mongodb())

