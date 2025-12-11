"""
User management routes
Handles user listing and user info endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.user import UserResponse
from app.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all users/team members"""
    try:
        user_service = UserService(db)
        return await user_service.get_all_users()
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/by-department/{department}", response_model=List[UserResponse])
async def get_users_by_department(
    department: str,
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get users by department"""
    try:
        user_service = UserService(db)
        return await user_service.get_users_by_department(department)
    except Exception as e:
        logger.error(f"Error getting users by department: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current logged-in user information"""
    try:
        user_service = UserService(db)
        return await user_service.get_current_user_info(email)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting current user info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



