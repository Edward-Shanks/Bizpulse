"""
Check if the new Azure file exists and show its structure
"""
import os
from dotenv import load_dotenv
import pandas as pd
from io import StringIO
from azure.storage.blob import BlobServiceClient

load_dotenv()

print("=" * 60)
print("🔍 Checking Azure Blob Storage for yearly_data1.csv")
print("=" * 60)
print()

# Azure configuration
conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
container_name = os.getenv('AZURE_CONTAINER_NAME')
blob_path = os.getenv('AZURE_BLOB_PATH_DEV') or 'Biz-Pulse/yearly_data1.csv'

if not conn_str or not container_name:
    print("❌ Azure Storage configuration not found!")
    print("   Required: AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME")
    exit(1)

print(f"📥 Checking Azure Blob Storage...")
print(f"   Container: {container_name}")
print(f"   Blob Path: {blob_path}")
print()

try:
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_path)
    
    # Check if blob exists
    if not blob_client.exists():
        print(f"❌ File NOT FOUND: {blob_path}")
        print()
        print("📋 Available files in container (first 20):")
        blobs = container_client.list_blobs(name_starts_with='Biz-Pulse/')
        count = 0
        for blob in blobs:
            print(f"   • {blob.name}")
            count += 1
            if count >= 20:
                break
        if count == 0:
            print("   (No files found in Biz-Pulse/ folder)")
        exit(1)
    
    print(f"✅ File FOUND: {blob_path}")
    print()
    
    # Get file properties
    properties = blob_client.get_blob_properties()
    size_mb = properties.size / (1024 * 1024)
    print(f"📊 File Properties:")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Last Modified: {properties.last_modified}")
    print()
    
    # Download and check structure
    print("📥 Downloading file to check structure...")
    stream = blob_client.download_blob()
    csv_bytes = stream.readall()
    csv_text = csv_bytes.decode('utf-8', errors='ignore')
    df = pd.read_csv(StringIO(csv_text))
    
    print(f"✅ Downloaded {len(df)} records")
    print()
    
    # Show columns
    print("📋 COLUMNS IN CSV:")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2d}. {col}")
    print()
    
    # Show data types
    print("📊 DATA TYPES:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        print(f"   {col}: {dtype}")
    print()
    
    # Show unique years
    if 'Year' in df.columns:
        years = sorted(df['Year'].dropna().unique())
        print(f"📅 YEARS IN DATA: {years}")
        print()
        
        # Check 2025 data
        if 2025 in years:
            df_2025 = df[df['Year'] == 2025]
            print(f"✅ 2025 DATA FOUND: {len(df_2025)} records")
            
            # Check months in 2025
            if 'Month' in df.columns or 'Month Name' in df.columns or 'MonthName' in df.columns:
                month_col = 'Month' if 'Month' in df.columns else ('Month Name' if 'Month Name' in df.columns else 'MonthName')
                months_2025 = sorted(df_2025[month_col].dropna().unique())
                print(f"   Months in 2025: {months_2025}")
        else:
            print("⚠️  No 2025 data found in CSV")
        print()
    
    # Show sample records
    print("📄 SAMPLE RECORDS (first 3):")
    print(df.head(3).to_string())
    print()
    
    # Show summary statistics
    numeric_cols = ['gSales', 'Revenue', 'fGP', 'Gross_Profit', 'Cases', 'Units']
    for col in numeric_cols:
        if col in df.columns:
            try:
                col_data = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                print(f"💰 {col} Summary:")
                print(f"   Total: {col_data.sum():,.2f}")
                print(f"   Mean: {col_data.mean():,.2f}")
                print(f"   Records: {col_data.notna().sum():,}")
                print()
            except:
                pass
    
    print("=" * 60)
    print("✅ File check completed successfully!")
    print("=" * 60)
    print()
    print("💡 Next step: Run 'python sync_azure_data_dev.py' to load data into bizpulseDev")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

