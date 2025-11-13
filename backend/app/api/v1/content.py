
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from app.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/content", tags=["content-generation"])

@router.get("")
async def list_content_generations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"content": [], "total": 0, "message": "Content generation system ready"}

@router.get("/types")
async def get_content_types():
    return {
        "types": ["cover_letter", "resume_summary", "linkedin_post", "email", "interview_prep"],
        "message": "Content types available"
    }
