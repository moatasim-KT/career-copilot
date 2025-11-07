
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/email", tags=["email-service"])

@router.get("/templates")
async def list_email_templates(current_user: User = Depends(get_current_user)):
    return {"templates": [], "total": 0, "message": "Email templates ready"}

@router.get("/history")
async def get_email_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"history": [], "total": 0, "message": "Email history ready"}
