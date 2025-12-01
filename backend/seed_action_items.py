"""
Script to seed cockpit_action_items collection in MongoDB
Run this script to populate the Top Action Items data
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
_dotenv_path = find_dotenv(str(ROOT_DIR / '.env')) or find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)

# MongoDB connection
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')

if not mongo_url or not db_name:
    raise RuntimeError("Missing MONGO_URL or DB_NAME in environment variables")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

async def seed_action_items():
    """Seed the cockpit_action_items collection with sample data"""
    
    # Action items based on the screenshot/requirements
    action_items_data = {
        "critical": [
            {
                "id": 1,
                "title": "Reverse 45% YoY Revenue Decline: Emergency Recovery Plan",
                "dueDate": "2025-12-15",
                "priority": "high",
                "impact": "high",
                "category": "critical",
                "description": "Urgent action required to address significant year-over-year revenue decline"
            },
            {
                "id": 2,
                "title": "Reduce Grocery Channel Concentration from 73.4%",
                "dueDate": "2025-01-20",
                "priority": "high",
                "impact": "high",
                "category": "critical",
                "description": "Diversify channel mix to reduce dependency on grocery channel"
            },
            {
                "id": 3,
                "title": "Stabilize Top 5 Customer Relationships",
                "dueDate": "2025-01-15",
                "priority": "medium",
                "impact": "high",
                "category": "critical",
                "description": "Focus on maintaining and strengthening relationships with top customers"
            },
            {
                "id": 4,
                "title": "Audit Food Business Unit Margin Compression",
                "dueDate": "2025-02-01",
                "priority": "medium",
                "impact": "medium",
                "category": "critical",
                "description": "Investigate and address margin compression in food business unit"
            },
            {
                "id": 5,
                "title": "Launch Online Channel Growth Initiative",
                "dueDate": "2025-02-28",
                "priority": "low",
                "impact": "medium",
                "category": "critical",
                "description": "Develop and execute strategy to grow online channel presence"
            }
        ],
        "impact": [
            {
                "id": 6,
                "title": "Scale Food Business to €22M+ via Category Expansion",
                "dueDate": "2025-03-15",
                "priority": "high",
                "impact": "high",
                "category": "impact",
                "description": "Expand food business categories to achieve revenue target of €22M+"
            },
            {
                "id": 7,
                "title": "Develop Wholesale Channel Acceleration Program",
                "dueDate": "2025-02-28",
                "priority": "high",
                "impact": "high",
                "category": "impact",
                "description": "Create program to accelerate growth in wholesale channel"
            },
            {
                "id": 8,
                "title": "Optimize Household & Beauty Segment Efficiency",
                "dueDate": "2025-03-20",
                "priority": "medium",
                "impact": "medium",
                "category": "impact",
                "description": "Improve operational efficiency in household and beauty segments"
            },
            {
                "id": 9,
                "title": "Build International Channel to 5% of Revenue Mix",
                "dueDate": "2025-03-31",
                "priority": "low",
                "impact": "medium",
                "category": "impact",
                "description": "Develop international channel to reach 5% of total revenue"
            }
        ],
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    # Check if collection already has data
    existing = await db.cockpit_action_items.find_one({})
    if existing:
        print("⚠️  Action items already exist in MongoDB")
        print(f"   Critical items: {len(existing.get('critical', []))}")
        print(f"   Impact items: {len(existing.get('impact', []))}")
        response = input("Do you want to replace existing data? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted. Existing data preserved.")
            return
    
    # Insert or update the action items
    result = await db.cockpit_action_items.update_one(
        {},
        {"$set": action_items_data},
        upsert=True
    )
    
    if result.upserted_id or result.modified_count > 0:
        print("✅ Successfully seeded action items to MongoDB!")
        print(f"   Critical items: {len(action_items_data['critical'])}")
        print(f"   Impact items: {len(action_items_data['impact'])}")
        
        # Verify
        verify = await db.cockpit_action_items.find_one({})
        if verify:
            print(f"\n✅ Verification:")
            print(f"   Critical items in DB: {len(verify.get('critical', []))}")
            print(f"   Impact items in DB: {len(verify.get('impact', []))}")
    else:
        print("⚠️  No changes made to MongoDB")

if __name__ == "__main__":
    print("🌱 Seeding cockpit_action_items collection...\n")
    asyncio.run(seed_action_items())
    print("\n✅ Done!")

