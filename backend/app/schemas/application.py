"""Application schemas"""

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date


class ApplicationCreate(BaseModel):
    job_id: int
    status: Optional[Literal["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"]] = "interested"
    applied_date: Optional[date] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[Literal["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"]] = None
    response_date: Optional[date] = None
    interview_date: Optional[datetime] = None
    offer_date: Optional[date] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    status: str
    applied_date: Optional[date]
    response_date: Optional[date]
    interview_date: Optional[datetime]
    offer_date: Optional[date]
    notes: Optional[str]
    follow_up_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
