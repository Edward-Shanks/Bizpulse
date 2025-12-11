"""
User repository - Database operations for users
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from app.models.user import User, UserResponse
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for user database operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users
    
    async def find_by_email(self, email: str) -> Optional[dict]:
        """Find user by email (case-insensitive)"""
        return await self.collection.find_one(
            {"email": {"$regex": f"^{email}$", "$options": "i"}},
            {"_id": 0}
        )
    
    async def create_user(self, user: User) -> dict:
        """Create a new user"""
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await self.collection.insert_one(user_dict)
        logger.info(f"User created: {user.email}")
        return user_dict
    
    async def get_all_active_users(self) -> List[dict]:
        """Get all active users"""
        return await self.collection.find(
            {"status": "active"},
            {"_id": 0, "password_hash": 0}
        ).to_list(1000)
    
    async def get_users_by_department(self, department: str) -> List[dict]:
        """Get users by department"""
        return await self.collection.find(
            {"department": department.lower(), "status": "active"},
            {"_id": 0, "password_hash": 0}
        ).to_list(1000)
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email (exact match)"""
        return await self.collection.find_one(
            {"email": email},
            {"_id": 0, "password_hash": 0}
        )
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        count = await self.collection.count_documents({"email": email})
        return count > 0



