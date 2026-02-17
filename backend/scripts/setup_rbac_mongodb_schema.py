#!/usr/bin/env python3
"""
Set up MongoDB schema for REAL RBAC (Role-Based Access Control)
This creates a users_permissions collection to store user access levels
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime
import bcrypt

load_dotenv()

# MongoDB connection
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'bizpulse')

async def setup_rbac_schema():
    """Create RBAC MongoDB collections and sample data"""
    
    print("=" * 70)
    print("🔐 Setting up RBAC MongoDB Schema")
    print("=" * 70)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("\n📊 Creating collections...")
    
    # 1. Create users_permissions collection
    # This stores user access controls
    print("\n1. Creating 'users_permissions' collection...")
    
    # Create indexes
    await db.users_permissions.create_index("email", unique=True)
    await db.users_permissions.create_index("user_id", unique=True)
    
    print("   ✅ Indexes created")
    
    # Check if admin user exists
    admin_exists = await db.users_permissions.find_one({"email": "admin@bizpulse.com"})
    
    if not admin_exists:
        print("\n2. Creating ADMIN user...")
        
        # Hash password
        password = "Admin@123!Secure"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = {
            "user_id": "admin_001",
            "email": "admin@bizpulse.com",
            "name": "Admin User",
            "password_hash": hashed.decode('utf-8'),
            "role": "admin",
            "is_admin": True,
            "is_active": True,
            
            # Admin has access to ALL data
            "access_level": {
                "businesses": ["*"],  # * means ALL
                "channels": ["*"],
                "brands": ["*"],
                "categories": ["*"],
                "sub_categories": ["*"],
                "customers": ["*"],
                "data_types": ["*"]  # revenue, profit, costs, finance, all
            },
            
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        await db.users_permissions.insert_one(admin_user)
        print("   ✅ Admin user created")
        print(f"      Email: admin@bizpulse.com")
        print(f"      Password: {password}")
    else:
        print("\n2. Admin user already exists ✓")
    
    # Get actual filter values from business_data
    print("\n3. Getting available filter options from data...")
    
    # Get distinct businesses
    businesses = await db.business_data.distinct("Business")
    businesses = [b for b in businesses if b and str(b).strip() and str(b).lower() != 'unknown']
    print(f"   Businesses: {len(businesses)}")
    for b in businesses[:10]:
        print(f"      - {b}")
    if len(businesses) > 10:
        print(f"      ... and {len(businesses) - 10} more")
    
    # Get distinct channels
    channels = await db.business_data.distinct("Channel")
    channels = [c for c in channels if c and str(c).strip() and str(c).lower() != 'unknown']
    print(f"   Channels: {len(channels)}")
    for c in channels[:10]:
        print(f"      - {c}")
    
    # Get distinct brands
    brands = await db.business_data.distinct("Brand")
    brands = [b for b in brands if b and str(b).strip() and str(b).lower() not in ['unknown', 'none']]
    print(f"   Brands: {len(brands)}")
    for b in brands[:10]:
        print(f"      - {b}")
    if len(brands) > 10:
        print(f"      ... and {len(brands) - 10} more")
    
    # Get distinct categories
    categories = await db.business_data.distinct("Category")
    categories = [c for c in categories if c and str(c).strip() and str(c).lower() not in ['unknown', 'none']]
    print(f"   Categories: {len(categories)}")
    for c in categories[:10]:
        print(f"      - {c}")
    
    # Get distinct customers
    customers = await db.business_data.distinct("Customer")
    customers = [c for c in customers if c and str(c).strip() and str(c).lower() not in ['unknown', 'none']]
    print(f"   Customers: {len(customers)}")
    for c in customers[:10]:
        print(f"      - {c}")
    if len(customers) > 10:
        print(f"      ... and {len(customers) - 10} more")
    
    # Create sample users with REAL data access
    print("\n4. Creating sample users with real access levels...")
    
    # Check if sample users exist
    existing_users = await db.users_permissions.find({}).to_list(length=None)
    existing_emails = [u['email'] for u in existing_users]
    
    sample_users = []
    
    # Manager: Access to first 2 businesses, revenue + profit
    if "manager@bizpulse.com" not in existing_emails and len(businesses) >= 2:
        password = "Manager@123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sample_users.append({
            "user_id": "manager_001",
            "email": "manager@bizpulse.com",
            "name": "Manager User",
            "password_hash": hashed.decode('utf-8'),
            "role": "manager",
            "is_admin": False,
            "is_active": True,
            "access_level": {
                "businesses": businesses[:2],  # First 2 businesses
                "channels": ["*"],
                "brands": ["*"],
                "categories": ["*"],
                "sub_categories": ["*"],
                "customers": ["*"],
                "data_types": ["revenue", "profit"]  # Can see revenue & profit, NOT costs
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"   ✅ Manager user: manager@bizpulse.com (Password: {password})")
        print(f"      Access: {businesses[:2]}")
    
    # Sales: Access to first business only, revenue only
    if "sales@bizpulse.com" not in existing_emails and len(businesses) >= 1:
        password = "Sales@123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sample_users.append({
            "user_id": "sales_001",
            "email": "sales@bizpulse.com",
            "name": "Sales User",
            "password_hash": hashed.decode('utf-8'),
            "role": "sales",
            "is_admin": False,
            "is_active": True,
            "access_level": {
                "businesses": [businesses[0]],  # Only first business
                "channels": ["*"],
                "brands": ["*"],
                "categories": ["*"],
                "sub_categories": ["*"],
                "customers": ["*"],
                "data_types": ["revenue"]  # Only revenue, NO profit or costs
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"   ✅ Sales user: sales@bizpulse.com (Password: {password})")
        print(f"      Access: [{businesses[0]}]")
    
    # Finance: All data access
    if "finance@bizpulse.com" not in existing_emails:
        password = "Finance@123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sample_users.append({
            "user_id": "finance_001",
            "email": "finance@bizpulse.com",
            "name": "Finance User",
            "password_hash": hashed.decode('utf-8'),
            "role": "finance",
            "is_admin": False,
            "is_active": True,
            "access_level": {
                "businesses": ["*"],
                "channels": ["*"],
                "brands": ["*"],
                "categories": ["*"],
                "sub_categories": ["*"],
                "customers": ["*"],
                "data_types": ["*"]  # All data including costs
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"   ✅ Finance user: finance@bizpulse.com (Password: {password})")
    
    # Channel Manager: Specific channel only
    if "channel@bizpulse.com" not in existing_emails and len(channels) >= 1:
        password = "Channel@123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sample_users.append({
            "user_id": "channel_001",
            "email": "channel@bizpulse.com",
            "name": "Channel Manager",
            "password_hash": hashed.decode('utf-8'),
            "role": "channel_manager",
            "is_admin": False,
            "is_active": True,
            "access_level": {
                "businesses": ["*"],
                "channels": [channels[0]],  # Only first channel
                "brands": ["*"],
                "categories": ["*"],
                "sub_categories": ["*"],
                "customers": ["*"],
                "data_types": ["revenue", "profit"]
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"   ✅ Channel Manager: channel@bizpulse.com (Password: {password})")
        print(f"      Access: [{channels[0]}]")
    
    # Brand Manager: Specific brands only
    if "brand@bizpulse.com" not in existing_emails and len(brands) >= 3:
        password = "Brand@123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sample_users.append({
            "user_id": "brand_001",
            "email": "brand@bizpulse.com",
            "name": "Brand Manager",
            "password_hash": hashed.decode('utf-8'),
            "role": "brand_manager",
            "is_admin": False,
            "is_active": True,
            "access_level": {
                "businesses": ["*"],
                "channels": ["*"],
                "brands": brands[:3],  # First 3 brands
                "categories": ["*"],
                "sub_categories": ["*"],
                "customers": ["*"],
                "data_types": ["revenue", "profit"]
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        print(f"   ✅ Brand Manager: brand@bizpulse.com (Password: {password})")
        print(f"      Access: {brands[:3]}")
    
    # Insert sample users
    if sample_users:
        await db.users_permissions.insert_many(sample_users)
        print(f"\n   ✅ Created {len(sample_users)} sample users")
    
    # Show summary
    print("\n" + "=" * 70)
    print("✅ RBAC Schema Setup Complete!")
    print("=" * 70)
    
    total_users = await db.users_permissions.count_documents({})
    print(f"\n📊 Total users in system: {total_users}")
    
    print("\n📋 Available filter values:")
    print(f"   Businesses: {len(businesses)}")
    print(f"   Channels: {len(channels)}")
    print(f"   Brands: {len(brands)}")
    print(f"   Categories: {len(categories)}")
    print(f"   Customers: {len(customers)}")
    
    print("\n🔐 User Roles:")
    print("   - admin: Full access to everything")
    print("   - manager: Multiple businesses, revenue + profit")
    print("   - sales: Single business, revenue only")
    print("   - finance: All data including costs")
    print("   - channel_manager: Specific channel")
    print("   - brand_manager: Specific brands")
    
    print("\n📝 Next Steps:")
    print("   1. Use these users to test RBAC")
    print("   2. Create real users via API endpoints")
    print("   3. Assign permissions based on checkboxes in UI")
    print("   4. Test with ClickHouse queries")
    
    print("=" * 70)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_rbac_schema())
