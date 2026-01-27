"""
Quick script to check what filter values exist in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def check_data():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.bizpulse
    collection = db.business_data
    
    print("\n=== Checking Database Structure ===\n")
    
    # Get sample document
    sample = await collection.find_one()
    if sample:
        print("Sample document fields:")
        for key in sample.keys():
            print(f"  - {key}: {sample[key]}")
    
    print("\n=== Unique Values in Key Fields ===\n")
    
    # Check unique years
    years = await collection.distinct("Year")
    print(f"Years: {sorted(years)}")
    
    # Check unique months
    months = await collection.distinct("Month")
    print(f"Months: {months}")
    
    # Check unique month names
    month_names = await collection.distinct("Month_Name")
    print(f"Month Names: {month_names}")
    
    # Check unique businesses
    businesses = await collection.distinct("Business")
    print(f"\nBusinesses ({len(businesses)}):")
    for b in sorted(businesses)[:10]:  # Show first 10
        print(f"  - {b}")
    
    # Check unique brands
    brands = await collection.distinct("Brand")
    print(f"\nBrands ({len(brands)}):")
    for b in sorted(brands)[:10]:  # Show first 10
        print(f"  - {b}")
    
    # Check unique channels
    channels = await collection.distinct("Channel")
    print(f"\nChannels: {sorted(channels)}")
    
    # Check unique categories
    categories = await collection.distinct("Category")
    print(f"\nCategories ({len(categories)}):")
    for c in sorted(categories)[:10]:  # Show first 10
        print(f"  - {c}")
    
    # Test a specific filter combination
    print("\n=== Testing Filter: Year=2023, Business=Brillo, Goddards & KMPL ===\n")
    test_query = {
        'Year': 2023,
        'Business': 'Brillo, Goddards & KMPL'
    }
    count = await collection.count_documents(test_query)
    print(f"Documents found: {count}")
    
    if count > 0:
        sample = await collection.find_one(test_query)
        print(f"Sample document:")
        print(f"  Month: {sample.get('Month')}")
        print(f"  Month_Name: {sample.get('Month_Name')}")
        print(f"  Brand: {sample.get('Brand')}")
        print(f"  Channel: {sample.get('Channel')}")
        print(f"  Category: {sample.get('Category')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_data())
