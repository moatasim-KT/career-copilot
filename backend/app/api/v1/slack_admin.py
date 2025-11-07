
from fastapi import APIRouter, Depends
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/slack", tags=["slack-integration"])

@router.get("/channels")
async def list_slack_channels(current_user: User = Depends(get_current_user)):
    return {"channels": [], "total": 0, "message": "Slack channels ready"}

@router.get("/status")
async def get_slack_status(current_user: User = Depends(get_current_user)):
    return {"status": "configured", "connected": False, "message": "Slack status ready"}
