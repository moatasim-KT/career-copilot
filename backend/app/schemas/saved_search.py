from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class SavedSearchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    filters: Dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False

class SavedSearchCreate(SavedSearchBase):
    pass

class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    filters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

class SavedSearchResponse(SavedSearchBase):
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_used: datetime

    class Config:
        from_attributes = True