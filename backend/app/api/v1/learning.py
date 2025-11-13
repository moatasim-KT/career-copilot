
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from app.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/learning", tags=["learning-paths"])

@router.get("/paths")
async def list_learning_paths(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"paths": [], "total": 0, "message": "Learning paths system ready"}

@router.get("/enrollments")
async def get_user_enrollments(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"enrollments": [], "total": 0, "message": "User enrollments ready"}

@router.get("/progress")
async def get_learning_progress(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"progress": [], "message": "Learning progress tracking ready"}
