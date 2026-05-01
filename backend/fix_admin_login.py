"""
Fix Admin Login - Create/Update admin user with correct credentials
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME')

async def fix_admin_user():
    """Create or update admin user with correct credentials"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Admin credentials
    admin_email = "admin@thrivebrands.ai"
    admin_password = "Thrive@123"
    
    print(f"Connecting to MongoDB: {DB_NAME}")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": admin_email})
    
    if existing_user:
        print(f"✓ User found: {admin_email}")
        print(f"  ID: {existing_user.get('id')}")
        print(f"  Name: {existing_user.get('name')}")
        print(f"  Status: {existing_user.get('status')}")
    else:
        print(f"✗ User NOT found: {admin_email}")
    
    # Hash the password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create/Update user
    admin_user = {
        "email": admin_email,
        "password_hash": password_hash,
        "name": "Admin User",
        "department": "technology",
        "role": "Admin",
        "status": "active"
    }
    
    result = await db.users.update_one(
        {"email": admin_email},
        {"$set": admin_user},
        upsert=True
    )
    
    if result.upserted_id:
        print(f"\n✓ Admin user CREATED successfully!")
    else:
        print(f"\n✓ Admin user UPDATED successfully!")
    
    print(f"\nLogin Credentials:")
    print(f"  Email: {admin_email}")
    print(f"  Password: {admin_password}")
    
    # Verify the user was created/updated
    updated_user = await db.users.find_one({"email": admin_email})
    print(f"\n✓ Verification:")
    print(f"  User exists: {updated_user is not None}")
    print(f"  Has password_hash: {bool(updated_user.get('password_hash'))}")
    
    # Test password verification
    stored_hash = updated_user.get('password_hash')
    if stored_hash:
        is_valid = bcrypt.checkpw(admin_password.encode('utf-8'), stored_hash.encode('utf-8'))
        print(f"  Password verification test: {'✓ PASS' if is_valid else '✗ FAIL'}")
    
    # List all users in database
    print(f"\n--- All Users in {DB_NAME} ---")
    all_users = await db.users.find({}, {"email": 1, "name": 1, "status": 1, "_id": 0}).to_list(length=100)
    for user in all_users:
        print(f"  • {user.get('email')} - {user.get('name')} ({user.get('status')})")
    
    client.close()
    print("\n✓ Done! You can now login with the credentials above.")

if __name__ == "__main__":
    asyncio.run(fix_admin_user())
