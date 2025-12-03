"""
Script to add test users to the database for testing goal assignment functionality.
Run this script to populate the database with sample team members across all departments.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# Load environment variables from .env file
ROOT_DIR = Path(__file__).parent
_dotenv_path = find_dotenv(str(ROOT_DIR / '.env')) or find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)
    print(f"✅ Loaded .env from: {_dotenv_path}")
else:
    print("⚠️  No .env file found. Using environment variables or defaults.")
# Hiiii
# MongoDB connection
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')

if not mongo_url or not db_name:
    raise RuntimeError(
        "Missing required environment variables. Make sure backend/.env exists and has MONGO_URL and DB_NAME."
    )

print(f"🔗 Connecting to: {db_name}")
print(f"📍 MongoDB URL: {mongo_url[:50]}...")  # Show first 50 chars for security

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Test users data
TEST_USERS = [
    # Sales Team
    {'email': 'sarah.johnson@thrivebrands.ai', 'name': 'Sarah Johnson', 'password': 'Test@123', 'department': 'sales', 'role': 'VP'},
    {'email': 'mike.chen@thrivebrands.ai', 'name': 'Mike Chen', 'password': 'Test@123', 'department': 'sales', 'role': 'Director'},
    {'email': 'emily.davis@thrivebrands.ai', 'name': 'Emily Davis', 'password': 'Test@123', 'department': 'sales', 'role': 'Manager'},
    {'email': 'john.smith@thrivebrands.ai', 'name': 'John Smith', 'password': 'Test@123', 'department': 'sales', 'role': 'Team Member'},
    {'email': 'lisa.williams@thrivebrands.ai', 'name': 'Lisa Williams', 'password': 'Test@123', 'department': 'sales', 'role': 'Team Member'},
    
    # Operations Team
    {'email': 'david.martinez@thrivebrands.ai', 'name': 'David Martinez', 'password': 'Test@123', 'department': 'operations', 'role': 'VP'},
    {'email': 'james.brown@thrivebrands.ai', 'name': 'James Brown', 'password': 'Test@123', 'department': 'operations', 'role': 'Director'},
    {'email': 'patricia.rodriguez@thrivebrands.ai', 'name': 'Patricia Rodriguez', 'password': 'Test@123', 'department': 'operations', 'role': 'Manager'},
    
    # Finance Team
    {'email': 'jennifer.lee@thrivebrands.ai', 'name': 'Jennifer Lee', 'password': 'Test@123', 'department': 'finance', 'role': 'VP'},
    {'email': 'robert.taylor@thrivebrands.ai', 'name': 'Robert Taylor', 'password': 'Test@123', 'department': 'finance', 'role': 'Director'},
    {'email': 'maria.garcia@thrivebrands.ai', 'name': 'Maria Garcia', 'password': 'Test@123', 'department': 'finance', 'role': 'Manager'},
    {'email': 'william.anderson@thrivebrands.ai', 'name': 'William Anderson', 'password': 'Test@123', 'department': 'finance', 'role': 'Team Member'},
    
    # HR Team
    {'email': 'patricia.rodriguez.hr@thrivebrands.ai', 'name': 'Patricia Rodriguez', 'password': 'Test@123', 'department': 'hr', 'role': 'VP'},
    {'email': 'amanda.foster@thrivebrands.ai', 'name': 'Amanda Foster', 'password': 'Test@123', 'department': 'hr', 'role': 'Manager'},
    {'email': 'susan.miller@thrivebrands.ai', 'name': 'Susan Miller', 'password': 'Test@123', 'department': 'hr', 'role': 'Team Member'},
    
    # Marketing Team
    {'email': 'michael.chen@thrivebrands.ai', 'name': 'Michael Chen', 'password': 'Test@123', 'department': 'marketing', 'role': 'VP'},
    {'email': 'emily.davis.marketing@thrivebrands.ai', 'name': 'Emily Davis', 'password': 'Test@123', 'department': 'marketing', 'role': 'Director'},
    {'email': 'rachel.green@thrivebrands.ai', 'name': 'Rachel Green', 'password': 'Test@123', 'department': 'marketing', 'role': 'Manager'},
    {'email': 'daniel.wilson@thrivebrands.ai', 'name': 'Daniel Wilson', 'password': 'Test@123', 'department': 'marketing', 'role': 'Team Member'},
    {'email': 'jessica.moore@thrivebrands.ai', 'name': 'Jessica Moore', 'password': 'Test@123', 'department': 'marketing', 'role': 'Team Member'},
    {'email': 'thomas.jackson@thrivebrands.ai', 'name': 'Thomas Jackson', 'password': 'Test@123', 'department': 'marketing', 'role': 'Team Member'},
    {'email': 'ashley.white@thrivebrands.ai', 'name': 'Ashley White', 'password': 'Test@123', 'department': 'marketing', 'role': 'Team Member'},
    
    # Technology Team
    {'email': 'alex.thompson@thrivebrands.ai', 'name': 'Alex Thompson', 'password': 'Test@123', 'department': 'technology', 'role': 'VP'},
    {'email': 'rachel.green.tech@thrivebrands.ai', 'name': 'Rachel Green', 'password': 'Test@123', 'department': 'technology', 'role': 'Director'},
    {'email': 'chris.martin@thrivebrands.ai', 'name': 'Chris Martin', 'password': 'Test@123', 'department': 'technology', 'role': 'Manager'},
    {'email': 'ryan.clark@thrivebrands.ai', 'name': 'Ryan Clark', 'password': 'Test@123', 'department': 'technology', 'role': 'Team Member'},
    {'email': 'nicole.lewis@thrivebrands.ai', 'name': 'Nicole Lewis', 'password': 'Test@123', 'department': 'technology', 'role': 'Team Member'},
    
    # Client User
    {'email': 'Barry@thrivebrands.ai', 'name': 'Barry', 'password': 'Barry@123', 'department': 'sales', 'role': 'VP'},
]

async def add_test_users():
    """Add test users to the database"""
    print("Starting to add test users...")
    
    added_count = 0
    skipped_count = 0
    
    for user_data in TEST_USERS:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data['email']})
        if existing_user:
            print(f"⏭️  User {user_data['email']} already exists, skipping...")
            skipped_count += 1
            continue
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user document
        user_doc = {
            "id": str(uuid.uuid4()),
            "email": user_data['email'],
            "password_hash": password_hash,
            "name": user_data['name'],
            "department": user_data['department'],
            "role": user_data['role'],
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert user
        await db.users.insert_one(user_doc)
        print(f"✅ Added user: {user_data['name']} ({user_data['email']}) - {user_data['department']} - {user_data['role']}")
        added_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Added: {added_count} users")
    print(f"   ⏭️  Skipped: {skipped_count} users (already exist)")
    print(f"   📝 Total test users available: {len(TEST_USERS)}")
    
    # Print summary by department
    print(f"\n📋 Users by Department:")
    dept_counts = {}
    for user_data in TEST_USERS:
        dept = user_data['department']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    
    for dept, count in sorted(dept_counts.items()):
        print(f"   {dept.capitalize()}: {count} users")
    
    print(f"\n🔑 All test users have password: Test@123")
    print(f"✅ Done!")

if __name__ == "__main__":
    asyncio.run(add_test_users())

