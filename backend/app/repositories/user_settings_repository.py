"""
User settings repository for managing user preferences and configuration.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database_models import UserSettings
from .base_repository import BaseRepository


class UserSettingsRepository(BaseRepository[UserSettings]):
	"""Repository for user settings operations."""

	def __init__(self, session: AsyncSession):
		super().__init__(UserSettings, session)

	async def get_by_user_id(self, user_id: UUID) -> Optional[UserSettings]:
		"""
		Get user settings by user ID.

		Args:
		    user_id: User UUID

		Returns:
		    UserSettings instance or None if not found
		"""
		return await self.get_by_field("user_id", user_id)

	async def create_default_settings(self, user_id: UUID) -> UserSettings:
		"""
		Create default settings for a new user.

		Args:
		    user_id: User UUID

		Returns:
		    Created UserSettings instance
		"""
		return await self.create(user_id=user_id)

	async def update_settings(self, user_id: UUID, **settings_data) -> Optional[UserSettings]:
		"""
		Update user settings.

		Args:
		    user_id: User UUID
		    **settings_data: Settings fields to update

		Returns:
		    Updated UserSettings instance or None if not found
		"""
		# First, try to get existing settings
		existing_settings = await self.get_by_user_id(user_id)

		if existing_settings:
			# Update existing settings
			return await self.update_by_id(existing_settings.id, **settings_data)
		else:
			# Create new settings with provided data
			return await self.create(user_id=user_id, **settings_data)

	async def get_ai_model_preference(self, user_id: UUID) -> str:
		"""
		Get user's AI model preference.

		Args:
		    user_id: User UUID

		Returns:
		    AI model preference or default value
		"""
		settings = await self.get_by_user_id(user_id)
		return settings.ai_model_preference if settings else "gpt-3.5-turbo"

	async def get_analysis_depth(self, user_id: UUID) -> str:
		"""
		Get user's analysis depth preference.

		Args:
		    user_id: User UUID

		Returns:
		    Analysis depth preference or default value
		"""
		settings = await self.get_by_user_id(user_id)
		return settings.analysis_depth if settings else "normal"

	async def get_notification_preferences(self, user_id: UUID) -> dict:
		"""
		Get user's notification preferences.

		Args:
		    user_id: User UUID

		Returns:
		    Dictionary with notification preferences
		"""
		settings = await self.get_by_user_id(user_id)

		if settings:
			return {
				"email_notifications_enabled": settings.email_notifications_enabled,
				"slack_notifications_enabled": settings.slack_notifications_enabled,
				"docusign_notifications_enabled": settings.docusign_notifications_enabled,
			}
		else:
			return {
				"email_notifications_enabled": True,
				"slack_notifications_enabled": True,
				"docusign_notifications_enabled": True,
			}

	async def get_risk_thresholds(self, user_id: UUID) -> dict:
		"""
		Get user's risk threshold preferences.

		Args:
		    user_id: User UUID

		Returns:
		    Dictionary with risk thresholds
		"""
		settings = await self.get_by_user_id(user_id)

		if settings:
			return {
				"low": float(settings.risk_threshold_low),
				"medium": float(settings.risk_threshold_medium),
				"high": float(settings.risk_threshold_high),
			}
		else:
			return {
				"low": 0.30,
				"medium": 0.60,
				"high": 0.80,
			}

	async def get_ui_preferences(self, user_id: UUID) -> dict:
		"""
		Get user's UI/UX preferences.

		Args:
		    user_id: User UUID

		Returns:
		    Dictionary with UI preferences
		"""
		settings = await self.get_by_user_id(user_id)

		if settings:
			return {
				"preferred_language": settings.preferred_language,
				"timezone": settings.timezone,
				"theme_preference": settings.theme_preference,
				"dashboard_layout": settings.dashboard_layout,
			}
		else:
			return {
				"preferred_language": "en",
				"timezone": "UTC",
				"theme_preference": "light",
				"dashboard_layout": None,
			}

	async def get_integration_settings(self, user_id: UUID) -> dict:
		"""
		Get user's integration settings.

		Args:
		    user_id: User UUID

		Returns:
		    Dictionary with integration settings
		"""
		settings = await self.get_by_user_id(user_id)
		return settings.integration_settings if settings and settings.integration_settings else {}

	async def update_integration_setting(self, user_id: UUID, integration_name: str, setting_key: str, setting_value: any) -> Optional[UserSettings]:
		"""
		Update a specific integration setting.

		Args:
		    user_id: User UUID
		    integration_name: Name of the integration (e.g., 'slack', 'docusign')
		    setting_key: Setting key to update
		    setting_value: New setting value

		Returns:
		    Updated UserSettings instance or None if not found
		"""
		settings = await self.get_by_user_id(user_id)

		if not settings:
			# Create new settings with integration setting
			integration_settings = {integration_name: {setting_key: setting_value}}
			return await self.create(user_id=user_id, integration_settings=integration_settings)

		# Update existing integration settings
		current_integration_settings = settings.integration_settings or {}

		if integration_name not in current_integration_settings:
			current_integration_settings[integration_name] = {}

		current_integration_settings[integration_name][setting_key] = setting_value

		return await self.update_by_id(settings.id, integration_settings=current_integration_settings)

	async def reset_to_defaults(self, user_id: UUID) -> Optional[UserSettings]:
		"""
		Reset user settings to default values.

		Args:
		    user_id: User UUID

		Returns:
		    Updated UserSettings instance or None if not found
		"""
		default_settings = {
			"ai_model_preference": "gpt-3.5-turbo",
			"analysis_depth": "normal",
			"email_notifications_enabled": True,
			"slack_notifications_enabled": True,
			"docusign_notifications_enabled": True,
			"risk_threshold_low": 0.30,
			"risk_threshold_medium": 0.60,
			"risk_threshold_high": 0.80,
			"auto_generate_redlines": True,
			"auto_generate_email_drafts": True,
			"preferred_language": "en",
			"timezone": "UTC",
			"theme_preference": "light",
			"dashboard_layout": None,
			"integration_settings": None,
		}

		return await self.update_settings(user_id, **default_settings)
