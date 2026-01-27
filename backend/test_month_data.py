"""
Diagnostic script to check what month data exists in database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def check_month_data():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.bizpulse
    collection = db.business_data
    
    print("\n=== Checking Month Data ===\n")
    
    # Get sample document
    sample = await collection.find_one({'Year': 2024})
    if sample:
        print("Sample 2024 document:")
        print(f"  Month field: {sample.get('Month')} (type: {type(sample.get('Month'))})")
        print(f"  Month_Name field: {sample.get('Month_Name')} (type: {type(sample.get('Month_Name'))})")
        print(f"  Year: {sample.get('Year')}")
        print(f"  Business: {sample.get('Business')}")
    
    # Check unique months for 2024
    print("\n=== Months in 2024 (Month field) ===")
    months_2024 = await collection.distinct("Month", {'Year': 2024})
    print(f"Unique Month values: {sorted(months_2024)}")
    
    print("\n=== Month_Name in 2024 (Month_Name field) ===")
    month_names_2024 = await collection.distinct("Month_Name", {'Year': 2024})
    print(f"Unique Month_Name values: {sorted(month_names_2024)}")
    
    # Count documents by month for 2024
    print("\n=== Document counts by Month_Name for 2024 ===")
    pipeline = [
        {'$match': {'Year': 2024}},
        {'$group': {'_id': '$Month_Name', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ]
    results = await collection.aggregate(pipeline).to_list(length=None)
    for r in results:
        print(f"  {r['_id']}: {r['count']} documents")
    
    # Test specific query
    print("\n=== Testing Query: Year=2024, Month_Name='March' ===")
    count = await collection.count_documents({'Year': 2024, 'Month_Name': 'March'})
    print(f"Found: {count} documents")
    
    print("\n=== Testing Query: Year=2024, Month_Name='march' (lowercase) ===")
    count = await collection.count_documents({'Year': 2024, 'Month_Name': 'march'})
    print(f"Found: {count} documents")
    
    print("\n=== Testing Query: Year=2024, Month='Mar' ===")
    count = await collection.count_documents({'Year': 2024, 'Month': 'Mar'})
    print(f"Found: {count} documents")
    
    print("\n=== Testing Query: Year=2024, Month=3 (number) ===")
    count = await collection.count_documents({'Year': 2024, 'Month': 3})
    print(f"Found: {count} documents")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_month_data())
