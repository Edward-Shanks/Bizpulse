#!/usr/bin/env python3
"""
Copy ALL collections from MongoDB database 'bizpulse' to ClickHouse.
- business_data → ClickHouse bizpulse.sales_analytics (via existing migration logic)
- All other collections → ClickHouse bizpulse.mongodb_sync (collection name + id + JSON doc)

Reads ONLY from MongoDB bizpulse. Does not modify MongoDB.
ClickHouse database: bizpulse (or CLICKHOUSE_DB from .env).
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import clickhouse_driver
import os
import json
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

SOURCE_DB = "bizpulse"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "192.168.50.29")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 9000))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "bizpulse")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
BATCH_SIZE = 2000


def json_serial(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


async def ensure_mongodb_sync_table(ch):
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {CLICKHOUSE_DB}.mongodb_sync (
        collection String,
        id String,
        doc String
    ) ENGINE = MergeTree()
    ORDER BY (collection, id)
    """
    ch.execute(create_sql)


async def copy_non_business_collections(client, ch):
    """Copy every collection except business_data into ClickHouse mongodb_sync table."""
    coll_names = await client[SOURCE_DB].list_collection_names()
    to_sync = [c for c in coll_names if not c.startswith("system.") and c != "business_data"]
    if not to_sync:
        print("   No other collections to sync (besides business_data).")
        return
    await ensure_mongodb_sync_table(ch)
    # Clear existing rows so this run replaces data (no duplicates on re-run)
    ch.execute(f"TRUNCATE TABLE IF EXISTS {CLICKHOUSE_DB}.mongodb_sync")
    for coll_name in to_sync:
        coll = client[SOURCE_DB][coll_name]
        total = 0
        batch = []
        cursor = coll.find({})
        async for doc in cursor:
            oid = doc.get("_id")
            id_str = str(oid) if oid is not None else ""
            # Convert to JSON-serializable
            try:
                doc_copy = json.loads(json.dumps(doc, default=json_serial))
            except Exception:
                doc_copy = {"_id": id_str, "_raw_error": "serialization failed"}
            doc_str = json.dumps(doc_copy, default=json_serial)
            batch.append((coll_name, id_str, doc_str))
            if len(batch) >= BATCH_SIZE:
                ch.execute(
                    f"INSERT INTO {CLICKHOUSE_DB}.mongodb_sync (collection, id, doc) VALUES",
                    batch,
                )
                total += len(batch)
                print(f"   {coll_name}: {total} docs...")
                batch = []
        if batch:
            ch.execute(
                f"INSERT INTO {CLICKHOUSE_DB}.mongodb_sync (collection, id, doc) VALUES",
                batch,
            )
            total += len(batch)
        print(f"   ✅ {coll_name}: {total} documents → mongodb_sync")


async def main():
    print("=" * 70)
    print("Copy MongoDB bizpulse → ClickHouse")
    print("=" * 70)
    print(f"MongoDB source: {SOURCE_DB} (read only)")
    print(f"ClickHouse DB:   {CLICKHOUSE_DB}")
    print("=" * 70)

    client = AsyncIOMotorClient(MONGO_URL)
    try:
        await client.admin.command("ping")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    ch = clickhouse_driver.Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        database=CLICKHOUSE_DB,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD or None,
    )
    try:
        ch.execute("SELECT 1")
    except Exception as e:
        print(f"❌ ClickHouse connection failed: {e}")
        return

    # 1) business_data → sales_analytics: run existing migration (auto-confirm full reload)
    print("\n1. business_data → sales_analytics (existing migration)...")
    import subprocess
    import sys
    env = os.environ.copy()
    env["DB_NAME"] = SOURCE_DB
    script_path = os.path.join(os.path.dirname(__file__), "migrate_real_data_to_clickhouse.py")
    r = subprocess.run(
        [sys.executable, script_path],
        env=env,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        input=b"yes\n",  # auto-confirm if table has rows
    )
    if r.returncode != 0:
        print("   ⚠ Migration script returned non-zero. Run it manually if needed.")
    else:
        print("   ✅ business_data → sales_analytics done.")

    # 2) All other collections → mongodb_sync
    print("\n2. All other collections → ClickHouse mongodb_sync table...")
    await copy_non_business_collections(client, ch)

    print("\n" + "=" * 70)
    print("✅ Copy complete.")
    print("=" * 70)
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
