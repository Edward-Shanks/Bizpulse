"""
Authentication routes
Handles login and signup endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.user import (
    LoginRequest, LoginResponse, SignupRequest, UserResponse, 
    RefreshTokenRequest, RefreshTokenResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ChangePasswordRequest, ChangePasswordResponse,
    UserListResponse, UpdateUserRequest, UpdateUserResponse, DeleteUserResponse
)
from app.core.config import settings
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """User login endpoint"""
    try:
        auth_service = AuthService(db)
        return await auth_service.login(request)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Refresh access token endpoint - accepts expired tokens"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(request.token)
        return RefreshTokenResponse(token=result["token"], email=result["email"])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/auth/signup", response_model=UserResponse)
async def signup(
    request: SignupRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
):
    """Development-only signup endpoint - authentication optional in dev mode"""
    try:
        # In development mode, authentication is optional
        current_user_email = None
        if credentials and credentials.credentials:
            try:
                # Try to get user from token (optional in dev mode)
                current_user_email = await get_current_user(credentials, db)
            except HTTPException:
                # If token is invalid, continue without auth (dev mode only)
                if settings.is_development:
                    logger.info("Signup called without valid token - allowing in dev mode")
                    current_user_email = None
                else:
                    raise
        
        auth_service = AuthService(db)
        return await auth_service.signup(request, current_user_email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Forgot password endpoint - sends email if user exists"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.forgot_password(request.email)
        return ForgotPasswordResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/auth/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Change password endpoint (development only)"""
    if not settings.is_development:
        raise HTTPException(status_code=403, detail="This endpoint is only available in development mode")
    try:
        auth_service = AuthService(db)
        result = await auth_service.change_password(request.email, request.new_password)
        return ChangePasswordResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/auth/users", response_model=UserListResponse)
async def list_users(
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = Depends(get_current_user)
):
    """List all users with passwords (development only) - requires authentication"""
    if not settings.is_development:
        raise HTTPException(status_code=403, detail="This endpoint is only available in development mode")
    try:
        # Get all users directly from database
        # Exclude MongoDB's internal _id field to avoid serialization issues
        cursor = db.users.find({}, {"_id": 0})
        users = await cursor.to_list(length=None)
        
        logger.info(f"Found {len(users)} users in database")
        
        user_list = []
        for user in users:
            # Convert ObjectId to string if present, and handle datetime
            user_id = user.get("id")
            if not user_id and "_id" in user:
                user_id = str(user["_id"])
            
            created_at = user.get("created_at")
            if created_at:
                if hasattr(created_at, 'isoformat'):
                    created_at = created_at.isoformat()
                elif isinstance(created_at, str):
                    created_at = created_at
                else:
                    created_at = None
            else:
                created_at = None
            
            # In dev mode, we can show password hashes (but not plain passwords)
            user_list.append({
                "id": user_id or "",
                "email": user.get("email", ""),
                "name": user.get("name"),
                "department": user.get("department"),
                "role": user.get("role"),
                "status": user.get("status", "active"),
                "password_hash": user.get("password_hash", ""),  # For dev reference
                "created_at": created_at
            })
        
        logger.info(f"Retrieved {len(user_list)} users for management")
        return UserListResponse(users=user_list)
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")

@router.put("/auth/users/{user_email}", response_model=UpdateUserResponse)
async def update_user(
    user_email: str,
    request: UpdateUserRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_email: str = Depends(get_current_user)
):
    """Update user details (development only) - requires authentication"""
    if not settings.is_development:
        raise HTTPException(status_code=403, detail="This endpoint is only available in development mode")
    try:
        email_lower = user_email.lower().strip()
        
        # Check if user exists
        user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update dictionary with only provided fields
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.department is not None:
            update_data["department"] = request.department
        if request.role is not None:
            update_data["role"] = request.role
        if request.status is not None:
            update_data["status"] = request.status
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update user
        result = await db.users.update_one(
            {"email": {"$regex": f"^{email_lower}$", "$options": "i"}},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to user")
        
        # Fetch updated user
        updated_user = await db.users.find_one(
            {"email": {"$regex": f"^{email_lower}$", "$options": "i"}},
            {"_id": 0}
        )
        
        # Format response
        user_dict = {
            "id": updated_user.get("id", ""),
            "email": updated_user.get("email", ""),
            "name": updated_user.get("name"),
            "department": updated_user.get("department"),
            "role": updated_user.get("role"),
            "status": updated_user.get("status", "active"),
            "password_hash": updated_user.get("password_hash", ""),
            "created_at": updated_user.get("created_at").isoformat() if updated_user.get("created_at") and hasattr(updated_user.get("created_at"), 'isoformat') else (updated_user.get("created_at") if isinstance(updated_user.get("created_at"), str) else None)
        }
        
        logger.info(f"User updated: {email_lower}")
        return UpdateUserResponse(message=f"User {email_lower} updated successfully", user=user_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.delete("/auth/users/{user_email}", response_model=DeleteUserResponse)
async def delete_user(
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_email: str = Depends(get_current_user)
):
    """Delete user (development only) - requires authentication"""
    if not settings.is_development:
        raise HTTPException(status_code=403, detail="This endpoint is only available in development mode")
    try:
        email_lower = user_email.lower().strip()
        
        # Prevent deleting yourself
        if email_lower == current_user_email.lower():
            raise HTTPException(status_code=400, detail="You cannot delete your own account")
        
        # Check if user exists
        user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user
        result = await db.users.delete_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="User could not be deleted")
        
        logger.info(f"User deleted: {email_lower}")
        return DeleteUserResponse(message=f"User {email_lower} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")



