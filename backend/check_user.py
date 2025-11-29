"""
Quick script to check if a user exists and verify their credentials
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.getenv('DB_NAME', 'bizpulse')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

async def check_user():
    email = os.getenv('TEST_USER_EMAIL', 'Barry@thrivebrands.ai')
    password = os.getenv('TEST_USER_PASSWORD', 'Barry@123')
    
    print(f"Checking user: {email}")
    
    # Check if user exists (case-insensitive search)
    user = await db.users.find_one({"email": email})
    if not user:
        # Try case-insensitive search
        user = await db.users.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
    
    if not user:
        print(f"❌ User not found: {email}")
        print("\nSearching for similar emails...")
        all_users = await db.users.find({}, {"email": 1, "name": 1}).to_list(100)
        barry_users = [u for u in all_users if 'barry' in u.get('email', '').lower()]
        if barry_users:
            print("Found similar users:")
            for u in barry_users:
                print(f"  - {u.get('email')} ({u.get('name')})")
        else:
            print("No users with 'barry' in email found")
        return
    
    print(f"✅ User found: {user.get('name')} ({user.get('email')})")
    print(f"   Department: {user.get('department')}")
    print(f"   Role: {user.get('role')}")
    print(f"   Status: {user.get('status')}")
    
    # Test password
    stored_hash = user.get('password_hash', '')
    if stored_hash:
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                print(f"✅ Password verification: SUCCESS")
            else:
                print(f"❌ Password verification: FAILED")
                print("   The stored password hash does not match 'Barry@123'")
        except Exception as e:
            print(f"❌ Password verification error: {e}")
    else:
        print("❌ No password hash found in user document")

if __name__ == "__main__":
    asyncio.run(check_user())

