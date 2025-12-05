"""
Sync data from Azure Blob Storage to MongoDB Production Database
This script loads data from Biz-Pulse/yearly_data1.csv into bizpulse database (PRODUCTION)
⚠️ WARNING: This will DELETE all existing data in bizpulse.business_data collection
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import pandas as pd
from io import StringIO
from azure.storage.blob import BlobServiceClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def load_data_to_production_db():
    """
    Load data from Azure Blob Storage (yearly_data1.csv) into production database
    ⚠️ WARNING: This will replace all existing production data
    """
    # MongoDB connection - read database name from .env file
    MONGO_URL = os.getenv('MONGO_URL')
    DB_NAME = os.getenv('DB_NAME', 'bizpulse')  # Read from .env, default to 'bizpulse' if not set
    
    if not MONGO_URL:
        logger.error("❌ MONGO_URL not found in environment variables!")
        return
    
    logger.warning("=" * 70)
    logger.warning("⚠️  PRODUCTION DATABASE UPDATE")
    logger.warning("=" * 70)
    logger.warning(f"📊 Target Database: {DB_NAME} (from .env file)")
    logger.warning(f"⚠️  This will DELETE all existing data in {DB_NAME}.business_data")
    logger.warning("=" * 70)
    
    # Ask for confirmation (in production, you might want to add input confirmation)
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
    
    # Azure Blob Storage configuration
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name = os.getenv('AZURE_CONTAINER_NAME')
    # New file path: Biz-Pulse/yearly_data1.csv (with 2025 data)
    blob_path = os.getenv('AZURE_BLOB_PATH') or 'Biz-Pulse/yearly_data1.csv'
    
    if not conn_str or not container_name:
        logger.error("❌ Azure Storage configuration not found!")
        logger.error("   Required: AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME")
        return
    
    logger.info(f"📥 Downloading CSV from Azure...")
    logger.info(f"   Container: {container_name}")
    logger.info(f"   Blob Path: {blob_path}")
    
    try:
        blob_service = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_path)
        
        # Check if blob exists
        if not blob_client.exists():
            logger.error(f"❌ Blob not found: {blob_path}")
            logger.error(f"   Please verify the file exists in Azure container: {container_name}")
            return
        
        stream = blob_client.download_blob()
        csv_bytes = stream.readall()
        csv_text = csv_bytes.decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(csv_text))
        
        logger.info(f"✅ Downloaded {len(df)} records from Azure")
        logger.info(f"   Columns: {list(df.columns)[:10]}...")  # Show first 10 columns
        
    except Exception as e:
        logger.error(f"❌ Failed to download from Azure: {e}")
        return
    
    # Normalize column names (same as in server.py and sync_azure_data.py)
    rename_map = {
        'Month': 'Month_Name',
        'Month Name': 'Month_Name',
        'MonthName': 'Month_Name',
        'month_name': 'Month_Name',
        'Sub-Cat': 'Sub_Cat',
        'Sub_Category': 'Sub_Cat',
        'SubCat': 'Sub_Cat',
        'sub_cat': 'Sub_Cat',
        'Brand Type Name': 'Brand_Type_Name',
        'Brand_Type': 'Brand_Type_Name',
        'P+L Brand': 'PL_Brand',
        'PL Brand': 'PL_Brand',
        'P+L Category': 'PL_Category',
        'PL Category': 'PL_Category',
        'SubCat Name': 'SubCat_Name',
        'SKU Channel Name': 'SKU_Channel_Name',
        'P+L Cust. Grp': 'PL_Cust_Grp',
        'PL Cust Grp': 'PL_Cust_Grp',
        'gSales': 'Revenue',
        'fGP': 'Gross_Profit',
        'Cases': 'Units',
    }
    
    logger.info("🔄 Normalizing column names...")
    df = df.rename(columns=rename_map)
    
    # Ensure numeric columns - handle comma separators
    def clean_numeric_column(series):
        """Remove commas and convert to numeric"""
        if series.dtype == 'object':
            # Remove commas and convert
            return pd.to_numeric(series.astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return pd.to_numeric(series, errors='coerce').fillna(0)
    
    logger.info("🔢 Cleaning numeric columns...")
    for col in ['Gross_Profit', 'Revenue', 'Units', 'Year']:
        if col in df.columns:
            df[col] = clean_numeric_column(df[col])
        else:
            logger.warning(f"⚠️  Column '{col}' not found in CSV")
    
    # Verify required columns exist
    required_cols = ['Year', 'Month_Name']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ Required columns missing: {missing_cols}")
        logger.error(f"   Available columns: {list(df.columns)}")
        return
    
    # Convert to list of dicts
    records = df.to_dict(orient='records')
    
    # Clear old data and insert new
    logger.warning(f"🗑️  Clearing existing PRODUCTION data in {DB_NAME}.business_data...")
    delete_result = await db.business_data.delete_many({})
    logger.info(f"   Deleted {delete_result.deleted_count} existing records")
    
    logger.info(f"💾 Inserting {len(records)} new records into {DB_NAME} PRODUCTION database...")
    batch_size = 5000
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            await db.business_data.insert_many(batch)
            total += len(batch)
            logger.info(f"   ✅ Inserted {total}/{len(records)} records...")
        except Exception as e:
            logger.error(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            raise
    
    logger.info(f"\n🎉 Successfully loaded {total} records into {DB_NAME} PRODUCTION database!")
    
    # Verify data
    logger.info("\n📊 Verifying data...")
    count = await db.business_data.count_documents({})
    logger.info(f"   Total records in database: {count}")
    
    # Check year distribution
    pipeline = [
        {
            '$group': {
                '_id': '$Year',
                'count': {'$sum': 1},
                'total_revenue': {'$sum': {'$toDouble': '$Revenue'}},
                'total_units': {'$sum': {'$toDouble': '$Units'}}
            }
        },
        {'$sort': {'_id': 1}}
    ]
    
    year_stats = await db.business_data.aggregate(pipeline).to_list(100)
    logger.info("\n📈 Year Distribution:")
    for stat in year_stats:
        year = stat.get('_id', 'Unknown')
        count = stat.get('count', 0)
        revenue = stat.get('total_revenue', 0)
        units = stat.get('total_units', 0)
        logger.info(f"   {year}: {count:,} records, Revenue: €{revenue:,.0f}, Cases: {units:,.0f}")
    
    # Check 2025 data specifically
    count_2025 = await db.business_data.count_documents({'Year': 2025})
    if count_2025 > 0:
        logger.info(f"\n✅ Found {count_2025:,} records for year 2025 (new data)")
        
        # Check months in 2025
        month_pipeline = [
            {'$match': {'Year': 2025}},
            {'$group': {'_id': '$Month_Name', 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]
        month_stats = await db.business_data.aggregate(month_pipeline).to_list(100)
        months = [m['_id'] for m in month_stats if m.get('_id')]
        logger.info(f"   2025 Months: {months}")
    else:
        logger.warning("⚠️  No records found for year 2025")
    
    client.close()
    logger.info("\n✅ Production database update completed successfully!")
    logger.warning("=" * 70)
    logger.warning("⚠️  PRODUCTION DATABASE HAS BEEN UPDATED")
    logger.warning("=" * 70)

if __name__ == "__main__":
    # Load .env to get DB_NAME for display
    load_dotenv()
    db_name = os.getenv('DB_NAME', 'bizpulse')
    
    print("=" * 70)
    print(f"🚀 Azure Data Sync to PRODUCTION Database ({db_name})")
    print("=" * 70)
    print("⚠️  WARNING: This will update the PRODUCTION database!")
    print(f"   - Database: {db_name} (from .env file)")
    print("   - Source: Biz-Pulse/yearly_data1.csv (with 2025 data)")
    print("   - Action: DELETE all existing data and load new data")
    print("=" * 70)
    print()
    
    asyncio.run(load_data_to_production_db())

