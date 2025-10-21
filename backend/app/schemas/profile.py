"""
User profile schemas for Career Co-Pilot system
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SkillBase(BaseModel):
    """Base skill schema"""
    name: str = Field(..., min_length=1, max_length=100)
    level: str = Field(..., pattern="^(beginner|intermediate|advanced|expert)$")
    years_experience: Optional[int] = Field(None, ge=0, le=50)


class LocationPreference(BaseModel):
    """Location preference schema"""
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: str = Field(..., min_length=1, max_length=100)
    is_remote: bool = False


class CareerPreferences(BaseModel):
    """Career preferences schema"""
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    company_sizes: List[str] = Field(default_factory=list)  # startup, small, medium, large, enterprise
    industries: List[str] = Field(default_factory=list)
    job_types: List[str] = Field(default_factory=list)  # full_time, part_time, contract, freelance
    remote_preference: str = Field(default="hybrid", pattern="^(remote|hybrid|onsite)$")
    travel_willingness: str = Field(default="minimal", pattern="^(none|minimal|moderate|frequent)$")


class CareerGoals(BaseModel):
    """Career goals schema"""
    target_roles: List[str] = Field(default_factory=list)
    career_level: str = Field(default="mid", pattern="^(entry|junior|mid|senior|lead|principal|executive)$")
    time_horizon: str = Field(default="1_year", pattern="^(6_months|1_year|2_years|5_years|long_term)$")
    learning_goals: List[str] = Field(default_factory=list)
    certifications_desired: List[str] = Field(default_factory=list)


class NotificationSettings(BaseModel):
    """Notification settings schema"""
    morning_briefing: bool = True
    evening_summary: bool = True
    job_recommendations: bool = True
    application_reminders: bool = True
    interview_reminders: bool = True
    email_time: str = Field(default="08:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = Field(default="UTC", max_length=50)


class UIPreferences(BaseModel):
    """UI preferences schema"""
    theme: str = Field(default="light", pattern="^(light|dark|auto)$")
    dashboard_layout: str = Field(default="default", pattern="^(compact|default|detailed)$")
    items_per_page: int = Field(default=20, ge=10, le=100)
    default_job_view: str = Field(default="cards", pattern="^(cards|list|table)$")


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    # Personal information
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    
    # Professional information
    current_title: Optional[str] = Field(None, max_length=200)
    current_company: Optional[str] = Field(None, max_length=200)
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    education_level: Optional[str] = Field(None, pattern="^(high_school|associate|bachelor|master|phd|other)$")
    
    # Skills and preferences
    skills: Optional[List[SkillBase]] = None
    location_preferences: Optional[List[LocationPreference]] = None
    career_preferences: Optional[CareerPreferences] = None
    career_goals: Optional[CareerGoals] = None


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings"""
    notifications: Optional[NotificationSettings] = None
    ui_preferences: Optional[UIPreferences] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    # Personal information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None
    
    # Professional information
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_experience: Optional[int] = None
    education_level: Optional[str] = None
    
    # Skills and preferences
    skills: List[SkillBase] = Field(default_factory=list)
    location_preferences: List[LocationPreference] = Field(default_factory=list)
    career_preferences: CareerPreferences = Field(default_factory=CareerPreferences)
    career_goals: CareerGoals = Field(default_factory=CareerGoals)
    
    # Metadata
    profile_completion: int = Field(default=0, ge=0, le=100)
    last_updated: Optional[datetime] = None


class ApplicationHistoryItem(BaseModel):
    """Schema for application history item"""
    id: int
    job_id: int
    job_title: str
    company_name: str
    status: str
    applied_at: datetime
    response_date: Optional[datetime] = None
    notes: Optional[str] = None
    documents_count: int = 0
    interview_rounds: int = 0


class ApplicationHistoryResponse(BaseModel):
    """Schema for application history response"""
    applications: List[ApplicationHistoryItem]
    total_count: int
    page: int
    per_page: int
    
    # Summary statistics
    total_applications: int
    applications_this_month: int
    interviews_scheduled: int
    offers_received: int
    success_rate: float


class ProgressTrackingStats(BaseModel):
    """Schema for progress tracking statistics"""
    # Application metrics
    total_applications: int
    applications_this_week: int
    applications_this_month: int
    
    # Response metrics
    response_rate: float
    interview_rate: float
    offer_rate: float
    
    # Timeline metrics
    avg_response_time_days: Optional[float] = None
    fastest_response_days: Optional[int] = None
    
    # Goal tracking
    weekly_application_goal: int = 5
    weekly_applications_completed: int = 0
    goal_completion_rate: float = 0.0
    
    # Goal progress metrics
    active_goals_count: int = 0
    completed_goals_this_month: int = 0
    current_streak_days: int = 0
    milestones_achieved_this_month: int = 0
    
    # Trend data (last 12 weeks)
    weekly_application_trend: List[Dict[str, Any]] = Field(default_factory=list)
    status_distribution: Dict[str, int] = Field(default_factory=dict)


class DocumentSummary(BaseModel):
    """Schema for document summary"""
    id: int
    filename: str
    document_type: str
    file_size: int
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime


class DocumentManagementResponse(BaseModel):
    """Schema for document management response"""
    documents: List[DocumentSummary]
    total_count: int
    
    # Document statistics
    total_documents: int
    documents_by_type: Dict[str, int] = Field(default_factory=dict)
    total_storage_used: int = 0  # in bytes
    most_used_document: Optional[DocumentSummary] = None