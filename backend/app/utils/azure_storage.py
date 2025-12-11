"""
Azure Blob Storage utilities
Handles CSV file downloads from Azure Blob Storage
"""
import pandas as pd
from io import StringIO
from azure.storage.blob import BlobServiceClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def load_data_from_azure_blob() -> int:
    """
    Load CSV data from Azure Blob Storage and return count of records loaded
    Returns 0 if Azure config is not set or if loading fails
    """
    if not (settings.AZURE_CONNECTION_STRING and settings.AZURE_CONTAINER_NAME and settings.AZURE_BLOB_PATH):
        logger.warning("Azure Blob config not set. Skipping Azure sync.")
        return 0
    
    try:
        logger.info(f"Downloading CSV from Azure: container={settings.AZURE_CONTAINER_NAME}, path={settings.AZURE_BLOB_PATH}")
        blob_service = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
        container_client = blob_service.get_container_client(settings.AZURE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(settings.AZURE_BLOB_PATH)
        stream = blob_client.download_blob()
        csv_bytes = stream.readall()
        csv_text = csv_bytes.decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(csv_text))
        
        # Normalize column names to expected schema
        rename_map = {
            'Month': 'Month_Name',
            'MonthName': 'Month_Name',
            'month_name': 'Month_Name',
            'Sub_Category': 'Sub_Cat',
            'SubCat': 'Sub_Cat',
            'sub_cat': 'Sub_Cat',
            'Brand_Type': 'Brand_Type_Name',
            'PL Brand': 'PL_Brand',
            'PL Category': 'PL_Category',
            'SKU Channel Name': 'SKU_Channel_Name',
            'PL Cust Grp': 'PL_Cust_Grp',
            'gSales': 'Revenue',
            'fGP': 'Gross_Profit',
            'Cases': 'Units',
        }
        df = df.rename(columns=rename_map)
        
        # Ensure required columns exist
        required = ['Year', 'Month_Name']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Required column missing in CSV: {col}")
        
        # Coerce numeric columns used downstream
        for col in ['Gross_Profit', 'Revenue', 'Units', 'Year']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert to list of dicts
        records = df.to_dict(orient='records')
        if not records:
            logger.warning("Azure CSV contained no records.")
            return 0
        
        return records
    except Exception as e:
        logger.error(f"Azure sync failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0



