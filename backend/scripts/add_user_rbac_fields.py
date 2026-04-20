#!/usr/bin/env python3
"""
Add RBAC (role + access) fields to the users collection in a TARGET database.
Run with --target-db bizpulse_rbac for testing, or --target-db bizpulse later for production.
Does NOT touch the source bizpulse unless you explicitly pass --target-db bizpulse.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import argparse
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

# RBAC schema: same as filter options (businesses, channels, brands, categories, sub_categories, customers)
# allowed_metrics: e.g. ["gsales", "fgp"] or ["*"] for all
DEFAULT_ACCESS = {
    "businesses": [],       # e.g. ["Food"]
    "channels": [],         # e.g. ["Grocery"]
    "brands": [],           # e.g. ["Cali Cali", "Bensons"]
    "categories": "all",    # "all" or list e.g. ["Curry", "Beauty"]
    "sub_categories": "all",
    "customers": "all",
    "allowed_metrics": [],  # e.g. ["gsales", "fgp"] or ["*"] for all
}

ADMIN_ACCESS = {
    "businesses": ["*"],
    "channels": ["*"],
    "brands": ["*"],
    "categories": "all",
    "sub_categories": "all",
    "customers": "all",
    "allowed_metrics": ["*"],
}


async def add_rbac_to_users(target_db_name: str, dry_run: bool = False):
    client = AsyncIOMotorClient(MONGO_URL)
    try:
        await client.admin.command("ping")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    db = client[target_db_name]
    users = db.users
    count = await users.count_documents({})
    if count == 0:
        print(f"No users in {target_db_name}.users. Nothing to update.")
        client.close()
        return

    updated = 0
    cursor = users.find({})
    async for user in cursor:
        email = user.get("email") or user.get("Email")
        if not email:
            continue
        # Skip if already has access + role
        if user.get("access") is not None and user.get("role") is not None:
            continue
        is_admin = user.get("role") == "admin" or user.get("is_admin") or str(email).lower().startswith("admin")
        role = "admin" if is_admin else "user"
        access = ADMIN_ACCESS if is_admin else DEFAULT_ACCESS.copy()
        if not dry_run:
            await users.update_one(
                {"_id": user["_id"]},
                {"$set": {"role": role, "access": access, "rbac_updated_at": datetime.utcnow()}},
            )
        updated += 1
        print(f"   {'[dry-run] ' if dry_run else ''}{email}: role={role}")

    print(f"\n✅ RBAC fields added for {updated} users in {target_db_name}.users")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="Add RBAC fields to users in target DB")
    parser.add_argument("--target-db", default="bizpulse_rbac", help="Target database (default: bizpulse_rbac)")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be updated")
    args = parser.parse_args()

    print("=" * 70)
    print("Add RBAC fields to users collection")
    print("=" * 70)
    print(f"Target DB: {args.target_db}")
    if args.dry_run:
        print("Mode: DRY RUN (no writes)")
    print("=" * 70)

    asyncio.run(add_rbac_to_users(args.target_db, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
