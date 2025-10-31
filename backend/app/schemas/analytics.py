from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
	total_jobs: int
	total_applications: int
	pending_applications: int
	interviews_scheduled: int
	offers_received: int
	rejections_received: int
	acceptance_rate: float
	daily_applications_today: int
	weekly_applications: int
	monthly_applications: int
	daily_application_goal: int
	daily_goal_progress: float
	top_skills_in_jobs: list[dict[str, Any]]
	top_companies_applied: list[dict[str, Any]]
	application_status_breakdown: dict[str, int]


class InterviewTrendsResponse(BaseModel):
	total_interviews_analyzed: int
	top_common_questions: list[list[Any]]
	top_skill_areas_discussed: list[list[Any]]
	common_tech_stack_in_interviews: list[list[Any]]
