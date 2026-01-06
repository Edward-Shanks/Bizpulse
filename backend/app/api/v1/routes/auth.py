"""
Authentication routes
Handles login and signup endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.user import LoginRequest, LoginResponse, SignupRequest, UserResponse, RefreshTokenRequest, RefreshTokenResponse
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
    email: str = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Development-only signup endpoint - requires authentication"""
    try:
        auth_service = AuthService(db)
        return await auth_service.signup(request, email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



