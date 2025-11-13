"""Pydantic schemas for User Profile"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
	skills: list[str] | None = []
	preferred_locations: list[str] | None = []
	experience_level: Literal["junior", "mid", "senior"] | None = None
	daily_application_goal: int | None = None


class ProfileUpdate(ProfileBase):
	pass


class ProfileResponse(ProfileBase):
	id: int
	username: str
	email: str

	model_config = {"from_attributes": True}


# Extended profile schemas for profile service
class UserProfileUpdate(BaseModel):
	"""Schema for updating user profile"""
	first_name: Optional[str] = None
	last_name: Optional[str] = None
	phone: Optional[str] = None
	linkedin_url: Optional[str] = None
	portfolio_url: Optional[str] = None
	github_url: Optional[str] = None
	current_title: Optional[str] = None
	current_company: Optional[str] = None
	years_experience: Optional[int] = None
	education_level: Optional[str] = None
	skills: Optional[List[str]] = None
	location_preferences: Optional[List[str]] = None
	career_preferences: Optional[Dict[str, Any]] = None
	career_goals: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
	"""Schema for user profile response"""
	first_name: Optional[str] = None
	last_name: Optional[str] = None
	phone: Optional[str] = None
	linkedin_url: Optional[str] = None
	portfolio_url: Optional[str] = None
	github_url: Optional[str] = None
	current_title: Optional[str] = None
	current_company: Optional[str] = None
	years_experience: Optional[int] = None
	education_level: Optional[str] = None
	skills: List[str] = Field(default_factory=list)
	location_preferences: List[str] = Field(default_factory=list)
	career_preferences: Dict[str, Any] = Field(default_factory=dict)
	career_goals: Dict[str, Any] = Field(default_factory=dict)
	profile_completion: int = 0
	last_updated: Optional[datetime] = None


class UserSettingsUpdate(BaseModel):
	"""Schema for updating user settings"""
	email_notifications: Optional[bool] = None
	push_notifications: Optional[bool] = None
	theme: Optional[str] = None
	language: Optional[str] = None
	timezone: Optional[str] = None


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
	total_applications: int
	applications_this_month: int
	interviews_scheduled: int
	offers_received: int
	success_rate: float


class ProgressTrackingStats(BaseModel):
	"""Schema for progress tracking statistics"""
	total_applications: int
	applications_this_week: int
	applications_this_month: int
	response_rate: float
	interview_rate: float
	offer_rate: float
	avg_response_time_days: Optional[float] = None
	fastest_response_days: Optional[int] = None
	weekly_application_goal: int
	weekly_applications_completed: int
	goal_completion_rate: float
	active_goals_count: int
	completed_goals_this_month: int
	current_streak_days: int
	milestones_achieved_this_month: int
	weekly_application_trend: List[Dict[str, Any]]
	status_distribution: Dict[str, int]


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
	total_documents: int
	documents_by_type: Dict[str, int]
	total_storage_used: int
	most_used_document: Optional[DocumentSummary] = None
