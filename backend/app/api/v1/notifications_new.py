
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.notification import Notification
from ...schemas.api_models import NotificationPreferences

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("")
async def list_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List all notifications for the current user."""
    result = await db.execute(select(Notification).where(Notification.user_id == current_user.id))
    notifications = result.scalars().all()
    unread_count = sum(1 for n in notifications if not n.is_read)
    return {"notifications": notifications, "total": len(notifications), "unread": unread_count}

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
    result = await db.execute(select(Notification).where(Notification.user_id == current_user.id, Notification.is_read == False))
    notifications = result.scalars().all()
    return {"unread": notifications, "count": len(notifications)}
