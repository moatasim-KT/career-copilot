
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from app.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/storage", tags=["file-storage"])

@router.get("/files")
async def list_files(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"files": [], "total": 0, "message": "File storage system ready"}

@router.get("/stats")
async def get_storage_stats(current_user: User = Depends(get_current_user)):
    return {"total_size": 0, "file_count": 0, "message": "Storage statistics ready"}
