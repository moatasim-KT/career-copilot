
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("")
async def list_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"notifications": [], "total": 0, "unread": 0, "message": "Notifications system ready"}

@router.get("/preferences")
async def get_notification_preferences(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {
        "preferences": {
            "email": True,
            "push": False,
            "sms": False
        },
        "message": "Notification preferences ready"
    }

@router.get("/unread")
async def get_unread_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"unread": [], "count": 0, "message": "Unread notifications ready"}
