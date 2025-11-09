from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...schemas.api_models import NotificationPreferences

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""List all notifications for the current user."""
	# The project currently stores notification-like data in user settings or via
	# the scheduled notification service. There is no dedicated Notification ORM
	# model in `app.models`. To avoid import errors in development, return a
	# best-effort view from the user's settings (if present) and fall back to an
	# empty list.
	stored = getattr(current_user, "settings", {}) or {}
	notifications = stored.get("notifications_list", [])
	# compute a simple unread count if items have an `is_read` flag
	unread_count = sum(1 for n in notifications if not n.get("is_read")) if isinstance(notifications, list) else 0
	return {"notifications": notifications, "total": len(notifications) if isinstance(notifications, list) else 0, "unread": unread_count}


@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get the current user's notification preferences."""
	# In a real application, you would fetch this from the user's settings
	return NotificationPreferences(
		email=current_user.notification_preferences.get("email", True),
		push=current_user.notification_preferences.get("push", False),
		sms=current_user.notification_preferences.get("sms", False),
	)


@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
	preferences: NotificationPreferences, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""Update the current user's notification preferences."""
	current_user.notification_preferences = preferences.dict()
	db.add(current_user)
	await db.commit()
	return preferences


@router.get("/unread")
async def get_unread_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get a list of unread notifications for the current user."""
	stored = getattr(current_user, "settings", {}) or {}
	notifications = stored.get("notifications_list", [])
	unread = [n for n in notifications if not n.get("is_read")] if isinstance(notifications, list) else []
	return {"unread": unread, "count": len(unread)}
