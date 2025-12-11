"""
User service - Handles user management operations
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from app.models.user import UserResponse
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.user_repo = UserRepository(db)
    
    async def get_all_users(self) -> List[UserResponse]:
        """Get all active users"""
        users = await self.user_repo.get_all_active_users()
        return [UserResponse(**user) for user in users]
    
    async def get_users_by_department(self, department: str) -> List[UserResponse]:
        """Get users by department"""
        users = await self.user_repo.get_users_by_department(department)
        return [UserResponse(**user) for user in users]
    
    async def get_current_user_info(self, email: str) -> UserResponse:
        """Get current user information"""
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        return UserResponse(**user)

# Factory function
def get_user_service(db: AsyncIOMotorDatabase) -> UserService:
    """Get user service instance"""
    return UserService(db)



