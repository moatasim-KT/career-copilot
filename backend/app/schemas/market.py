"""
Market Intelligence Schemas.

Pydantic models for market trends and salary insights.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SkillDemand(BaseModel):
	"""Skill demand statistics."""

	skill: str
	demand_count: int
	growth_percentage: float = 0.0


class LocationTrend(BaseModel):
	"""Location-based job trends."""

	location: str
	job_count: int
	avg_salary: float = 0.0


class IndustryTrend(BaseModel):
	"""Industry growth trends."""

	industry: str
	job_count: int
	growth_rate: float = 0.0


class MarketTrend(BaseModel):
	"""Individual market trend metric."""

	metric_name: str
	current_value: float
	previous_value: float
	change_percentage: float
	trend_direction: str  # 'up', 'down', 'stable'


class MarketTrendResponse(BaseModel):
	"""Comprehensive market trends analysis."""

	time_range_days: int
	total_jobs_posted: int
	growth_rate: float
	top_skills: List[SkillDemand]
	top_locations: List[LocationTrend]
	top_companies: List[Dict[str, Any]]
	industry_trends: List[IndustryTrend]
	remote_work_percentage: float
	average_postings_per_day: float
	generated_at: datetime


class SalaryInsight(BaseModel):
	"""Salary statistics for a category."""

	category: str
	median_salary: float
	mean_salary: float
	min_salary: float
	max_salary: float
	sample_size: int


class SalaryInsightResponse(BaseModel):
	"""Comprehensive salary insights."""

	total_data_points: int
	overall_median: float
	overall_mean: float
	overall_min: float
	overall_max: float
	by_role: List[SalaryInsight]
	by_location: List[SalaryInsight]
	by_experience: List[SalaryInsight]
	currency_breakdown: Dict[str, float]
	generated_at: datetime


class TrendMetric(BaseModel):
	"""Generic trend metric."""

	name: str
	value: float
	unit: str
	change_from_previous: Optional[float] = None
