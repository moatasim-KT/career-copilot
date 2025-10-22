"""Pydantic schemas for User Profile"""

from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal

class ProfileBase(BaseModel):
    skills: Optional[List[str]] = []
    preferred_locations: Optional[List[str]] = []
    experience_level: Optional[Literal["junior", "mid", "senior"]] = None
    daily_application_goal: Optional[int] = None

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True  # Pydantic v2 syntax (replaces orm_mode)
