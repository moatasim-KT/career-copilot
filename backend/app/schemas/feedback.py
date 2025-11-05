"""
Pydantic schemas for feedback and onboarding system
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from app.models.feedback import FeedbackPriority, FeedbackStatus, FeedbackType
from pydantic import BaseModel, ConfigDict, Field, validator


class FeedbackCreate(BaseModel):
	"""Schema for creating feedback"""

	type: FeedbackType
	title: str = Field(..., min_length=5, max_length=255)
	description: str = Field(..., min_length=10, max_length=5000)
	priority: FeedbackPriority | None = FeedbackPriority.MEDIUM

	# Context information
	page_url: str | None = Field(None, max_length=500)
	user_agent: str | None = Field(None, max_length=500)
	screen_resolution: str | None = Field(None, max_length=50)
	browser_info: dict[str, Any] | None = None
	metadata: dict[str, Any] | None = None

	@validator("title")
	def validate_title(cls, v):
		if not v.strip():
			raise ValueError("Title cannot be empty")
		return v.strip()

	@validator("description")
	def validate_description(cls, v):
		if not v.strip():
			raise ValueError("Description cannot be empty")
		return v.strip()


class FeedbackUpdate(BaseModel):
	"""Schema for updating feedback"""

	title: str | None = Field(None, min_length=5, max_length=255)
	description: str | None = Field(None, min_length=10, max_length=5000)
	priority: FeedbackPriority | None = None
	status: FeedbackStatus | None = None
	admin_response: str | None = None
	admin_notes: str | None = None


class FeedbackVoteCreate(BaseModel):
	"""Schema for voting on feedback"""

	vote: int = Field(..., ge=-1, le=1)

	@validator("vote")
	def validate_vote(cls, v):
		if v not in [-1, 0, 1]:
			raise ValueError("Vote must be -1, 0, or 1")
		return v


class FeedbackResponse(BaseModel):
	"""Schema for feedback response"""

	id: int
	user_id: int
	type: FeedbackType
	priority: FeedbackPriority
	status: FeedbackStatus
	title: str
	description: str
	page_url: str | None
	created_at: datetime
	updated_at: datetime
	resolved_at: datetime | None
	admin_response: str | None
	vote_count: int = 0
	user_vote: int | None = None

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class OnboardingProgressUpdate(BaseModel):
	"""Schema for updating onboarding progress"""

	steps_completed: list[str] | None = None
	current_step: str | None = None
	tutorials_completed: list[str] | None = None
	features_discovered: list[str] | None = None
	help_topics_viewed: list[str] | None = None
	show_tooltips: bool | None = None
	show_feature_highlights: bool | None = None
	onboarding_completed: bool | None = None


class OnboardingProgressResponse(BaseModel):
	"""Schema for onboarding progress response"""

	id: int
	user_id: int
	steps_completed: list[str]
	current_step: str | None
	tutorials_completed: list[str]
	features_discovered: list[str]
	help_topics_viewed: list[str]
	show_tooltips: bool
	show_feature_highlights: bool
	onboarding_completed: bool
	created_at: datetime
	updated_at: datetime
	completed_at: datetime | None

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class HelpArticleCreate(BaseModel):
	"""Schema for creating help articles"""

	title: str = Field(..., min_length=5, max_length=255)
	slug: str = Field(..., min_length=3, max_length=255)
	content: str = Field(..., min_length=50)
	excerpt: str | None = Field(None, max_length=500)
	category: str = Field(..., min_length=2, max_length=100)
	tags: list[str] | None = []
	meta_description: str | None = Field(None, max_length=500)
	search_keywords: list[str] | None = []
	is_published: bool = True

	@validator("slug")
	def validate_slug(cls, v):
		import re

		if not re.match(r"^[a-z0-9-]+$", v):
			raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
		return v


class HelpArticleUpdate(BaseModel):
	"""Schema for updating help articles"""

	title: str | None = Field(None, min_length=5, max_length=255)
	content: str | None = Field(None, min_length=50)
	excerpt: str | None = Field(None, max_length=500)
	category: str | None = Field(None, min_length=2, max_length=100)
	tags: list[str] | None = None
	meta_description: str | None = Field(None, max_length=500)
	search_keywords: list[str] | None = None
	is_published: bool | None = None


class HelpArticleVoteCreate(BaseModel):
	"""Schema for voting on help articles"""

	is_helpful: bool


class HelpArticleResponse(BaseModel):
	"""Schema for help article response"""

	id: int
	title: str
	slug: str
	content: str
	excerpt: str | None
	category: str
	tags: list[str]
	is_published: bool
	view_count: int
	helpful_votes: int
	unhelpful_votes: int
	created_at: datetime
	updated_at: datetime
	published_at: datetime | None
	user_vote: bool | None = None

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class HelpArticleSummary(BaseModel):
	"""Schema for help article summary (for lists)"""

	id: int
	title: str
	slug: str
	excerpt: str | None
	category: str
	tags: list[str]
	view_count: int
	helpful_votes: int
	unhelpful_votes: int
	created_at: datetime
	updated_at: datetime

	# Pydantic v2 configuration
	model_config = ConfigDict(from_attributes=True)


class TutorialStep(BaseModel):
	"""Schema for tutorial step"""

	id: str
	title: str
	description: str
	target_element: str | None = None
	position: str = "bottom"  # top, bottom, left, right
	content: str
	action_required: bool = False
	action_text: str | None = None


class Tutorial(BaseModel):
	"""Schema for tutorial"""

	id: str
	title: str
	description: str
	category: str
	difficulty: str = "beginner"  # beginner, intermediate, advanced
	estimated_time: int  # in minutes
	prerequisites: list[str] = []
	steps: list[TutorialStep]
	is_required: bool = False


class FeatureHighlight(BaseModel):
	"""Schema for feature highlights"""

	id: str
	title: str
	description: str
	target_element: str
	position: str = "bottom"
	priority: int = 1  # 1 = high, 2 = medium, 3 = low
	show_once: bool = True
	conditions: dict[str, Any] | None = None  # Conditions for showing the highlight


class HelpSearchRequest(BaseModel):
	"""Schema for help search request"""

	query: str = Field(..., min_length=2, max_length=100)
	category: str | None = None
	tags: list[str] | None = None
	limit: int = Field(10, ge=1, le=50)


class HelpSearchResponse(BaseModel):
	"""Schema for help search response"""

	articles: list[HelpArticleSummary]
	total_count: int
	query: str
	suggestions: list[str] = []
