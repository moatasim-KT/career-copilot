
from fastapi import APIRouter, Depends
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/vector-store", tags=["vector-store"])

@router.get("/collections")
async def list_collections(current_user: User = Depends(get_current_user)):
    return {"collections": [], "total": 0, "message": "Vector store collections ready"}

@router.get("/stats")
async def get_vector_stats(current_user: User = Depends(get_current_user)):
    return {"stats": {"documents": 0, "embeddings": 0}, "message": "Vector store statistics ready"}
