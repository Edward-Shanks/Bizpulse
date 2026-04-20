#!/usr/bin/env python3
"""
Copy ALL collections from MongoDB database 'bizpulse' to 'bizpulse_rbac'.
READ-ONLY from bizpulse (production). All writes go to bizpulse_rbac only.
Use this for testing RBAC and new user access features.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

SOURCE_DB = "bizpulse"
TARGET_DB = "bizpulse_rbac"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
BATCH_SIZE = 5000

# Collections we never write to (source only)
READ_ONLY_SOURCE = SOURCE_DB


async def copy_collection(client, coll_name: str) -> int:
    """Copy one collection from SOURCE_DB to TARGET_DB. Returns document count copied."""
    source_coll = client[SOURCE_DB][coll_name]
    target_coll = client[TARGET_DB][coll_name]
    total = 0
    cursor = source_coll.find({})
    batch = []
    async for doc in cursor:
        batch.append(doc)
        if len(batch) >= BATCH_SIZE:
            await target_coll.insert_many(batch)
            total += len(batch)
            print(f"   {coll_name}: {total} docs...")
            batch = []
    if batch:
        await target_coll.insert_many(batch)
        total += len(batch)
    return total


async def main():
    print("=" * 70)
    print("COPY bizpulse → bizpulse_rbac (MongoDB)")
    print("=" * 70)
    print(f"Source: {SOURCE_DB} (READ ONLY)")
    print(f"Target: {TARGET_DB}")
    print("=" * 70)

    client = AsyncIOMotorClient(MONGO_URL)
    try:
        await client.admin.command("ping")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    # List collections in source (bizpulse only)
    coll_names = await client[SOURCE_DB].list_collection_names()
    if not coll_names:
        print(f"❌ No collections found in '{SOURCE_DB}'")
        return

    print(f"\n📋 Collections to copy: {coll_names}")

    for coll_name in coll_names:
        if coll_name.startswith("system."):
            continue
        try:
            # Optional: clear target collection for full refresh
            await client[TARGET_DB][coll_name].delete_many({})
            count = await copy_collection(client, coll_name)
            print(f"   ✅ {coll_name}: {count} documents")
        except Exception as e:
            print(f"   ❌ {coll_name}: {e}")

    print("\n" + "=" * 70)
    print("✅ Copy complete. Use DB_NAME=bizpulse_rbac for read/write.")
    print("=" * 70)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
