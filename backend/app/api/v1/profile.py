from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.dependencies import User, get_current_user
from app.schemas.api_models import SuccessResponse, UserProfileUpdate
from app.schemas.user import UserResponse
from app.services.user_settings_service import get_user_settings_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
	"""Get current user's profile information."""
	try:
		return current_user
	except Exception as e:
		logger.error(f"Error getting user profile: {e}")
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user profile")


@router.put("/", response_model=SuccessResponse)
async def update_profile(profile_update: UserProfileUpdate, current_user: User = Depends(get_current_user)):
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
