"""User job preferences schemas"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class UserJobPreferencesCreate(BaseModel):
    preferred_sources: Optional[List[str]] = Field(default_factory=list, description="List of preferred job sources")
    disabled_sources: Optional[List[str]] = Field(default_factory=list, description="List of disabled job sources")
    source_priorities: Optional[Dict[str, float]] = Field(default_factory=dict, description="Custom source priority weights")
    auto_scraping_enabled: Optional[bool] = True
    max_jobs_per_source: Optional[int] = Field(default=10, ge=1, le=100)
    min_quality_threshold: Optional[float] = Field(default=60.0, ge=0.0, le=100.0)
    notify_on_high_match: Optional[bool] = True
    notify_on_new_sources: Optional[bool] = False

class UserJobPreferencesUpdate(BaseModel):
    preferred_sources: Optional[List[str]] = None
    disabled_sources: Optional[List[str]] = None
    source_priorities: Optional[Dict[str, float]] = None
    auto_scraping_enabled: Optional[bool] = None
    max_jobs_per_source: Optional[int] = Field(None, ge=1, le=100)
    min_quality_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    notify_on_high_match: Optional[bool] = None
    notify_on_new_sources: Optional[bool] = None

class UserJobPreferencesResponse(BaseModel):
    id: int
    user_id: int
    preferred_sources: List[str]
    disabled_sources: List[str]
    source_priorities: Dict[str, float]
    auto_scraping_enabled: bool
    max_jobs_per_source: int
    min_quality_threshold: float
    notify_on_high_match: bool
    notify_on_new_sources: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobSourceInfo(BaseModel):
    source: str
    display_name: str
    description: str
    is_available: bool
    requires_api_key: bool
    quality_score: Optional[float] = None
    job_count: Optional[int] = None
    success_rate: Optional[float] = None
    
class AvailableSourcesResponse(BaseModel):
    sources: List[JobSourceInfo]
    user_preferences: Optional[UserJobPreferencesResponse] = None