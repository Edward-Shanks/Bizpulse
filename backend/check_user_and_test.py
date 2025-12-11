"""
Check if admin user exists and test authentication
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

async def check_user():
    """Check if admin user exists"""
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    
    try:
        # Check for user
        user = await db.users.find_one({"email": {"$regex": "^data.admin@thrivebrands.ai$", "$options": "i"}})
        
        if user:
            print(f"[OK] User found: {user.get('email')}")
            print(f"[INFO] Status: {user.get('status')}")
            print(f"[INFO] Department: {user.get('department')}")
            print(f"[INFO] Has password_hash: {bool(user.get('password_hash'))}")
        else:
            print("[WARN] User not found!")
            print("[INFO] User should be created on server startup")
        
        # List all users
        all_users = await db.users.find({}, {"email": 1, "status": 1}).to_list(10)
        print(f"\n[INFO] Total users in database: {len(all_users)}")
        for u in all_users:
            print(f"  - {u.get('email')} ({u.get('status')})")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_user())



