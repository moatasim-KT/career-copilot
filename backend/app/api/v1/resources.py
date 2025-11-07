
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/resources", tags=["career-resources"])

@router.get("")
async def list_resources(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"resources": [], "total": 0, "message": "Career resources system ready"}

@router.get("/categories")
async def get_resource_categories():
    return {
        "categories": ["resume_templates", "interview_guides", "salary_data", "career_advice"],
        "message": "Resource categories available"
    }

@router.get("/bookmarks")
async def get_user_bookmarks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"bookmarks": [], "total": 0, "message": "User bookmarks ready"}
