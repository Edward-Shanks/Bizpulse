"""
Quick script to check MongoDB data structure for reports
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client.bizpulse

# Get a sample document
sample = db.business_data.find_one()

if sample:
    print("="*50)
    print("Sample Document Fields:")
    print("="*50)
    for key in sample.keys():
        print(f"  {key}: {sample[key]}")
    
    print("\n" + "="*50)
    print("Testing Filter Query:")
    print("="*50)
    
    # Test query with actual values from sample
    test_query = {
        'Year': sample.get('Year'),
        'Business': sample.get('Business')
    }
    print(f"Test query: {test_query}")
    
    count = db.business_data.count_documents(test_query)
    print(f"Documents matching query: {count}")
    
    # Check unique values for key fields
    print("\n" + "="*50)
    print("Unique Values Sample:")
    print("="*50)
    print(f"Years: {db.business_data.distinct('Year')[:5]}")
    print(f"Businesses: {db.business_data.distinct('Business')[:5]}")
    print(f"Brands: {db.business_data.distinct('Brand')[:5]}")
    print(f"Channels: {db.business_data.distinct('Channel')[:5]}")
    print(f"Categories: {db.business_data.distinct('Category')[:5]}")
else:
    print("No data found in business_data collection!")

client.close()
