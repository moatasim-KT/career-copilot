
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/help", tags=["help"])

@router.get("/articles")
async def list_help_articles(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"articles": [], "total": 0, "message": "Help articles system ready"}

@router.get("/search")
async def search_help_articles(q: str, current_user: User = Depends(get_current_user)):
    return {"results": [], "query": q, "message": "Help search ready"}
