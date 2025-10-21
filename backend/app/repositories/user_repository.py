"""
User repository for user management and authentication operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.database_models import User, APIKey
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user management operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by_field("username", username)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance or None if not found
        """
        return await self.get_by_field("email", email)
    
    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """
        Get user by username or email address.
        
        Args:
            identifier: Username or email to search for
            
        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(User).where(
                or_(User.username == identifier, User.email == identifier)
            )
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self, 
        username: str, 
        email: str, 
        hashed_password: str,
        is_superuser: bool = False
    ) -> User:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: Unique email address
            hashed_password: Bcrypt hashed password
            is_superuser: Whether user has admin privileges
            
        Returns:
            Created user instance
        """
        return await self.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_superuser=is_superuser,
            is_active=True
        )
    
    async def update_password(self, user_id: UUID, hashed_password: str) -> Optional[User]:
        """
        Update user password.
        
        Args:
            user_id: User UUID
            hashed_password: New bcrypt hashed password
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update_by_id(user_id, hashed_password=hashed_password)
    
    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update_by_id(user_id, is_active=True)
    
    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: User UUID
            
        Returns:
            Updated user instance or None if not found
        """
        return await self.update_by_id(user_id, is_active=False)
    
    async def get_active_users(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[User]:
        """
        Get all active users.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of active user instances
        """
        return await self.list_by_field("is_active", True, limit=limit, offset=offset)
    
    async def get_superusers(self) -> List[User]:
        """
        Get all superuser accounts.
        
        Returns:
            List of superuser instances
        """
        return await self.list_by_field("is_superuser", True)
    
    async def search_users(
        self, 
        search_term: str, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """
        Search users by username or email.
        
        Args:
            search_term: Term to search for in username or email
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of matching user instances
        """
        query = select(User).where(
            or_(
                User.username.ilike(f"%{search_term}%"),
                User.email.ilike(f"%{search_term}%")
            )
        )
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_with_api_keys(self, user_id: UUID) -> Optional[User]:
        """
        Get user with their API keys loaded.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance with API keys or None if not found
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.api_keys))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_with_analyses(self, user_id: UUID) -> Optional[User]:
        """
        Get user with their contract analyses loaded.
        
        Args:
            user_id: User UUID
            
        Returns:
            User instance with contract analyses or None if not found
        """
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.contract_analyses))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def username_exists(self, username: str) -> bool:
        """
        Check if username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        return await self.exists(username=username)
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email to check
            
        Returns:
            True if email exists, False otherwise
        """
        return await self.exists(email=email)
    
    async def get_user_stats(self) -> dict:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        total_users = await self.count()
        active_users = await self.count(is_active=True)
        superusers = await self.count(is_superuser=True)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "superusers": superusers,
        }