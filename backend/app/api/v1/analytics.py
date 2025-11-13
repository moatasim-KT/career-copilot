@router.get("/api/v1/analytics/summary", response_model=AnalyticsSummaryResponse)
@deprecated_route
async def get_analytics_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get a summary of job application analytics for the current user."""
	from sqlalchemy import and_, select

	from ...models.job import Job

	# Check cache first
	cache_key = f"analytics_summary_{current_user.id}"
	now = datetime.now(timezone.utc)

	if cache_key in _analytics_cache:
		cached_data, cached_time = _analytics_cache[cache_key]
		if now - cached_time < _cache_ttl:
			return cached_data

	# Generate fresh analytics data using async queries
	# Basic counts
	total_jobs_result = await db.execute(select(func.count()).select_from(Job).where(Job.user_id == current_user.id))
	total_jobs = total_jobs_result.scalar() or 0

	total_apps_result = await db.execute(select(func.count()).select_from(Application).where(Application.user_id == current_user.id))
	total_applications = total_apps_result.scalar() or 0

	# Status-based counts
	pending_result = await db.execute(
		select(func.count())
		.select_from(Application)
		.where(and_(Application.user_id == current_user.id, Application.status.in_(["interested", "applied"])))
	)
	pending_applications = pending_result.scalar() or 0

	interviews_result = await db.execute(
		select(func.count()).select_from(Application).where(and_(Application.user_id == current_user.id, Application.status == "interview"))
	)
	interviews_scheduled = interviews_result.scalar() or 0

	offers_result = await db.execute(
		select(func.count())
		.select_from(Application)
		.where(and_(Application.user_id == current_user.id, Application.status.in_(["offer", "accepted"])))
	)
	offers_received = offers_result.scalar() or 0

	rejections_result = await db.execute(
		select(func.count()).select_from(Application).where(and_(Application.user_id == current_user.id, Application.status == "rejected"))
	)
	rejections_received = rejections_result.scalar() or 0

	accepted_result = await db.execute(
		select(func.count()).select_from(Application).where(and_(Application.user_id == current_user.id, Application.status == "accepted"))
	)
	accepted_applications = accepted_result.scalar() or 0
	acceptance_rate = (accepted_applications / offers_received * 100) if offers_received > 0 else 0.0

	# Time-based queries
	today = datetime.now(timezone.utc).date()
	daily_result = await db.execute(
		select(func.count())
		.select_from(Application)
		.where(and_(Application.user_id == current_user.id, func.date(Application.applied_date) == today))
	)
	daily_applications_today = daily_result.scalar() or 0

	one_week_ago = today - timedelta(days=7)
	weekly_result = await db.execute(
		select(func.count())
		.select_from(Application)
		.where(and_(Application.user_id == current_user.id, func.date(Application.applied_date) >= one_week_ago))
	)
	weekly_applications = weekly_result.scalar() or 0

	one_month_ago = today - timedelta(days=30)
	monthly_result = await db.execute(
		select(func.count())
		.select_from(Application)
		.where(and_(Application.user_id == current_user.id, func.date(Application.applied_date) >= one_month_ago))
	)
	monthly_applications = monthly_result.scalar() or 0

	daily_application_goal = current_user.daily_application_goal if current_user.daily_application_goal is not None else 10
	goal_progress = (daily_applications_today / daily_application_goal * 100) if daily_application_goal > 0 else 0.0

	# Get application status breakdown
	status_result = await db.execute(
		select(Application.status, func.count(Application.id)).where(Application.user_id == current_user.id).group_by(Application.status)
	)
	status_breakdown = {status: count for status, count in status_result.all()}

	# Get top skills from jobs (simplified version)
	# This would ideally come from job tech_stack analysis
	top_skills_in_jobs = []

	# Get top companies applied to
	companies_result = await db.execute(
		select(Job.company, func.count(Application.id).label("count"))
		.join(Application, Application.job_id == Job.id)
		.where(Application.user_id == current_user.id)
		.group_by(Job.company)
		.order_by(func.count(Application.id).desc())
		.limit(5)
	)
	top_companies_applied = [{"company": company, "count": count} for company, count in companies_result.all()]

	summary = {
		"total_jobs": total_jobs,
		"total_applications": total_applications,
		"pending_applications": pending_applications,
		"interviews_scheduled": interviews_scheduled,
		"offers_received": offers_received,
		"rejections_received": rejections_received,
		"acceptance_rate": round(acceptance_rate, 2),
		"daily_applications_today": daily_applications_today,
		"weekly_applications": weekly_applications,
		"monthly_applications": monthly_applications,
		"daily_application_goal": daily_application_goal,
		"daily_goal_progress": round(goal_progress, 2),
		"top_skills_in_jobs": top_skills_in_jobs,
		"top_companies_applied": top_companies_applied,
		"application_status_breakdown": status_breakdown,
	}


"""
Analytics API endpoints (canonical v1 module)

This is the canonical `app.api.v1.analytics` module — previously the
functionality lived across several legacy modules. The unified
implementation was consolidated and is placed here with the canonical name
so the rest of the codebase can import `app.api.v1.analytics` directly.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user

from ...core.database import get_db
from ...core.langsmith_integration import LangSmithMetrics, get_langsmith_metrics_summary
from ...core.logging import get_logger
from ...core.monitoring import log_audit_event
from ...models.application import Application
from ...models.job import Job
from ...models.user import User
from ...schemas.analytics import (
	AnalyticsSummaryResponse,
	ComprehensiveAnalyticsSummary,
	InterviewTrendsResponse,
	SkillGapAnalysisResponse,
	TrendAnalysisResponse,
)
from ...services.analytics_service import AnalyticsService
from ...services.analytics_specialized import analytics_specialized_service

logger = get_logger(__name__)

# Global cache for analytics data
_analytics_cache = {}
_cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes

router = APIRouter(tags=["analytics"])


# ===== BASIC ANALYTICS ENDPOINTS =====


@router.get("/api/v1/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get a summary of job application analytics for the current user."""
	# Check cache first
	cache_key = f"analytics_summary_{current_user.id}"
	now = datetime.now(timezone.utc)

	if cache_key in _analytics_cache:
		cached_data, cached_time = _analytics_cache[cache_key]
		if now - cached_time < _cache_ttl:
			return cached_data

	# Generate fresh analytics data using async queries
	try:
		# Basic counts
		total_applications = await db.scalar(select(func.count()).select_from(Application).where(Application.user_id == current_user.id))

		total_jobs = await db.scalar(select(func.count()).select_from(Job).where(Job.user_id == current_user.id))

		# Status breakdown
		status_counts = await db.execute(
			select(Application.status, func.count(Application.id)).where(Application.user_id == current_user.id).group_by(Application.status)
		)
		status_breakdown = {status: count for status, count in status_counts}

		# Recent activity (last 30 days)
		thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
		recent_applications = await db.scalar(
			select(func.count())
			.select_from(Application)
			.where(and_(Application.user_id == current_user.id, Application.created_at >= thirty_days_ago))
		)

		# Success rate calculation
		successful_applications = status_breakdown.get("accepted", 0) + status_breakdown.get("interviewed", 0)
		success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0

		result = AnalyticsSummaryResponse(
			total_applications=total_applications,
			total_jobs=total_jobs,
			status_breakdown=status_breakdown,
			recent_activity=recent_applications,
			success_rate=round(success_rate, 2),
			last_updated=now,
		)

		# Cache the result
		_analytics_cache[cache_key] = (result, now)

		return result

	except Exception as e:
		logger.error(f"Failed to get analytics summary: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve analytics summary")


@router.get("/analytics/timeline")
@deprecated_route
async def get_timeline(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	from sqlalchemy import select

	result = await db.execute(select(Application).where(Application.user_id == current_user.id).order_by(Application.applied_date.desc()).limit(50))
	applications = result.scalars().all()

	return [{"date": app.applied_date, "status": app.status, "job_id": app.job_id} for app in applications]


@router.get("/analytics/status")
@deprecated_route
async def get_status_breakdown(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	from sqlalchemy import select

	result = await db.execute(
		select(Application.status, func.count(Application.id)).where(Application.user_id == current_user.id).group_by(Application.status)
	)
	status_counts = result.all()

	return {"breakdown": [{"status": status, "count": count} for status, count in status_counts]}


@router.get("/api/v1/analytics/interview-trends", response_model=InterviewTrendsResponse)
@deprecated_route
async def get_interview_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get analysis of interview trends for the current user."""
	from sqlalchemy import and_, select

	# Get all interviews
	result = await db.execute(select(Application).where(and_(Application.user_id == current_user.id, Application.status == "interview")))
	interviews = result.scalars().all()

	total_interviews = len(interviews)
	if total_interviews == 0:
		return {
			"total_interviews": 0,
			"avg_preparation_time": 0,
			"success_rate": 0.0,
			"common_topics": [],
			"difficulty_distribution": {},
		}

	# Calculate success rate (offers from interviews)
	offers_result = await db.execute(
		select(func.count())
		.select_from(Application)
		.where(and_(Application.user_id == current_user.id, Application.status.in_(["offer", "accepted"])))
	)
	successful_interviews = offers_result.scalar() or 0
	success_rate = (successful_interviews / total_interviews * 100) if total_interviews > 0 else 0.0

	# Difficulty distribution
	difficulty_distribution = {}
	for i in interviews:
		difficulty = i.interview_difficulty or "medium"
		difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1

	# Calculate average preparation time (example logic)
	# This is a simplified calculation. A real implementation would need more data.
	total_prep_time = timedelta(0)
	prep_time_count = 0
	for i in interviews:
		if i.status_history and "interested" in i.status_history and "interview" in i.status_history:
			interested_date = i.status_history["interested"]
			interview_date = i.status_history["interview"]
			if interested_date and interview_date:
				total_prep_time += interview_date - interested_date
				prep_time_count += 1
	avg_preparation_time = (total_prep_time.days / prep_time_count) if prep_time_count > 0 else 0

	# Extract common topics from job descriptions (simplified)
	from collections import Counter

	from ...models.job import Job

	job_ids = [i.job_id for i in interviews if i.job_id]
	if job_ids:
		jobs_result = await db.execute(select(Job.description).where(Job.id.in_(job_ids)))
		descriptions = [desc for (desc,) in jobs_result.all() if desc]
		words = " ".join(descriptions).lower().split()
		common_words = [word for word, count in Counter(words).most_common(10) if len(word) > 4 and word.isalpha()]
	else:
		common_words = []

	return {
		"total_interviews": total_interviews,
		"avg_preparation_time": avg_preparation_time,
		"success_rate": round(success_rate, 2),
		"common_topics": common_words,
		"difficulty_distribution": difficulty_distribution,
	}


@router.get("/api/v1/analytics/comprehensive-dashboard")
@deprecated_route
async def get_comprehensive_dashboard(days: int = 90, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get comprehensive analytics data for dashboard visualization."""
	from sqlalchemy import and_, select

	# Get time-based trends
	end_date = datetime.now(timezone.utc).date()
	start_date = end_date - timedelta(days=days)

	# Application trends over time using async
	result = await db.execute(
		select(func.date(Application.applied_date).label("date"), func.count(Application.id).label("count"))
		.where(and_(Application.user_id == current_user.id, Application.applied_date >= start_date, Application.applied_date <= end_date))
		.group_by(func.date(Application.applied_date))
	)
	applications_by_date = result.all()

	# Weekly performance
	weekly_performance = []
	for i in range(4):
		week_end = end_date - timedelta(days=i * 7)
		week_start = week_end - timedelta(days=7)
		result = await db.execute(
			select(func.count(Application.id)).where(
				and_(
					Application.user_id == current_user.id,
					Application.applied_date >= week_start,
					Application.applied_date < week_end,
				)
			)
		)
		weekly_apps = result.scalar() or 0
		weekly_performance.append({"week": f"Week {-i}", "applications": weekly_apps})

	return {
		"application_trends": [
			{"date": date.isoformat() if hasattr(date, "isoformat") else str(date), "applications": count} for date, count in applications_by_date
		],
		"weekly_performance": weekly_performance,
		"generated_at": datetime.now(timezone.utc).isoformat(),
	}


# ============================================================================
# Enhanced Analytics Endpoints (Task 10)
# ============================================================================


@router.get("/api/v1/analytics/comprehensive-summary", response_model=ComprehensiveAnalyticsSummary)
@deprecated_route
async def get_comprehensive_analytics_summary(
	days: int = Query(90, ge=1, le=365, description="Number of days for analysis period"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get comprehensive analytics summary with all metrics.

	This endpoint provides:
	- Application counts by status
	- Interview, offer, and acceptance rates
	- Daily, weekly, and monthly application trends
	- Top skills in jobs
	- Top companies applied to
	- Goal progress tracking

	Requirements: 6.1, 6.2, 6.3
	"""
	# Check cache first
	cache_key = f"comprehensive_summary_{current_user.id}_{days}"
	now = datetime.now(timezone.utc)

	if cache_key in _analytics_cache:
		cached_data, cached_time = _analytics_cache[cache_key]
		if now - cached_time < _cache_ttl:
			return cached_data

	# Generate fresh analytics
	service = AnalyticsService(db)
	summary = await service.get_comprehensive_summary(user_id=current_user.id, analysis_period_days=days)

	# Cache the result
	_analytics_cache[cache_key] = (summary, now)

	return summary


@router.get("/api/v1/analytics/trends", response_model=TrendAnalysisResponse)
@deprecated_route
async def get_trend_analysis(
	start_date: Optional[date] = Query(None, description="Start date for analysis (defaults to 30 days ago)"),
	end_date: Optional[date] = Query(None, description="End date for analysis (defaults to today)"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""
	Get detailed trend analysis with direction and percentage changes.

	This endpoint provides:
	- Trend direction (up, down, neutral) for daily, weekly, and monthly periods
	- Percentage changes from previous periods
	- Time series data for visualization

	Supports custom time ranges for flexible analysis.

	Requirements: 6.2
	"""
	# Set default dates if not provided
	if end_date is None:
		end_date = datetime.now(timezone.utc).date()
	if start_date is None:
		start_date = end_date - timedelta(days=30)

	# Check cache
	cache_key = f"trends_{current_user.id}_{start_date}_{end_date}"
	now = datetime.now(timezone.utc)

	if cache_key in _analytics_cache:
		cached_data, cached_time = _analytics_cache[cache_key]
		if now - cached_time < _cache_ttl:
			return cached_data

	# Generate trend analysis
	service = AnalyticsService(db)

	# Get application trends
	trends = await service.calculate_application_trends(user_id=current_user.id)

	# Get time series data
	time_series_data = await service.get_time_series_data(user_id=current_user.id, start_date=start_date, end_date=end_date)

	response = TrendAnalysisResponse(
		trends=trends, time_series_data=time_series_data, analysis_period_start=start_date, analysis_period_end=end_date, generated_at=now
	)

	# Cache the result
	_analytics_cache[cache_key] = (response, now)

	return response


@router.get("/api/v1/analytics/skill-gap-analysis", response_model=SkillGapAnalysisResponse)
@deprecated_route
async def get_skill_gap_analysis(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get skill gap analysis comparing user skills with market demand.

	This endpoint provides:
	- User's current skills
	- Top skills in demand in the market (from jobs)
	- Missing skills the user should consider learning
	- Skill coverage percentage
	- Personalized skill recommendations

	Requirements: 6.3
	"""
	# Check cache
	cache_key = f"skill_gap_{current_user.id}"
	now = datetime.now(timezone.utc)

	if cache_key in _analytics_cache:
		cached_data, cached_time = _analytics_cache[cache_key]
		if now - cached_time < _cache_ttl:
			return cached_data

	# Generate skill gap analysis
	service = AnalyticsService(db)
	analysis = await service.analyze_skill_gaps(user_id=current_user.id)

	response = SkillGapAnalysisResponse(analysis=analysis, generated_at=now)

	# Cache the result
	_analytics_cache[cache_key] = (response, now)

	return response


@router.delete("/api/v1/analytics/cache")
@deprecated_route
async def clear_analytics_cache(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Clear analytics cache for the current user.

	This endpoint allows users to force refresh their analytics data
	by clearing the cache. Useful after bulk data imports or updates.

	Requirements: 10.4
	"""
	service = AnalyticsService(db)
	count = service.invalidate_user_cache(user_id=current_user.id)

	# Also clear in-memory cache
	keys_to_delete = [k for k in _analytics_cache.keys() if str(current_user.id) in k]
	for key in keys_to_delete:
		_analytics_cache.pop(key, None)

	return {"message": "Analytics cache cleared successfully", "entries_cleared": count + len(keys_to_delete)}


@router.get("/api/v1/analytics/cache/stats")
@deprecated_route
async def get_cache_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get analytics cache statistics.

	Provides information about cache performance and usage.

	Requirements: 10.4
	"""
	from ..services.analytics_cache_service import get_analytics_cache

	cache = get_analytics_cache()
	stats = cache.get_stats()

	return {"cache_stats": stats, "in_memory_cache_size": len(_analytics_cache)}


# Extended Analytics Endpoints (from analytics_extended.py)


@router.get("/api/v1/analytics/dashboard")
@deprecated_route
async def get_analytics_dashboard(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, 1y, all"),
):
	"""
	Get comprehensive analytics dashboard data.

	Includes:
	- Application statistics
	- Success rates
	- Timeline metrics
	- Top companies
	- Technology trends

	Args:
		current_user: Current authenticated user
		db: Database session
		time_range: Time range for analytics

	Returns:
		dict: Dashboard analytics data
	"""
	from sqlalchemy import and_, select

	from ...models.application import Application
	from ...models.job import Job

	# Calculate date filter
	now = datetime.utcnow()
	if time_range == "7d":
		start_date = now - timedelta(days=7)
	elif time_range == "30d":
		start_date = now - timedelta(days=30)
	elif time_range == "90d":
		start_date = now - timedelta(days=90)
	elif time_range == "1y":
		start_date = now - timedelta(days=365)
	else:  # "all"
		start_date = None

	# Get jobs and applications
	jobs_query = select(Job).where(Job.user_id == current_user.id)
	apps_query = select(Application).where(Application.user_id == current_user.id)

	if start_date:
		jobs_query = jobs_query.where(Job.created_at >= start_date)
		apps_query = apps_query.where(Application.created_at >= start_date)

	jobs_result = await db.execute(jobs_query)
	jobs = jobs_result.scalars().all()

	apps_result = await db.execute(apps_query)
	applications = apps_result.scalars().all()

	# Basic statistics
	total_jobs = len(jobs)
	total_applications = len(applications)

	# Application status counts
	status_counts = {}
	for app in applications:
		status = app.status or "unknown"
		status_counts[status] = status_counts.get(status, 0) + 1

	# Company statistics
	company_counts = {}
	for job in jobs:
		company = job.company or "Unknown"
		company_counts[company] = company_counts.get(company, 0) + 1

	top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]

	# Technology trends
	tech_counts = {}
	for job in jobs:
		for tech in job.tech_stack or []:
			tech_counts[tech] = tech_counts.get(tech, 0) + 1

	top_technologies = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:15]

	# Success rate
	successful_apps = status_counts.get("offer", 0) + status_counts.get("accepted", 0)
	success_rate = (successful_apps / total_applications * 100) if total_applications > 0 else 0

	# Response rate
	response_count = sum(count for status, count in status_counts.items() if status not in ["sent", "pending"])
	response_rate = (response_count / total_applications * 100) if total_applications > 0 else 0

	# Timeline data (applications per week)
	timeline_data = []
	if start_date:
		weeks = []
		current = start_date
		while current <= now:
			week_end = current + timedelta(days=7)
			week_apps = [app for app in applications if current <= app.created_at < week_end]
			weeks.append(
				{
					"week": current.strftime("%Y-%m-%d"),
					"applications": len(week_apps),
					"successes": len([app for app in week_apps if app.status in ["offer", "accepted"]]),
				}
			)
			current = week_end
		timeline_data = weeks

	return {
		"summary": {
			"total_jobs": total_jobs,
			"total_applications": total_applications,
			"success_rate": round(success_rate, 1),
			"response_rate": round(response_rate, 1),
			"time_range": time_range,
		},
		"status_breakdown": status_counts,
		"top_companies": top_companies,
		"top_technologies": top_technologies,
		"timeline": timeline_data,
		"generated_at": now.isoformat(),
	}


@router.get("/api/v1/analytics/performance-metrics")
@deprecated_route
async def get_performance_metrics(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	time_period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
):
	"""
	Get performance metrics for job applications.

	Provides detailed performance analysis including:
	- Application velocity
	- Success rates by company size
	- Response time analysis
	- Conversion funnel metrics

	Args:
		current_user: Current authenticated user
		db: Database session
		time_period: Time period for analysis

	Returns:
		dict: Performance metrics data
	"""
	from sqlalchemy import and_, select

	from ...models.application import Application
	from ...models.job import Job

	# Calculate date filter
	now = datetime.utcnow()
	if time_period == "7d":
		start_date = now - timedelta(days=7)
	elif time_period == "30d":
		start_date = now - timedelta(days=30)
	elif time_period == "90d":
		start_date = now - timedelta(days=90)
	elif time_period == "1y":
		start_date = now - timedelta(days=365)
	else:
		start_date = now - timedelta(days=30)

	# Get applications with job details
	apps_query = select(Application).where(and_(Application.user_id == current_user.id, Application.created_at >= start_date))

	apps_result = await db.execute(apps_query)
	applications = apps_result.scalars().all()

	# Calculate metrics
	total_applications = len(applications)
	response_count = sum(1 for app in applications if app.status not in ["sent", "pending"])
	success_count = sum(1 for app in applications if app.status in ["offer", "accepted"])

	response_rate = (response_count / total_applications * 100) if total_applications > 0 else 0
	success_rate = (success_count / total_applications * 100) if total_applications > 0 else 0

	# Application velocity (applications per week)
	weeks_active = max(1, (now - start_date).days / 7)
	velocity = total_applications / weeks_active

	# Response time analysis (simplified)
	avg_response_days = 7  # Placeholder - would need actual response timestamps

	# Company size analysis (simplified categorization)
	company_size_performance = {
		"startup": {"applications": 0, "successes": 0},
		"mid_size": {"applications": 0, "successes": 0},
		"enterprise": {"applications": 0, "successes": 0},
	}

	# This would require company size data in the job model
	# For now, return placeholder data

	return {
		"overview": {
			"total_applications": total_applications,
			"response_rate": round(response_rate, 1),
			"success_rate": round(success_rate, 1),
			"application_velocity": round(velocity, 1),
			"time_period": time_period,
		},
		"response_time": {"average_days": avg_response_days, "median_days": avg_response_days},
		"company_size_performance": company_size_performance,
		"conversion_funnel": {"applied": total_applications, "responded": response_count, "successful": success_count},
		"generated_at": now.isoformat(),
	}


@router.get("/api/v1/analytics/risk-trends")
@deprecated_route
async def get_risk_trends(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	time_period: str = Query("90d", description="Time period for risk analysis"),
):
	"""
	Analyze risk trends in job applications.

	Identifies patterns that may indicate:
	- Application fatigue
	- Market saturation
	- Timing issues
	- Strategy effectiveness

	Args:
		current_user: Current authenticated user
		db: Database session
		time_period: Time period for analysis

	Returns:
		dict: Risk analysis data
	"""
	from sqlalchemy import and_, select

	from ...models.application import Application

	# Calculate date filter
	now = datetime.utcnow()
	if time_period == "30d":
		start_date = now - timedelta(days=30)
	elif time_period == "90d":
		start_date = now - timedelta(days=90)
	elif time_period == "1y":
		start_date = now - timedelta(days=365)
	else:
		start_date = now - timedelta(days=90)

	# Get applications
	apps_query = select(Application).where(and_(Application.user_id == current_user.id, Application.created_at >= start_date))

	apps_result = await db.execute(apps_query)
	applications = apps_result.scalars().all()

	# Analyze risk patterns
	total_applications = len(applications)

	# Weekly application distribution
	weekly_counts = []
	current = start_date
	while current <= now:
		week_end = current + timedelta(days=7)
		week_apps = [app for app in applications if current <= app.created_at < week_end]
		weekly_counts.append(len(week_apps))
		current = week_end

	# Calculate risk metrics
	avg_weekly = sum(weekly_counts) / len(weekly_counts) if weekly_counts else 0
	max_weekly = max(weekly_counts) if weekly_counts else 0
	min_weekly = min(weekly_counts) if weekly_counts else 0

	volatility = (max_weekly - min_weekly) / avg_weekly if avg_weekly > 0 else 0

	# Risk assessment
	risks = []
	if volatility > 1.5:
		risks.append("High application volume volatility - consider more consistent pacing")
	if max_weekly > 20:
		risks.append("Peak application weeks exceed 20 - monitor for quality degradation")
	if len([w for w in weekly_counts if w == 0]) > len(weekly_counts) * 0.3:
		risks.append("Extended periods with no applications - risk of losing momentum")

	# Success rate trends
	recent_success_rate = 0  # Would need more complex analysis

	return {
		"risk_assessment": {
			"overall_risk_level": "low" if len(risks) == 0 else "medium" if len(risks) <= 2 else "high",
			"identified_risks": risks,
			"volatility_score": round(volatility, 2),
		},
		"application_patterns": {
			"average_weekly": round(avg_weekly, 1),
			"peak_weekly": max_weekly,
			"low_weekly": min_weekly,
			"total_weeks": len(weekly_counts),
		},
		"recommendations": [
			"Maintain consistent application volume",
			"Track response rates by application source",
			"Consider seasonal timing in job market",
		]
		if not risks
		else risks,
		"time_period": time_period,
		"generated_at": now.isoformat(),
	}


@router.get("/api/v1/analytics/success-metrics")
@deprecated_route
async def get_success_metrics(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	metric_type: str = Query("overall", description="Type of success metric: overall, company_size, industry, timing"),
):
	"""
	Get detailed success metrics for job applications.

	Provides insights into what factors contribute to application success.

	Args:
		current_user: Current authenticated user
		db: Database session
		metric_type: Type of success analysis

	Returns:
		dict: Success metrics data
	"""
	from sqlalchemy import and_, select

	from ...models.application import Application
	from ...models.job import Job

	# Get successful applications
	success_query = select(Application).where(and_(Application.user_id == current_user.id, Application.status.in_(["offer", "accepted"])))

	success_result = await db.execute(success_query)
	successful_apps = success_result.scalars().all()

	# Get all applications for comparison
	all_query = select(Application).where(Application.user_id == current_user.id)
	all_result = await db.execute(all_query)
	all_apps = all_result.scalars().all()

	total_successful = len(successful_apps)
	total_applications = len(all_apps)
	overall_success_rate = (total_successful / total_applications * 100) if total_applications > 0 else 0

	# Analyze by different dimensions
	metrics = {
		"overall": {
			"success_rate": round(overall_success_rate, 1),
			"successful_applications": total_successful,
			"total_applications": total_applications,
		}
	}

	if metric_type == "company_size":
		# This would require company size data
		metrics["company_size"] = {
			"startup": {"success_rate": 0, "sample_size": 0},
			"mid_size": {"success_rate": 0, "sample_size": 0},
			"enterprise": {"success_rate": 0, "sample_size": 0},
		}
	elif metric_type == "industry":
		# Would need industry classification
		metrics["industry"] = {}
	elif metric_type == "timing":
		# Analyze by day of week, month, etc.
		dow_success = {}
		for app in successful_apps:
			dow = app.created_at.strftime("%A")
			dow_success[dow] = dow_success.get(dow, 0) + 1

		metrics["timing"] = {"best_day": max(dow_success.items(), key=lambda x: x[1])[0] if dow_success else "N/A", "day_performance": dow_success}

	return {
		"metric_type": metric_type,
		"metrics": metrics,
		"insights": [
			f"Overall success rate: {round(overall_success_rate, 1)}%",
			"Track which application sources yield best results",
			"Consider timing and volume patterns",
		],
		"generated_at": datetime.utcnow().isoformat(),
	}


@router.get("/api/v1/analytics/application-velocity")
@deprecated_route
async def get_application_velocity(
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
	period: str = Query("weekly", description="Analysis period: daily, weekly, monthly"),
):
	"""
	Analyze application velocity and pacing.

	Helps users understand their application patterns and optimize their job search strategy.

	Args:
		current_user: Current authenticated user
		db: Database session
		period: Analysis period

	Returns:
		dict: Application velocity data
	"""
	from sqlalchemy import and_, select

	from ...models.application import Application

	# Get applications from last 90 days
	start_date = datetime.utcnow() - timedelta(days=90)
	apps_query = select(Application).where(and_(Application.user_id == current_user.id, Application.created_at >= start_date))

	apps_result = await db.execute(apps_query)
	applications = apps_result.scalars().all()

	# Calculate velocity based on period
	velocity_data = []
	now = datetime.utcnow()

	if period == "daily":
		# Daily breakdown
		for i in range(90):
			day = now - timedelta(days=i)
			day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
			day_end = day_start + timedelta(days=1)
			day_apps = [app for app in applications if day_start <= app.created_at < day_end]
			velocity_data.append({"date": day.strftime("%Y-%m-%d"), "applications": len(day_apps)})
	elif period == "weekly":
		# Weekly breakdown
		for i in range(12):
			week_start = now - timedelta(days=i * 7)
			week_end = week_start + timedelta(days=7)
			week_apps = [app for app in applications if week_start <= app.created_at < week_end]
			velocity_data.append({"week": f"Week {12 - i}", "applications": len(week_apps), "start_date": week_start.strftime("%Y-%m-%d")})
	else:  # monthly
		# Monthly breakdown
		for i in range(3):
			month_start = (now - timedelta(days=i * 30)).replace(day=1)
			next_month = (
				month_start.replace(month=month_start.month % 12 + 1, day=1)
				if month_start.month < 12
				else month_start.replace(year=month_start.year + 1, month=1, day=1)
			)
			month_apps = [app for app in applications if month_start <= app.created_at < next_month]
			velocity_data.append({"month": month_start.strftime("%B %Y"), "applications": len(month_apps)})

	# Calculate trends
	if len(velocity_data) >= 2:
		recent = sum(item["applications"] for item in velocity_data[:3]) / 3
		older = sum(item["applications"] for item in velocity_data[3:6]) / 3 if len(velocity_data) >= 6 else recent
		trend = "increasing" if recent > older * 1.1 else "decreasing" if recent < older * 0.9 else "stable"
	else:
		trend = "insufficient_data"

	# Recommendations
	recommendations = []
	weekly_avg = sum(item["applications"] for item in velocity_data) / len(velocity_data) if velocity_data else 0

	if trend == "decreasing":
		recommendations.append("Application velocity is decreasing - consider increasing activity")
	elif trend == "increasing":
		recommendations.append("Great momentum! Keep up the consistent application pace")

	if weekly_avg > 15:
		recommendations.append("High application volume - ensure quality isn't sacrificed for quantity")

	return {
		"period": period,
		"velocity_data": velocity_data,
		"trend": trend,
		"average_applications": round(weekly_avg, 1),
		"recommendations": recommendations if recommendations else ["Maintain current application pace"],
		"generated_at": datetime.utcnow().isoformat(),
	}
