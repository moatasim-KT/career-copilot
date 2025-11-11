"""
Test to verify that both dependency implementations return consistent users.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user as get_current_user_main
from app.core.dependencies import get_current_user as get_current_user_core
from app.models.user import User


@pytest.mark.asyncio
async def test_dependency_consistency(db: AsyncSession):
    """Test that both get_current_user implementations return the same user."""
    # Get user from main dependencies
    user_main = await get_current_user_main(db)
    
    # Get user from core dependencies
    user_core = await get_current_user_core(db)
    
    # Verify they return the same user
    assert user_main.id == user_core.id, "Both implementations should return the same user ID"
    assert user_main.email == user_core.email, "Both implementations should return the same email"
    assert user_main.username == user_core.username, "Both implementations should return the same username"


@pytest.mark.asyncio
async def test_get_current_user_returns_moatasim(db: AsyncSession):
    """Test that get_current_user returns the Moatasim user."""
    user = await get_current_user_main(db)
    
    assert user is not None, "User should not be None"
    assert isinstance(user, User), "Should return a User instance"
    # Should be Moatasim's user or the first user in the database
    assert user.email in ["moatasimfarooque@gmail.com"] or user.id == 1


@pytest.mark.asyncio
async def test_get_current_user_optional(db: AsyncSession):
    """Test that get_current_user_optional works correctly."""
    from app.dependencies import get_current_user_optional
    
    user = await get_current_user_optional(db)
    
    # Should return a user or None (depending on database state)
    if user is not None:
        assert isinstance(user, User), "Should return a User instance if user exists"


@pytest.mark.asyncio
async def test_get_admin_user(db: AsyncSession):
    """Test that get_admin_user returns the current user."""
    from app.dependencies import get_admin_user, get_current_user
    
    current_user = await get_current_user(db)
    admin_user = await get_admin_user(current_user)
    
    assert admin_user.id == current_user.id, "Admin user should be the same as current user"
    assert admin_user.email == current_user.email, "Admin user should have the same email"
