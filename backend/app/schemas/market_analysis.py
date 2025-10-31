"""
Pydantic schemas for market analysis endpoints
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SalaryRangeSchema(BaseModel):
	"""Schema for salary range data"""

	min: int
	max: int
	median: int
	average: int
	percentile_25: int
	percentile_75: int
	standard_deviation: int


class LocationSalarySchema(BaseModel):
	"""Schema for location-based salary data"""

	count: int
	total_jobs: int
	salary_data_coverage: float
	min: int
	max: int
	median: int
	average: int
	percentile_25: int
	percentile_75: int
	market_competitiveness: str


class IndustrySalarySchema(BaseModel):
	"""Schema for industry-based salary data"""

	count: int
	average: int
	median: int
	min: int
	max: int


class MonthlySalaryTrendSchema(BaseModel):
	"""Schema for monthly salary trend data"""

	month: str
	average_salary: int
	job_count: int
	min_salary: int
	max_salary: int
	median_salary: int


class SalaryTrendsResponse(BaseModel):
	"""Response schema for salary trends analysis"""

	analysis_date: str
	analysis_period_days: int
	total_jobs_analyzed: int
	jobs_with_salary_data: int
	salary_data_coverage: float
	role_filter: str | None
	overall_salary_range: SalaryRangeSchema
	monthly_trends: list[MonthlySalaryTrendSchema]
	salary_growth_rate: float
	growth_percentage: str
	by_location: dict[str, LocationSalarySchema]
	by_industry: dict[str, IndustrySalarySchema]
	by_experience_level: dict[str, IndustrySalarySchema]
	by_company_size: dict[str, IndustrySalarySchema]
	market_insights: list[str]
	chart_data: dict[str, list[dict[str, Any]]]


class GrowthMetricsSchema(BaseModel):
	"""Schema for growth metrics"""

	daily_growth_rate: float
	weekly_growth_rate: float
	monthly_growth_rate: float


class CompanyAnalysisSchema(BaseModel):
	"""Schema for company analysis data"""

	total_companies: int
	active_companies_count: int
	top_companies: list[dict[str, Any]]
	most_active_recently: list[str]


class IndustryDistributionSchema(BaseModel):
	"""Schema for industry distribution data"""

	count: int
	recent_count: int
	percentage: float
	company_count: int
	companies: list[str]
	avg_jobs_per_company: float


class LocationAnalysisSchema(BaseModel):
	"""Schema for location analysis data"""

	count: int
	remote_count: int
	hybrid_count: int
	onsite_count: int
	percentage: float
	remote_percentage: float


class RoleAnalysisSchema(BaseModel):
	"""Schema for role analysis data"""

	role_keywords: Dict[str, int]
	seniority_distribution: Dict[str, int]


class SeasonalPatternsSchema(BaseModel):
	"""Schema for seasonal patterns data"""

	monthly_distribution: dict[str, int]
	weekly_distribution: dict[str, int]
	peak_hiring_month: str | None
	peak_hiring_day: str | None


class MarketVelocitySchema(BaseModel):
	"""Schema for market velocity data"""

	jobs_per_day_recent: float
	jobs_per_day_overall: float
	market_acceleration: bool
	competition_level: str


class JobMarketPatternsResponse(BaseModel):
	"""Response schema for job market patterns analysis"""

	analysis_date: str
	analysis_period_days: int
	total_jobs: int
	daily_average: float
	weekly_average: float
	temporal_distribution: dict[str, dict[str, int]]
	growth_metrics: GrowthMetricsSchema
	job_sources: dict[str, dict[str, Any]]
	company_analysis: CompanyAnalysisSchema
	industry_distribution: dict[str, IndustryDistributionSchema]
	location_analysis: dict[str, LocationAnalysisSchema]
	role_analysis: RoleAnalysisSchema
	seasonal_patterns: SeasonalPatternsSchema
	market_velocity: MarketVelocitySchema
	market_insights: list[str]
	chart_data: dict[str, list[dict[str, Any]]]


class OpportunityAlertSchema(BaseModel):
	"""Schema for opportunity alerts"""

	type: str
	title: str
	message: str
	priority: str
	action: str


class MarketDashboardResponse(BaseModel):
	"""Response schema for market dashboard data"""

	generated_at: str
	salary_trends: SalaryTrendsResponse
	market_patterns: JobMarketPatternsResponse
	opportunity_alerts: list[OpportunityAlertSchema]
	chart_data: dict[str, list[dict[str, Any]]]
	summary: dict[str, Any]


class SkillDemandForecastSchema(BaseModel):
	"""Schema for skill demand forecasting"""

	skill: str
	current_demand: int
	trend_direction: str  # 'increasing', 'decreasing', 'stable'
	growth_rate: float
	projected_demand: int
	market_saturation: str  # 'low', 'medium', 'high'
	learning_priority: str  # 'high', 'medium', 'low'


class CompetitiveAnalysisSchema(BaseModel):
	"""Schema for competitive analysis"""

	total_candidates_estimated: int
	skill_competition_level: str  # 'low', 'medium', 'high'
	location_competition_level: str
	experience_level_competition: str
	recommended_differentiation_strategies: List[str]
	market_positioning_advice: List[str]


class MarketTrendAnalysisResponse(BaseModel):
	"""Response schema for comprehensive market trend analysis"""

	analysis_date: str
	analysis_period_days: int
	user_skills: list[str]
	user_locations: list[str]
	user_experience_level: str

	# Job posting trends
	job_posting_trends: dict[str, list[dict[str, Any]]]
	skill_demand_forecast: list[SkillDemandForecastSchema]
	salary_trend_predictions: dict[str, Any]

	# Competitive analysis
	competitive_analysis: CompetitiveAnalysisSchema

	# Market insights
	market_insights: list[str]
	recommendations: list[str]

	# Predictive analytics
	future_job_market_conditions: dict[str, Any]
	optimal_application_timing: dict[str, Any]


class UserAnalyticsRequest(BaseModel):
	"""Request schema for user analytics"""

	timeframe: str = Field(default="30d", description="Analysis timeframe (30d, 90d, 1y)")
	include_predictions: bool = Field(default=True, description="Include predictive analytics")
	role_filter: str | None = Field(default=None, description="Filter by specific role")


class ConversionFunnelSchema(BaseModel):
	"""Schema for conversion funnel analysis"""

	stage: str
	count: int
	conversion_rate: float
	average_time_in_stage: float  # days
	success_factors: list[str]


class PerformanceBenchmarkSchema(BaseModel):
	"""Schema for performance benchmarking"""

	metric: str
	user_value: float
	market_average: float
	percentile_rank: int
	benchmark_category: str  # 'above_average', 'average', 'below_average'


class PredictiveAnalyticsSchema(BaseModel):
	"""Schema for predictive analytics"""

	success_probability: float
	estimated_time_to_offer: int  # days
	recommended_application_rate: int  # applications per week
	optimal_job_types: list[str]
	risk_factors: list[str]
	success_factors: list[str]


class AdvancedUserAnalyticsResponse(BaseModel):
	"""Response schema for advanced user analytics"""

	analysis_date: str
	user_id: int
	analysis_period_days: int

	# Success rate tracking
	application_success_rate: float
	interview_success_rate: float
	offer_success_rate: float

	# Conversion funnel
	conversion_funnel: list[ConversionFunnelSchema]

	# Performance benchmarking
	performance_benchmarks: list[PerformanceBenchmarkSchema]

	# Predictive analytics
	predictive_analytics: PredictiveAnalyticsSchema

	# Insights and recommendations
	insights: list[str]
	recommendations: list[str]

	# Chart data for visualization
	chart_data: dict[str, list[dict[str, Any]]]
