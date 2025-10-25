"""
Authentication and authorization module.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from ..models.user import User as DBUser
from ..repositories.user_repository import UserRepository
from ..services.authentication_service import get_authentication_service

# Security scheme for JWT tokens
security = HTTPBearer()


class User:
    """User model for authentication context."""
    
    def __init__(self, db_user: DBUser):
        self.id = db_user.id
        self.username = db_user.username
        self.email = db_user.email
        self.is_active = db_user.is_active
        self.is_superuser = db_user.is_superuser
        self.permissions = []  # Can be extended based on roles


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).
    
    Args:
        credentials: HTTP authorization credentials (optional)
        session: Database session
        
    Returns:
        Current user or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user_from_credentials(credentials, session)
    except HTTPException:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        session: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    return await get_current_user_from_credentials(credentials, session)


async def get_current_user_from_credentials(
    credentials: HTTPAuthorizationCredentials,
    session: AsyncSession
) -> User:
    """
    Get current user from JWT credentials.
    
    Args:
        credentials: HTTP authorization credentials
        session: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        auth_service = get_authentication_service()
        
        # Validate token
        token_data = await auth_service.validate_access_token(credentials.credentials)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_id(token_data.user_id)
        
        if not db_user or not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return User(db_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# API Key authentication
async def APIKey(
    api_key: str = Depends(HTTPBearer()),
    session: Session = Depends(get_db)
) -> User:
    """
    API Key authentication dependency.
    
    Args:
        api_key: API key from Authorization header
        session: Database session
        
    Returns:
        User associated with the API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    try:
        from ..services.api_key_service import get_api_key_manager
        
        api_key_manager = get_api_key_manager()
        
        # Extract the actual key from the credentials
        key_value = api_key.credentials if hasattr(api_key, 'credentials') else str(api_key)
        
        # Validate API key
        validation_result = await api_key_manager.validate_api_key(key_value)
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_id(validation_result.key_data.user_id)
        
        if not db_user or not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return User(db_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


# For backward compatibility
def get_current_user_or_api_key():
    """Get current user or API key from request context."""
    return get_current_user
