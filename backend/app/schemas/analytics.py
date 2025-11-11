from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


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


class ApplicationStatusCount(BaseModel):
	"""Application count by status"""
	status: str
	count: int


class TrendDataPoint(BaseModel):
	"""Data point for trend analysis"""
	date: date
	count: int


class SkillData(BaseModel):
	"""Skill information with count"""
	skill: str
	count: int
	percentage: float = Field(description="Percentage of jobs requiring this skill")


class CompanyData(BaseModel):
	"""Company information with application count"""
	company: str
	count: int


class RateMetrics(BaseModel):
	"""Success rate metrics"""
	interview_rate: float = Field(description="Percentage of applications that led to interviews")
	offer_rate: float = Field(description="Percentage of interviews that led to offers")
	acceptance_rate: float = Field(description="Percentage of offers that were accepted")


class TrendAnalysis(BaseModel):
	"""Trend analysis with direction and change"""
	direction: str = Field(description="Trend direction: up, down, or neutral")
	percentage_change: float = Field(description="Percentage change from previous period")
	current_value: int
	previous_value: int


class ApplicationTrends(BaseModel):
	"""Application trends over different time periods"""
	daily: TrendAnalysis
	weekly: TrendAnalysis
	monthly: TrendAnalysis


class SkillGapAnalysis(BaseModel):
	"""Skill gap analysis results"""
	user_skills: list[str] = Field(description="Skills the user has")
	market_skills: list[SkillData] = Field(description="Skills in demand in the market")
	missing_skills: list[SkillData] = Field(description="Skills the user is missing")
	skill_coverage_percentage: float = Field(description="Percentage of market skills the user has")
	recommendations: list[str] = Field(description="Skill recommendations for the user")


class ComprehensiveAnalyticsSummary(BaseModel):
	"""Comprehensive analytics summary with all metrics"""
	# Basic counts
	total_jobs: int
	total_applications: int
	
	# Status breakdown
	application_counts_by_status: list[ApplicationStatusCount]
	
	# Rate metrics
	rates: RateMetrics
	
	# Trend data
	trends: ApplicationTrends
	
	# Top skills and companies
	top_skills_in_jobs: list[SkillData]
	top_companies_applied: list[CompanyData]
	
	# Time-based data
	daily_applications_today: int
	weekly_applications: int
	monthly_applications: int
	
	# Goals
	daily_application_goal: int
	daily_goal_progress: float
	
	# Metadata
	generated_at: datetime
	analysis_period_days: int


class TrendAnalysisResponse(BaseModel):
	"""Response for trend analysis endpoint"""
	trends: ApplicationTrends
	time_series_data: list[TrendDataPoint]
	analysis_period_start: date
	analysis_period_end: date
	generated_at: datetime


class SkillGapAnalysisResponse(BaseModel):
	"""Response for skill gap analysis endpoint"""
	analysis: SkillGapAnalysis
	generated_at: datetime
