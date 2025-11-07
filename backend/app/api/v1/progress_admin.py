
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/progress", tags=["progress-tracking"])

@router.get("")
async def get_overall_progress(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"progress": {"total": 0, "completed": 0}, "message": "Progress tracking ready"}

@router.get("/daily")
async def get_daily_progress(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"daily_progress": [], "message": "Daily progress tracking ready"}
