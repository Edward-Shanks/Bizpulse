"""
Check and update admin user
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
_dotenv_path = find_dotenv(str(ROOT_DIR / '.env')) or find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)

# MongoDB connection
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')
if not mongo_url or not db_name:
    raise RuntimeError("Missing MONGO_URL or DB_NAME")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

async def check_and_update_admin():
    email = os.getenv('ADMIN_EMAIL', 'admin@thrivebrands.ai')
    password = os.getenv('ADMIN_PASSWORD', 'Thrive@123')
    
    print(f"Checking user: {email}")
    
    # Find user
    user = await db.users.find_one({"email": email})
    if not user:
        print(f"❌ User not found: {email}")
        return
    
    print(f"✅ User found: {user.get('name', 'N/A')} ({user.get('email')})")
    print(f"   Current role: {user.get('role')}")
    print(f"   Current department: {user.get('department')}")
    print(f"   Current status: {user.get('status')}")
    
    # Verify password
    stored_hash = user.get('password_hash', '')
    if stored_hash:
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            print(f"✅ Password verification: SUCCESS")
        else:
            print(f"❌ Password verification: FAILED")
            print("   The stored password hash does not match 'Thrive@123'")
            return
    
    # Update user to be admin
    update_data = {
        'role': 'Admin',
        'department': 'admin',
        'status': 'active'
    }
    
    result = await db.users.update_one(
        {"email": email},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        print(f"\n✅ Successfully updated user to Admin!")
        print(f"   Role: Admin")
        print(f"   Department: admin")
        print(f"   Status: active")
    else:
        print(f"\n⚠️  User already has these values or no changes were made")
    
    # Verify update
    updated_user = await db.users.find_one({"email": email})
    print(f"\n📋 Updated user details:")
    print(f"   Email: {updated_user.get('email')}")
    print(f"   Role: {updated_user.get('role')}")
    print(f"   Department: {updated_user.get('department')}")
    print(f"   Status: {updated_user.get('status')}")

if __name__ == "__main__":
    asyncio.run(check_and_update_admin())

