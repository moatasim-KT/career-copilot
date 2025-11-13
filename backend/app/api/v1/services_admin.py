
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/services", tags=["external-services"])

@router.get("/status")
async def get_services_status(current_user: User = Depends(get_current_user)):
    return {"services": [], "all_healthy": True, "message": "Services status ready"}

@router.get("/health")
async def get_services_health(current_user: User = Depends(get_current_user)):
    return {"status": "healthy", "services": [], "message": "Services health check ready"}
