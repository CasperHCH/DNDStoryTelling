"""Authentication service for user management and JWT handling."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class AuthService:
    """Service for handling user authentication and authorization."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise AuthenticationError("Token creation failed")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def authenticate_user(
        self, 
        username: str, 
        password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token data."""
        try:
            # Get user from database
            query = select(User).where(User.username == username)
            result = await self.db.execute(query)
            user = result.scalars().first()
            
            if not user or not user.is_active:
                logger.warning(f"Authentication failed for inactive user: {username}")
                return None
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            await self.db.commit()
            
            # Create access token
            access_token = self.create_access_token(
                data={"sub": user.username, "user_id": user.id}
            )
            
            logger.info(f"User authenticated successfully: {username}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return None
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token."""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            username = payload.get("sub")
            if not username:
                return None
            
            # Get user from database
            query = select(User).where(User.username == username)
            result = await self.db.execute(query)
            user = result.scalars().first()
            
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    async def logout_user(self, token: str) -> bool:
        """Logout user (in a real system, you'd invalidate the token)."""
        try:
            # In a production system, you would:
            # 1. Add token to blacklist
            # 2. Store blacklisted tokens in Redis/database
            # 3. Check blacklist in verify_token method
            
            user = await self.get_current_user(token)
            if user:
                logger.info(f"User logged out: {user.username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False