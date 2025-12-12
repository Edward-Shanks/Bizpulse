import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import sys

# Configure encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def test_brand_counts():
    """Test brand counts for specific periods"""
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    print("="*60)
    print("Brand Count Analysis")
    print("="*60)
    
    test_cases = [
        {"year": 2023, "month": "March", "expected": 34},
        {"year": 2023, "month": "Mar", "expected": 34},
        {"year": 2023, "month": "June", "expected": 33},
        {"year": 2023, "month": "Jun", "expected": 33},
        {"year": 2024, "month": None, "expected": 33},
        {"year": 2024, "month": "January", "expected": 31},
        {"year": 2024, "month": "Jan", "expected": 31},
    ]
    
    for test_case in test_cases:
        year = test_case["year"]
        month = test_case["month"]
        expected = test_case["expected"]
        
        print(f"\n📊 Testing: Year {year}" + (f", Month {month}" if month else ""))
        print("-" * 60)
        
        # Build query - try both full month name and abbreviation
        query = {"Year": year}
        if month:
            # Try to match month name (case-insensitive)
            month_variations = [month]
            if month == "March":
                month_variations.extend(["Mar", "march", "MARCH"])
            elif month == "June":
                month_variations.extend(["Jun", "june", "JUNE"])
            elif month == "January":
                month_variations.extend(["Jan", "january", "JANUARY"])
            elif month == "Mar":
                month_variations.extend(["March", "march", "MARCH"])
            elif month == "Jun":
                month_variations.extend(["June", "june", "JUNE"])
            elif month == "Jan":
                month_variations.extend(["January", "january", "JANUARY"])
            
            query["Month_Name"] = {"$in": month_variations}
        
        # Count all distinct brands (including those with 0 revenue)
        pipeline_all_brands = [
            {"$match": query},
            {"$match": {"Brand": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None"]}}},
            {"$group": {"_id": "$Brand"}},
            {"$sort": {"_id": 1}}
        ]
        
        all_brands_result = await db.business_data.aggregate(pipeline_all_brands).to_list(1000)
        all_brands = [item["_id"] for item in all_brands_result if item.get("_id")]
        all_brands_count = len(all_brands)
        
        # Count brands with revenue > 0 (current logic)
        pipeline_brands_with_revenue = [
            {"$match": query},
            {"$match": {"Brand": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None"]}}},
            {
                "$group": {
                    "_id": "$Brand",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                }
            },
            {"$match": {"Revenue": {"$gt": 0}}},
            {"$sort": {"_id": 1}}
        ]
        
        brands_with_revenue_result = await db.business_data.aggregate(pipeline_brands_with_revenue).to_list(1000)
        brands_with_revenue = [item["_id"] for item in brands_with_revenue_result if item.get("_id")]
        brands_with_revenue_count = len(brands_with_revenue)
        
        # Count brands with any data (revenue, profit, or units > 0)
        pipeline_brands_with_data = [
            {"$match": query},
            {"$match": {"Brand": {"$ne": None, "$exists": True, "$nin": ["", " ", "Unknown", "null", "None"]}}},
            {
                "$group": {
                    "_id": "$Brand",
                    "Revenue": {"$sum": {"$toDouble": {"$ifNull": ["$Revenue", 0]}}},
                    "Gross_Profit": {"$sum": {"$toDouble": {"$ifNull": ["$Gross_Profit", 0]}}},
                    "Units": {"$sum": {"$toDouble": {"$ifNull": ["$Units", 0]}}},
                }
            },
            {
                "$match": {
                    "$or": [
                        {"Revenue": {"$gt": 0}},
                        {"Gross_Profit": {"$gt": 0}},
                        {"Units": {"$gt": 0}}
                    ]
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        brands_with_data_result = await db.business_data.aggregate(pipeline_brands_with_data).to_list(1000)
        brands_with_data = [item["_id"] for item in brands_with_data_result if item.get("_id")]
        brands_with_data_count = len(brands_with_data)
        
        # Find brands with 0 revenue but have other data
        brands_zero_revenue = []
        for item in brands_with_data_result:
            if item.get("Revenue", 0) == 0 and (item.get("Gross_Profit", 0) > 0 or item.get("Units", 0) > 0):
                brands_zero_revenue.append(item["_id"])
        
        print(f"✅ All distinct brands: {all_brands_count}")
        print(f"✅ Brands with Revenue > 0: {brands_with_revenue_count} (current logic)")
        print(f"✅ Brands with any data (Revenue/Profit/Units > 0): {brands_with_data_count}")
        print(f"✅ Expected count: {expected}")
        
        if brands_zero_revenue:
            print(f"⚠️  Brands with 0 revenue but have other data: {len(brands_zero_revenue)}")
            print(f"   {brands_zero_revenue[:5]}...")  # Show first 5
        
        # Check which count matches expected
        if all_brands_count == expected:
            print(f"✅ Match: All distinct brands count matches expected!")
        elif brands_with_data_count == expected:
            print(f"✅ Match: Brands with any data count matches expected!")
            print(f"⚠️  Issue: Current logic (Revenue > 0) excludes {expected - brands_with_revenue_count} brand(s)")
        elif brands_with_revenue_count == expected:
            print(f"✅ Match: Brands with Revenue > 0 count matches expected!")
        else:
            print(f"❌ No match found!")
            print(f"   Difference (all brands vs expected): {all_brands_count - expected}")
            print(f"   Difference (with data vs expected): {brands_with_data_count - expected}")
            print(f"   Difference (with revenue vs expected): {brands_with_revenue_count - expected}")
        
        # Show brands that are in "all brands" but not in "with revenue"
        missing_brands = set(all_brands) - set(brands_with_revenue)
        if missing_brands:
            print(f"\n📋 Brands with 0 revenue (excluded by current logic): {len(missing_brands)}")
            print(f"   {sorted(list(missing_brands))[:10]}...")  # Show first 10
    
    client.close()
    print("\n" + "="*60)
    print("Analysis Complete")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_brand_counts())

