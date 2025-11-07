
from fastapi import APIRouter, Depends
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/status", tags=["realtime-status"])

@router.get("/current")
async def get_current_status(current_user: User = Depends(get_current_user)):
    return {"status": "active", "message": "Current status ready"}

@router.get("/updates")
async def get_status_updates(current_user: User = Depends(get_current_user)):
    return {"updates": [], "message": "Status updates ready"}
