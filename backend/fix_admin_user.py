"""
Fix admin user status to 'active'
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

async def fix_user():
    """Update admin user status to active"""
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    try:
        result = await db.users.update_one(
            {"email": "data.admin@thrivebrands.ai"},
            {"$set": {"status": "active"}}
        )
        
        if result.modified_count > 0:
            print("[OK] User status updated to 'active'")
        else:
            print("[INFO] User status already set or user not found")
        
        # Verify
        user = await db.users.find_one({"email": "data.admin@thrivebrands.ai"})
        if user:
            print(f"[OK] User status is now: {user.get('status')}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_user())



