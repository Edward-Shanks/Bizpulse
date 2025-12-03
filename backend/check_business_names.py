import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_business_names():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI', os.getenv('MONGO_URL', 'mongodb://localhost:27017')))
    db_name = os.getenv('MONGODB_DB_NAME', os.getenv('DB_NAME', 'thrivebrands'))
    db = client[db_name]
    
    # Get distinct business names
    businesses = await db.business_data.distinct('Business')
    
    print(f"Total distinct businesses: {len(businesses)}")
    print("\nBusiness names in database:")
    for b in sorted(set(businesses)):
        print(f"  '{b}'")
    
    # Check specifically for "Brillo, Goddards & KMPL"
    target = "Brillo, Goddards & KMPL"
    print(f"\n\nChecking for: '{target}'")
    count = await db.business_data.count_documents({"Business": target})
    print(f"Exact match count: {count}")
    
    # Check with regex (case-insensitive, flexible spacing)
    import re
    pattern = re.compile(r"brillo.*goddards.*kmpl", re.IGNORECASE)
    count_regex = await db.business_data.count_documents({"Business": {"$regex": pattern}})
    print(f"Regex match count: {count_regex}")
    
    # Check similar variations
    variations = [
        "Brillo, Goddards & KMPL",
        "Brillo, Goddards & KMPL ",
        "Brillo, Goddards & KMPL",
        "Brillo,Goddards & KMPL",
        "Brillo, Goddards & KMPL",
    ]
    for var in variations:
        count_var = await db.business_data.count_documents({"Business": var})
        if count_var > 0:
            print(f"  Found '{var}': {count_var} records")
    
    # Sample records with this business
    sample = await db.business_data.find_one({"Business": {"$regex": pattern}})
    if sample:
        print(f"\nSample record Business field: '{sample.get('Business')}'")
        print(f"  Year: {sample.get('Year')}")
        print(f"  Revenue: {sample.get('Revenue')}")

if __name__ == "__main__":
    asyncio.run(check_business_names())

