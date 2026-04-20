#!/usr/bin/env python3
"""
Quick verification script: Check if RBAC fields exist in users collection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_rbac():
    client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
    db = client["bizpulse_rbac"]
    
    # Check admin user
    admin = await db.users.find_one({"email": "admin@thrivebrands.ai"})
    if admin:
        print("✅ Admin user found:")
        print(f"   role = {admin.get('role')}")
        print(f"   access = {admin.get('access')}")
    else:
        print("❌ Admin user not found")
    
    # Count users with RBAC fields
    with_role = await db.users.count_documents({"role": {"$exists": True}})
    with_access = await db.users.count_documents({"access": {"$exists": True}})
    total = await db.users.count_documents({})
    
    print(f"\n📊 Users in bizpulse_rbac:")
    print(f"   Total: {total}")
    print(f"   With 'role' field: {with_role}")
    print(f"   With 'access' field: {with_access}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(verify_rbac())
