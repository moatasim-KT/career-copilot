
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

@router.get("")
async def list_feedback(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"feedback": [], "total": 0, "message": "Feedback system ready"}

@router.get("/stats")
async def get_feedback_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {
        "total_submissions": 0,
        "resolved": 0,
        "pending": 0,
        "message": "Feedback statistics ready"
    }
