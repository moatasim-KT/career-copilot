"""
API endpoints for user management and settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status

"""
API endpoints for user management and settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, User
from ...core.logging import get_logger
from ...schemas.api_models import (
	UserSettingsResponse,
	UserSettingsUpdate,
	UserProfileUpdate,
	PasswordChange,
	UserResponse,
	SuccessResponse,
	IntegrationSettingsResponse,
	AIModelPreferenceResponse,
	NotificationPreferencesResponse,
	RiskThresholdsResponse,
)
from ...services.user_settings_service import get_user_settings_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(current_user: User = Depends(get_current_user)):
	"""Get current user's settings and preferences."""
	try:
		settings_service = get_user_settings_service()
		settings = await settings_service.get_user_settings(current_user.id)

		if not settings:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User settings not found")

		return settings

	except Exception as e:
		logger.error(f"Error getting user settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user settings")


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(settings_update: UserSettingsUpdate, current_user: User = Depends(get_current_user)):
	"""Update current user's settings and preferences."""
	try:
		settings_service = get_user_settings_service()
		updated_settings = await settings_service.update_user_settings(current_user.id, settings_update)

		if not updated_settings:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user settings")

		return updated_settings

	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error updating user settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user settings")


@router.post("/me/settings/reset", response_model=UserSettingsResponse)
async def reset_user_settings(current_user: User = Depends(get_current_user)):
	"""Reset current user's settings to default values."""
	try:
		settings_service = get_user_settings_service()
		reset_settings = await settings_service.reset_user_settings(current_user.id)

		if not reset_settings:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to reset user settings")

		return reset_settings

	except Exception as e:
		logger.error(f"Error resetting user settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset user settings")


@router.get("/me/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
	"""Get current user's profile information."""
	try:
		return current_user

	except Exception as e:
		logger.error(f"Error getting user profile: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user profile")


@router.put("/me/profile", response_model=SuccessResponse)
async def update_user_profile(profile_update: UserProfileUpdate, current_user: User = Depends(get_current_user)):
	"""Update current user's profile information."""
	try:
		settings_service = get_user_settings_service()

		success = await settings_service.update_profile(current_user.id, username=profile_update.username, email=profile_update.email)

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user profile")

		return SuccessResponse(message="Profile updated successfully", data={"updated_fields": profile_update.model_dump(exclude_none=True)})

	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error updating user profile: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user profile")


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_password(password_change: PasswordChange, current_user: User = Depends(get_current_user)):
	"""Change current user's password."""
	try:
		settings_service = get_user_settings_service()

		success = await settings_service.change_password(current_user.id, password_change.current_password, password_change.new_password)

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to change password")

		return SuccessResponse(message="Password changed successfully")

	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error changing password: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to change password")


@router.get("/me/settings/ai-model", response_model=AIModelPreferenceResponse)
async def get_ai_model_preference(current_user: User = Depends(get_current_user)):
	"""Get current user's AI model preference."""
	try:
		settings_service = get_user_settings_service()
		ai_model = await settings_service.get_ai_model_preference(current_user.id)

		return AIModelPreferenceResponse(ai_model_preference=ai_model)

	except Exception as e:
		logger.error(f"Error getting AI model preference: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve AI model preference")


@router.get("/me/settings/notifications", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(current_user: User = Depends(get_current_user)):
	"""Get current user's notification preferences."""
	try:
		settings_service = get_user_settings_service()
		preferences = await settings_service.get_notification_preferences(current_user.id)

		return NotificationPreferencesResponse(notification_preferences=preferences)

	except Exception as e:
		logger.error(f"Error getting notification preferences: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve notification preferences")


@router.get("/me/settings/risk-thresholds", response_model=RiskThresholdsResponse)
async def get_risk_thresholds(current_user: User = Depends(get_current_user)):
	"""Get current user's risk threshold preferences."""
	try:
		settings_service = get_user_settings_service()
		thresholds = await settings_service.get_risk_thresholds(current_user.id)

		return RiskThresholdsResponse(risk_thresholds=thresholds)

	except Exception as e:
		logger.error(f"Error getting risk thresholds: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve risk thresholds")


@router.get("/me/settings/integrations", response_model=IntegrationSettingsResponse)
async def get_integration_settings(current_user: User = Depends(get_current_user)):
	"""Get current user's integration settings."""
	try:
		settings_service = get_user_settings_service()
		settings = await settings_service.get_integration_settings(current_user.id)

		return IntegrationSettingsResponse(integration_settings=settings)

	except Exception as e:
		logger.error(f"Error getting integration settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve integration settings")


@router.put("/me/settings/integrations/{integration_name}/{setting_key}", response_model=SuccessResponse)
async def update_integration_setting(
	integration_name: str,
	setting_key: str,
	setting_value: dict,  # Expecting {"value": actual_value}
	current_user: User = Depends(get_current_user),
):
	"""Update a specific integration setting."""
	try:
		settings_service = get_user_settings_service()

		success = await settings_service.update_integration_setting(current_user.id, integration_name, setting_key, setting_value.get("value"))

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update integration setting")

		return SuccessResponse(
			message=f"Integration setting updated: {integration_name}.{setting_key}",
			data={"integration": integration_name, "setting": setting_key, "value": setting_value.get("value")},
		)

	except Exception as e:
		logger.error(f"Error updating integration setting: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update integration setting")

from ...core.logging import get_logger
from ...schemas.api_models import (
	UserSettingsResponse,
	UserSettingsUpdate,
	UserProfileUpdate,
	PasswordChange,
	UserResponse,
	SuccessResponse,
	IntegrationSettingsResponse,
	AIModelPreferenceResponse,
	NotificationPreferencesResponse,
	RiskThresholdsResponse,
)
from ...services.user_settings_service import get_user_settings_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(current_user: User = Depends(get_current_user)):
	"""Get current user's settings and preferences."""
	try:
		settings_service = get_user_settings_service()
		settings = await settings_service.get_user_settings(current_user.id)

		if not settings:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User settings not found")

		return settings

	except Exception as e:
		logger.error(f"Error getting user settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user settings")


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(settings_update: UserSettingsUpdate, current_user: User = Depends(get_current_user)):
	"""Update current user's settings and preferences."""
	try:
		settings_service = get_user_settings_service()
		updated_settings = await settings_service.update_user_settings(current_user.id, settings_update)

		if not updated_settings:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user settings")

		return updated_settings

	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error updating user settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user settings")


@router.post("/me/settings/reset", response_model=UserSettingsResponse)
async def reset_user_settings(current_user: User = Depends(get_current_user)):
	"""Reset current user's settings to default values."""
	try:
		settings_service = get_user_settings_service()
		reset_settings = await settings_service.reset_user_settings(current_user.id)

		if not reset_settings:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to reset user settings")

		return reset_settings

	except Exception as e:
		logger.error(f"Error resetting user settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset user settings")


@router.get("/me/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
	"""Get current user's profile information."""
	try:
		return current_user

	except Exception as e:
		logger.error(f"Error getting user profile: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user profile")


@router.put("/me/profile", response_model=SuccessResponse)
async def update_user_profile(profile_update: UserProfileUpdate, current_user: User = Depends(get_current_user)):
	"""Update current user's profile information."""
	try:
		settings_service = get_user_settings_service()

		success = await settings_service.update_profile(current_user.id, username=profile_update.username, email=profile_update.email)

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user profile")

		return SuccessResponse(message="Profile updated successfully", data={"updated_fields": profile_update.model_dump(exclude_none=True)})

	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error updating user profile: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user profile")


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_password(password_change: PasswordChange, current_user: User = Depends(get_current_user)):
	"""Change current user's password."""
	try:
		settings_service = get_user_settings_service()

		success = await settings_service.change_password(current_user.id, password_change.current_password, password_change.new_password)

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to change password")

		return SuccessResponse(message="Password changed successfully")

	except ValueError as e:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.error(f"Error changing password: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to change password")


@router.get("/me/settings/ai-model", response_model=AIModelPreferenceResponse)
async def get_ai_model_preference(current_user: User = Depends(get_current_user)):
	"""Get current user's AI model preference."""
	try:
		settings_service = get_user_settings_service()
		ai_model = await settings_service.get_ai_model_preference(current_user.id)

		return AIModelPreferenceResponse(ai_model_preference=ai_model)

	except Exception as e:
		logger.error(f"Error getting AI model preference: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve AI model preference")


@router.get("/me/settings/notifications", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(current_user: User = Depends(get_current_user)):
	"""Get current user's notification preferences."""
	try:
		settings_service = get_user_settings_service()
		preferences = await settings_service.get_notification_preferences(current_user.id)

		return NotificationPreferencesResponse(notification_preferences=preferences)

	except Exception as e:
		logger.error(f"Error getting notification preferences: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve notification preferences")


@router.get("/me/settings/risk-thresholds", response_model=RiskThresholdsResponse)
async def get_risk_thresholds(current_user: User = Depends(get_current_user)):
	"""Get current user's risk threshold preferences."""
	try:
		settings_service = get_user_settings_service()
		thresholds = await settings_service.get_risk_thresholds(current_user.id)

		return RiskThresholdsResponse(risk_thresholds=thresholds)

	except Exception as e:
		logger.error(f"Error getting risk thresholds: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve risk thresholds")


@router.get("/me/settings/integrations", response_model=IntegrationSettingsResponse)
async def get_integration_settings(current_user: User = Depends(get_current_user)):
	"""Get current user's integration settings."""
	try:
		settings_service = get_user_settings_service()
		settings = await settings_service.get_integration_settings(current_user.id)

		return IntegrationSettingsResponse(integration_settings=settings)

	except Exception as e:
		logger.error(f"Error getting integration settings: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve integration settings")


@router.put("/me/settings/integrations/{integration_name}/{setting_key}", response_model=SuccessResponse)
async def update_integration_setting(
	integration_name: str,
	setting_key: str,
	setting_value: dict,  # Expecting {"value": actual_value}
	current_user: User = Depends(get_current_user),
):
	"""Update a specific integration setting."""
	try:
		settings_service = get_user_settings_service()

		success = await settings_service.update_integration_setting(current_user.id, integration_name, setting_key, setting_value.get("value"))

		if not success:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update integration setting")

		return SuccessResponse(
			message=f"Integration setting updated: {integration_name}.{setting_key}",
			data={"integration": integration_name, "setting": setting_key, "value": setting_value.get("value")},
		)

	except Exception as e:
		logger.error(f"Error updating integration setting: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update integration setting")
