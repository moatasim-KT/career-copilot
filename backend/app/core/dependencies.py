"""
FastAPI dependencies for authentication and database access
"""

from typing import Optional
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.profile_service import ProfileService

# HTTP Bearer token security scheme
security = HTTPBearer()

# Simple in-memory rate limiting (for production, use Redis)
_rate_limit_storage = defaultdict(list)
_failed_attempts = defaultdict(int)


class RateLimiter:
    """Simple rate limiter for authentication endpoints"""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit"""
        now = time.time()
        
        # Clean old entries
        _rate_limit_storage[identifier] = [
            timestamp for timestamp in _rate_limit_storage[identifier]
            if now - timestamp < self.window_seconds
        ]
        
        # Check if under limit
        if len(_rate_limit_storage[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        _rate_limit_storage[identifier].append(now)
        return True
    
    def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt"""
        _failed_attempts[identifier] += 1
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked due to too many failed attempts"""
        return _failed_attempts[identifier] >= 10  # Block after 10 failed attempts
    
    def reset_failed_attempts(self, identifier: str):
        """Reset failed attempts counter"""
        _failed_attempts[identifier] = 0


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Get authentication service instance
    
    Args:
        db: Database session
        
    Returns:
        AuthService instance
    """
    return AuthService(db)


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    """
    Get profile service instance
    
    Args:
        db: Database session
        
    Returns:
        ProfileService instance
    """
    return ProfileService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    request: Request = None
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP authorization credentials
        auth_service: Authentication service
        request: HTTP request object
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    # Check rate limiting if request is available
    if request:
        client_ip = request.client.host if request.client else "unknown"
        if rate_limiter.is_blocked(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed authentication attempts. Please try again later."
            )
    
    user = auth_service.get_current_user_from_token(credentials.credentials)
    if user is None:
        # Record failed attempt if request is available
        if request:
            client_ip = request.client.host if request.client else "unknown"
            rate_limiter.record_failed_attempt(client_ip)
        raise credentials_exception
    
    # Reset failed attempts on successful authentication
    if request:
        client_ip = request.client.host if request.client else "unknown"
        rate_limiter.reset_failed_attempts(client_ip)
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Get current user if token provided, otherwise return None
    Used for endpoints that work with or without authentication
    
    Args:
        credentials: Optional HTTP authorization credentials
        auth_service: Authentication service
        
    Returns:
        User object or None
    """
    if not credentials:
        return None
    
    user = auth_service.get_current_user_from_token(credentials.credentials)
    return user if user and user.is_active else None