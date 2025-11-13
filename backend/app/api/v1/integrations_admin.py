from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from ...models.user import User

router = APIRouter()


@router.get("")
async def list_integrations(current_user: User = Depends(get_current_user)):
	return {"integrations": [], "total": 0, "message": "System integrations ready"}


@router.get("/health")
async def get_integrations_health(current_user: User = Depends(get_current_user)):
	return {"status": "healthy", "integrations": [], "message": "Integrations health check ready"}
