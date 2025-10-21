"""
Authentication service for user management and JWT operations
"""

import re
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate, UserLogin
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements
            
        Raises:
            HTTPException: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        if len(password) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be less than 128 characters long"
            )
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter"
            )
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one digit"
            )
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character"
            )
        
        return True
    
    def validate_email_format(self, email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            True if email is valid
            
        Raises:
            HTTPException: If email format is invalid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        return True
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create new user account
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Validate email format
        self.validate_email_format(user_data.email)
        
        # Validate password strength
        self.validate_password_strength(user_data.password)
        
        # Check if user already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        # Set default profile and settings if not provided
        default_profile = {
            "skills": [],
            "experience_level": "entry",
            "locations": [],
            "preferences": {
                "salary_min": None,
                "company_size": [],
                "industries": [],
                "remote_preference": "no_preference"
            },
            "career_goals": []
        }
        
        default_settings = {
            "notifications": {
                "morning_briefing": True,
                "evening_summary": True,
                "email_time": "08:00"
            },
            "ui_preferences": {
                "theme": "light",
                "dashboard_layout": "standard"
            }
        }
        
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            profile=user_data.profile or default_profile,
            settings=user_data.settings or default_settings,
            is_active=user_data.is_active
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """
        Authenticate user with email and password
        
        Args:
            login_data: Login credentials
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user_by_email(login_data.email)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(login_data.password, user.password_hash):
            return None
        
        # Update last active timestamp
        user.last_active = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information
        
        Args:
            user_id: User ID to update
            user_data: Updated user data
            
        Returns:
            Updated user object or None if not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update fields if provided
        if user_data.email is not None:
            # Check if new email is already taken
            existing_user = self.get_user_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = user_data.email
        
        if user_data.password is not None:
            self.validate_password_strength(user_data.password)
            user.password_hash = get_password_hash(user_data.password)
        
        if user_data.profile is not None:
            user.profile = user_data.profile
        
        if user_data.settings is not None:
            user.settings = user_data.settings
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False
        
        # Validate new password strength
        self.validate_password_strength(new_password)
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def create_tokens(self, user: User) -> dict:
        """
        Create access and refresh tokens for user
        
        Args:
            user: User object
            
        Returns:
            Dictionary containing access and refresh tokens
        """
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """
        Create new access token from refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token pair or None if refresh token invalid
        """
        payload = verify_token(refresh_token)
        if not payload:
            return None
        
        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = self.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            return None
        
        return self.create_tokens(user)
    
    def get_current_user_from_token(self, token: str) -> Optional[User]:
        """
        Get current user from access token
        
        Args:
            token: JWT access token
            
        Returns:
            User object or None if token invalid
        """
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = self.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            return None
        
        return user