
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/cache", tags=["cache-admin"])

@router.get("/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    return {"stats": {"hits": 0, "misses": 0}, "message": "Cache statistics ready"}

@router.get("/health")
async def get_cache_health(current_user: User = Depends(get_current_user)):
    return {"status": "healthy", "message": "Cache health check ready"}
