"""
User-related Pydantic models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class User(BaseModel):
    """User model for database"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    name: Optional[str] = None
    department: Optional[str] = None  # sales, operations, finance, hr, marketing, technology
    role: Optional[str] = None  # VP, Director, Manager, Team Member
    status: str = "active"  # active, inactive
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    token: str
    email: str

class SignupRequest(BaseModel):
    """Signup request model"""
    email: str
    password: str
    name: str
    department: str  # sales, operations, finance, hr, marketing, technology
    role: str  # VP, Director, Manager, Team Member

class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    status: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    token: str

class RefreshTokenResponse(BaseModel):
    """Refresh token response model"""
    token: str
    email: str

class ForgotPasswordRequest(BaseModel):
    """Forgot password request model"""
    email: str

class ForgotPasswordResponse(BaseModel):
    """Forgot password response model"""
    message: str

class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    email: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    """Change password response model"""
    message: str

class UserListResponse(BaseModel):
    """User list response model"""
    users: list[dict]

class UpdateUserRequest(BaseModel):
    """Update user request model"""
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

class UpdateUserResponse(BaseModel):
    """Update user response model"""
    message: str
    user: dict

class DeleteUserResponse(BaseModel):
    """Delete user response model"""
    message: str



