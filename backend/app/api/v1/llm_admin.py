
from fastapi import APIRouter, Depends
from ...core.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/llm", tags=["llm-services"])

@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    return {
        "models": ["gpt-4", "gpt-3.5-turbo", "claude-3", "llama-2"],
        "message": "LLM models available"
    }

@router.get("/stats")
async def get_llm_stats(current_user: User = Depends(get_current_user)):
    return {"stats": {"requests": 0, "tokens_used": 0}, "message": "LLM usage statistics ready"}
