"""
Pydantic schemas for job recommendation feedback
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


class JobRecommendationFeedbackCreate(BaseModel):
	"""Schema for creating job recommendation feedback"""

	job_id: int = Field(..., gt=0)
	is_helpful: bool = Field(..., description="True for thumbs up, False for thumbs down")
	comment: str | None = Field(None, max_length=1000, description="Optional comment about the recommendation")

	@field_validator("comment")
	def validate_comment(cls, v):
		if v is not None:
			v = v.strip()
			if not v:
				return None
		return v


class JobRecommendationFeedbackUpdate(BaseModel):
	"""Schema for updating job recommendation feedback"""

	is_helpful: bool | None = None
	comment: str | None = Field(None, max_length=1000)

	@field_validator("comment")
	def validate_comment(cls, v):
		if v is not None:
			v = v.strip()
			if not v:
				return None
		return v


class JobRecommendationFeedbackResponse(BaseModel):
	"""Schema for job recommendation feedback response"""

	id: int
	user_id: int
	job_id: int
	is_helpful: bool
	match_score: int | None
	comment: str | None

	# Context information (for debugging/analysis)
	user_skills_at_time: list[str] | None
	user_experience_level: str | None
	user_preferred_locations: list[str] | None
	job_tech_stack: list[str] | None
	job_location: str | None

	created_at: datetime
	model_config = {"from_attributes": True}


class JobRecommendationFeedbackSummary(BaseModel):
	"""Schema for job recommendation feedback summary"""

	job_id: int
	total_feedback_count: int
	helpful_count: int
	unhelpful_count: int
	helpful_percentage: float
	model_config = {"from_attributes": True}


class FeedbackAnalytics(BaseModel):
	"""Schema for feedback analytics"""

	total_feedback_count: int
	helpful_count: int
	unhelpful_count: int
	helpful_percentage: float

	# Breakdown by context
	feedback_by_experience_level: dict[str, dict[str, int]]
	feedback_by_skill_match: dict[str, dict[str, int]]  # High/Medium/Low skill match
	feedback_by_location_match: dict[str, dict[str, int]]  # Exact/Partial/No match

	# Recent trends
	recent_feedback_trend: list[dict[str, Any]]  # Daily feedback counts over time

	model_config = {"from_attributes": True}


class BulkFeedbackCreate(BaseModel):
	"""Schema for creating multiple feedback items at once"""

	feedback_items: list[JobRecommendationFeedbackCreate] = Field(..., min_length=1, max_length=50)

	@field_validator("feedback_items")
	def validate_unique_jobs(cls, v):
		job_ids = [item.job_id for item in v]
		if len(job_ids) != len(set(job_ids)):
			raise ValueError("Duplicate job_ids are not allowed in bulk feedback")
		return v
