"""
Authentication service - Handles user authentication and JWT token generation
"""
import bcrypt
import jwt
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.models.user import User, LoginRequest, LoginResponse, SignupRequest, UserResponse
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.user_repo = UserRepository(db)
    
    async def login(self, request: LoginRequest) -> LoginResponse:
        """Authenticate user and return JWT token"""
        # Make email matching case-insensitive
        email_lower = request.email.lower().strip()
        user_doc = await self.user_repo.find_by_email(email_lower)
        
        if not user_doc:
            raise ValueError("Invalid credentials")
        
        # Use the actual email from database for consistency
        actual_email = user_doc.get('email', request.email)
        
        # Verify password
        if not bcrypt.checkpw(request.password.encode('utf-8'), user_doc['password_hash'].encode('utf-8')):
            raise ValueError("Invalid credentials")
        
        # Create JWT token
        token = jwt.encode(
            {
                "email": actual_email,
                "exp": datetime.now(timezone.utc).timestamp() + (settings.JWT_EXPIRATION_HOURS * 3600)
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return LoginResponse(token=token, email=actual_email)
    
    async def signup(self, request: SignupRequest, current_user_email: str) -> UserResponse:
        """Create a new user (development only)"""
        # Check if in development mode
        if not settings.is_development:
            raise ValueError("Signup is only available in development mode")
        
        # Check if user already exists
        if await self.user_repo.user_exists(request.email):
            raise ValueError("User already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = User(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
            department=request.department,
            role=request.role,
            status="active"
        )
        
        user_dict = await self.user_repo.create_user(user)
        
        return UserResponse(
            id=user_dict['id'],
            email=user_dict['email'],
            name=user_dict.get('name'),
            department=user_dict.get('department'),
            role=user_dict.get('role'),
            status=user_dict['status']
        )
    
    async def create_default_admin_user(self) -> None:
        """Create default admin user if it doesn't exist"""
        existing_user = await self.user_repo.find_by_email("data.admin@thrivebrands.ai")
        if not existing_user:
            default_password = "ThriveBrands@2024"
            password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            user = User(
                email="data.admin@thrivebrands.ai",
                password_hash=password_hash,
                name="Data Admin",
                department="technology",
                role="VP",
                status="active"
            )
            
            await self.user_repo.create_user(user)
            logger.info("Admin user created")

# Factory function for dependency injection
def get_auth_service(db: AsyncIOMotorDatabase) -> AuthService:
    """Get auth service instance"""
    return AuthService(db)

# Standalone function for creating default admin (used in startup)
async def create_default_admin_user(db: AsyncIOMotorDatabase) -> None:
    """Create default admin user (standalone function for startup)"""
    service = AuthService(db)
    await service.create_default_admin_user()



