"""
User Settings Service
Handles user preferences, configuration, and profile management.
"""

from typing import Dict, Optional
from uuid import UUID

from ..core.database import get_database_manager
from ..core.logging import get_logger
from ..models.api_models import UserSettings, UserSettingsResponse, UserSettingsUpdate
from ..models.database_models import UserSettings as DBUserSettings
from ..repositories.user_settings_repository import UserSettingsRepository
from ..repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserSettingsService:
    """Service for managing user settings and preferences."""
    
    def __init__(self):
        """Initialize user settings service."""
        logger.info("User settings service initialized")
    
    async def get_user_settings(self, user_id: UUID) -> Optional[UserSettingsResponse]:
        """
        Get user settings by user ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            UserSettingsResponse or None if not found
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                settings = await settings_repo.get_by_user_id(user_id)
                
                if not settings:
                    # Create default settings for the user
                    settings = await settings_repo.create_default_settings(user_id)
                    await session.commit()
                
                return UserSettingsResponse.model_validate(settings)
                
        except Exception as e:
            logger.error(f"Error getting user settings for user {user_id}: {e}")
            return None
    
    async def update_user_settings(
        self, 
        user_id: UUID, 
        settings_update: UserSettingsUpdate
    ) -> Optional[UserSettingsResponse]:
        """
        Update user settings.
        
        Args:
            user_id: User UUID
            settings_update: Settings update data
            
        Returns:
            Updated UserSettingsResponse or None if failed
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                
                # Convert update model to dict, excluding None values
                update_data = settings_update.model_dump(exclude_none=True)
                
                if not update_data:
                    # No updates provided, return current settings
                    return await self.get_user_settings(user_id)
                
                # Validate risk thresholds if provided
                if self._has_risk_threshold_updates(update_data):
                    current_settings = await settings_repo.get_by_user_id(user_id)
                    if not self._validate_risk_thresholds(update_data, current_settings):
                        raise ValueError("Invalid risk threshold configuration")
                
                # Update settings
                updated_settings = await settings_repo.update_settings(user_id, **update_data)
                
                if updated_settings:
                    await session.commit()
                    logger.info(f"Updated settings for user {user_id}")
                    return UserSettingsResponse.model_validate(updated_settings)
                else:
                    logger.error(f"Failed to update settings for user {user_id}")
                    return None
                
        except Exception as e:
            logger.error(f"Error updating user settings for user {user_id}: {e}")
            return None
    
    async def reset_user_settings(self, user_id: UUID) -> Optional[UserSettingsResponse]:
        """
        Reset user settings to default values.
        
        Args:
            user_id: User UUID
            
        Returns:
            Reset UserSettingsResponse or None if failed
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                
                reset_settings = await settings_repo.reset_to_defaults(user_id)
                
                if reset_settings:
                    await session.commit()
                    logger.info(f"Reset settings to defaults for user {user_id}")
                    return UserSettingsResponse.model_validate(reset_settings)
                else:
                    logger.error(f"Failed to reset settings for user {user_id}")
                    return None
                
        except Exception as e:
            logger.error(f"Error resetting user settings for user {user_id}: {e}")
            return None
    
    async def get_ai_model_preference(self, user_id: UUID) -> str:
        """
        Get user's AI model preference.
        
        Args:
            user_id: User UUID
            
        Returns:
            AI model preference
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                return await settings_repo.get_ai_model_preference(user_id)
                
        except Exception as e:
            logger.error(f"Error getting AI model preference for user {user_id}: {e}")
            return "gpt-3.5-turbo"  # Default fallback
    
    async def get_analysis_depth(self, user_id: UUID) -> str:
        """
        Get user's analysis depth preference.
        
        Args:
            user_id: User UUID
            
        Returns:
            Analysis depth preference
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                return await settings_repo.get_analysis_depth(user_id)
                
        except Exception as e:
            logger.error(f"Error getting analysis depth for user {user_id}: {e}")
            return "normal"  # Default fallback
    
    async def get_notification_preferences(self, user_id: UUID) -> Dict[str, bool]:
        """
        Get user's notification preferences.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary with notification preferences
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                return await settings_repo.get_notification_preferences(user_id)
                
        except Exception as e:
            logger.error(f"Error getting notification preferences for user {user_id}: {e}")
            return {
                "email_notifications_enabled": True,
                "slack_notifications_enabled": True,
                "docusign_notifications_enabled": True,
            }
    
    async def get_risk_thresholds(self, user_id: UUID) -> Dict[str, float]:
        """
        Get user's risk threshold preferences.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary with risk thresholds
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                return await settings_repo.get_risk_thresholds(user_id)
                
        except Exception as e:
            logger.error(f"Error getting risk thresholds for user {user_id}: {e}")
            return {"low": 0.30, "medium": 0.60, "high": 0.80}
    
    async def update_profile(
        self, 
        user_id: UUID, 
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> bool:
        """
        Update user profile information.
        
        Args:
            user_id: User UUID
            username: New username (optional)
            email: New email (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                user_repo = UserRepository(session)
                
                # Check if username/email already exist
                if username:
                    if await user_repo.username_exists(username):
                        existing_user = await user_repo.get_by_username(username)
                        if existing_user and existing_user.id != user_id:
                            raise ValueError("Username already exists")
                
                if email:
                    if await user_repo.email_exists(email):
                        existing_user = await user_repo.get_by_email(email)
                        if existing_user and existing_user.id != user_id:
                            raise ValueError("Email already exists")
                
                # Update user profile
                update_data = {}
                if username:
                    update_data["username"] = username
                if email:
                    update_data["email"] = email
                
                if update_data:
                    updated_user = await user_repo.update_by_id(user_id, **update_data)
                    if updated_user:
                        await session.commit()
                        logger.info(f"Updated profile for user {user_id}")
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}")
            return False
    
    async def change_password(
        self, 
        user_id: UUID, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User UUID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from ..services.authentication_service import get_authentication_service
            
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                user_repo = UserRepository(session)
                auth_service = get_authentication_service()
                
                # Get user
                user = await user_repo.get_by_id(user_id)
                if not user:
                    return False
                
                # Verify current password
                if not auth_service._verify_password(current_password, user.hashed_password):
                    raise ValueError("Current password is incorrect")
                
                # Hash new password
                new_password_hash = auth_service.hash_password(new_password)
                
                # Update password
                updated_user = await user_repo.update_password(user_id, new_password_hash)
                
                if updated_user:
                    await session.commit()
                    logger.info(f"Password changed for user {user_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False
    
    async def get_integration_settings(self, user_id: UUID) -> Dict:
        """
        Get user's integration settings.
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary with integration settings
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                return await settings_repo.get_integration_settings(user_id)
                
        except Exception as e:
            logger.error(f"Error getting integration settings for user {user_id}: {e}")
            return {}
    
    async def update_integration_setting(
        self, 
        user_id: UUID, 
        integration_name: str, 
        setting_key: str, 
        setting_value: any
    ) -> bool:
        """
        Update a specific integration setting.
        
        Args:
            user_id: User UUID
            integration_name: Name of the integration
            setting_key: Setting key to update
            setting_value: New setting value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db_manager = await get_database_manager()
            async with db_manager.get_session() as session:
                settings_repo = UserSettingsRepository(session)
                
                updated_settings = await settings_repo.update_integration_setting(
                    user_id, integration_name, setting_key, setting_value
                )
                
                if updated_settings:
                    await session.commit()
                    logger.info(f"Updated integration setting for user {user_id}: {integration_name}.{setting_key}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating integration setting for user {user_id}: {e}")
            return False
    
    def _has_risk_threshold_updates(self, update_data: Dict) -> bool:
        """Check if update contains risk threshold changes."""
        risk_fields = ["risk_threshold_low", "risk_threshold_medium", "risk_threshold_high"]
        return any(field in update_data for field in risk_fields)
    
    def _validate_risk_thresholds(
        self, 
        update_data: Dict, 
        current_settings: Optional[DBUserSettings]
    ) -> bool:
        """Validate risk threshold configuration."""
        # Get current values or defaults
        current_low = float(current_settings.risk_threshold_low) if current_settings else 0.30
        current_medium = float(current_settings.risk_threshold_medium) if current_settings else 0.60
        current_high = float(current_settings.risk_threshold_high) if current_settings else 0.80
        
        # Apply updates
        low = update_data.get("risk_threshold_low", current_low)
        medium = update_data.get("risk_threshold_medium", current_medium)
        high = update_data.get("risk_threshold_high", current_high)
        
        # Validate thresholds are in ascending order
        return low < medium < high and 0.0 <= low <= 1.0 and 0.0 <= medium <= 1.0 and 0.0 <= high <= 1.0


# Global instance
_user_settings_service = None


def get_user_settings_service() -> UserSettingsService:
    """Get global user settings service instance."""
    global _user_settings_service
    if _user_settings_service is None:
        _user_settings_service = UserSettingsService()
    return _user_settings_service