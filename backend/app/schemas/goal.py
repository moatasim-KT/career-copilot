"""
Goal schemas for Career Co-Pilot system
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class MilestoneData(BaseModel):
	"""Schema for milestone data within goals"""

	value: int = Field(..., ge=0)
	message: str = Field(..., min_length=1, max_length=200)
	achieved: bool = False
	achieved_at: datetime | None = None


class GoalCreate(BaseModel):
	"""Schema for creating a new goal"""

	goal_type: str = Field(
		...,
		pattern="^(daily_applications|weekly_applications|monthly_applications|skill_development|interview_preparation|networking|portfolio_building|certification|salary_negotiation|career_transition)$",
	)
	title: str = Field(..., min_length=1, max_length=200)
	description: str | None = Field(None, max_length=500)
	target_value: int = Field(..., ge=1)
	unit: str = Field(..., min_length=1, max_length=50)
	start_date: date
	end_date: date
	category: str = Field(default="job_search", max_length=50)
	priority: str = Field(default="medium", pattern="^(low|medium|high)$")
	reminder_frequency: str = Field(default="daily", pattern="^(daily|weekly|never)$")
	milestones: list[MilestoneData] = Field(default_factory=list)


class GoalUpdate(BaseModel):
	"""Schema for updating an existing goal"""

	title: str | None = Field(None, min_length=1, max_length=200)
	description: str | None = Field(None, max_length=500)
	target_value: int | None = Field(None, ge=1)
	end_date: date | None = None
	is_active: bool | None = None
	priority: str | None = Field(None, pattern="^(low|medium|high)$")
	reminder_frequency: str | None = Field(None, pattern="^(daily|weekly|never)$")


class GoalProgressCreate(BaseModel):
	"""Schema for creating goal progress entry"""

	value_added: int = Field(..., ge=0)
	notes: str | None = Field(None, max_length=500)
	source: str = Field(default="manual", pattern="^(manual|automatic|system)$")
	activities: list[dict[str, Any]] = Field(default_factory=list)
	mood: str | None = Field(None, pattern="^(frustrated|neutral|motivated|excited)$")
	challenges: list[str] = Field(default_factory=list)


class GoalProgressResponse(BaseModel):
	"""Schema for goal progress response"""

	id: int
	goal_id: int
	progress_date: date
	value_added: int
	total_value: int
	notes: str | None = None
	source: str
	details: dict[str, Any] = Field(default_factory=dict)
	created_at: datetime


class GoalResponse(BaseModel):
	"""Schema for goal response"""

	id: int
	goal_type: str
	title: str
	description: str | None = None
	target_value: int
	current_value: int
	unit: str
	start_date: date
	end_date: date
	is_active: bool
	is_completed: bool
	completed_at: datetime | None = None
	metadata: dict[str, Any] = Field(default_factory=dict)
	created_at: datetime
	updated_at: datetime

	# Calculated fields
	progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
	days_remaining: int | None = None
	is_overdue: bool = False
	recent_progress: list[GoalProgressResponse] = Field(default_factory=list)


class MilestoneCreate(BaseModel):
	"""Schema for creating a milestone"""

	milestone_type: str = Field(
		...,
		pattern="^(goal_achievement|application_streak|response_milestone|interview_milestone|offer_milestone|skill_milestone|consistency_milestone|improvement_milestone)$",
	)
	title: str = Field(..., min_length=1, max_length=200)
	description: str | None = Field(None, max_length=500)
	achievement_value: int | None = Field(None, ge=0)
	category: str = Field(default="application_progress", max_length=50)
	badge: str | None = Field(None, max_length=50)
	celebration_message: str = Field(..., min_length=1, max_length=300)
	reward_type: str = Field(default="badge", pattern="^(badge|streak|achievement)$")
	related_goal_id: int | None = None
	difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class MilestoneResponse(BaseModel):
	"""Schema for milestone response"""

	id: int
	milestone_type: str
	title: str
	description: str | None = None
	achievement_value: int | None = None
	achievement_date: datetime
	metadata: dict[str, Any] = Field(default_factory=dict)
	is_celebrated: bool
	celebrated_at: datetime | None = None
	created_at: datetime


class GoalSummaryStats(BaseModel):
	"""Schema for goal summary statistics"""

	total_goals: int = 0
	active_goals: int = 0
	completed_goals: int = 0
	overdue_goals: int = 0
	goals_completion_rate: float = 0.0
	current_streak: int = 0
	longest_streak: int = 0
	total_milestones: int = 0
	recent_milestones: int = 0


class MotivationalMessage(BaseModel):
	"""Schema for motivational messages"""

	message_type: str = Field(..., pattern="^(encouragement|celebration|reminder|tip|challenge)$")
	title: str = Field(..., min_length=1, max_length=100)
	message: str = Field(..., min_length=1, max_length=300)
	context: dict[str, Any] = Field(default_factory=dict)
	priority: str = Field(default="medium", pattern="^(low|medium|high)$")
	expires_at: datetime | None = None


class GoalDashboardResponse(BaseModel):
	"""Schema for goal dashboard response"""

	summary_stats: GoalSummaryStats
	active_goals: list[GoalResponse]
	recent_milestones: list[MilestoneResponse]
	motivational_messages: list[MotivationalMessage]
	weekly_progress_chart: list[dict[str, Any]] = Field(default_factory=list)
	goal_completion_trend: list[dict[str, Any]] = Field(default_factory=list)


class ProgressCelebration(BaseModel):
	"""Schema for progress celebration"""

	celebration_type: str = Field(..., pattern="^(goal_completed|milestone_reached|streak_achieved|improvement_made)$")
	title: str = Field(..., min_length=1, max_length=100)
	message: str = Field(..., min_length=1, max_length=300)
	achievement_data: dict[str, Any] = Field(default_factory=dict)
	badge_earned: str | None = None
	points_earned: int = Field(default=0, ge=0)
	share_message: str | None = None


class WeeklyGoalSummary(BaseModel):
	"""Schema for weekly goal summary"""

	week_start: date
	week_end: date
	goals_worked_on: int
	goals_completed: int
	total_progress_made: int
	milestones_achieved: int
	consistency_score: float = Field(ge=0.0, le=100.0)
	top_achievement: str | None = None
	areas_for_improvement: list[str] = Field(default_factory=list)
	next_week_focus: list[str] = Field(default_factory=list)
