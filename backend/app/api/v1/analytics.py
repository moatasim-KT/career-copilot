"""Analytics endpoints"""

from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.application import Application
from ...models.user import User
from ...schemas.analytics import (
    AnalyticsSummaryResponse,
    InterviewTrendsResponse,
    ComprehensiveAnalyticsSummary,
    TrendAnalysisResponse,
    SkillGapAnalysisResponse,
)
from ...services.analytics_service import AnalyticsService
from ...services.comprehensive_analytics_service import ComprehensiveAnalyticsService

_analytics_cache = {}
_cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter(tags=["analytics"])


@router.get("/api/v1/analytics/summary", response_model=AnalyticsSummaryResponse)
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

	# Cache the result
	_analytics_cache[cache_key] = (summary, now)

	return summary


@router.get("/analytics/timeline")
async def get_timeline(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	from sqlalchemy import select

	result = await db.execute(select(Application).where(Application.user_id == current_user.id).order_by(Application.applied_date.desc()).limit(50))
	applications = result.scalars().all()

	return [{"date": app.applied_date, "status": app.status, "job_id": app.job_id} for app in applications]


@router.get("/analytics/status")
async def get_status_breakdown(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	from sqlalchemy import select

	result = await db.execute(
		select(Application.status, func.count(Application.id)).where(Application.user_id == current_user.id).group_by(Application.status)
	)
	status_counts = result.all()

	return {"breakdown": [{"status": status, "count": count} for status, count in status_counts]}


@router.get("/api/v1/analytics/interview-trends", response_model=InterviewTrendsResponse)
async def get_interview_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get analysis of interview trends for the current user."""
    from sqlalchemy import and_, select

    # Get all interviews
    result = await db.execute(
        select(Application).where(and_(Application.user_id == current_user.id, Application.status == "interview"))
    )
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
            {"date": date.isoformat() if hasattr(date, "isoformat") else str(date), "applications": count}
            for date, count in applications_by_date
        ],
        "weekly_performance": weekly_performance,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Enhanced Analytics Endpoints (Task 10)
# ============================================================================


@router.get("/api/v1/analytics/comprehensive-summary", response_model=ComprehensiveAnalyticsSummary)
async def get_comprehensive_analytics_summary(
    days: int = Query(90, ge=1, le=365, description="Number of days for analysis period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    service = ComprehensiveAnalyticsService(db)
    summary = await service.get_comprehensive_summary(
        user_id=current_user.id,
        analysis_period_days=days
    )
    
    # Cache the result
    _analytics_cache[cache_key] = (summary, now)
    
    return summary


@router.get("/api/v1/analytics/trends", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis (defaults to 30 days ago)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (defaults to today)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    service = ComprehensiveAnalyticsService(db)
    
    # Get application trends
    trends = await service.calculate_application_trends(user_id=current_user.id)
    
    # Get time series data
    time_series_data = await service.get_time_series_data(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    response = TrendAnalysisResponse(
        trends=trends,
        time_series_data=time_series_data,
        analysis_period_start=start_date,
        analysis_period_end=end_date,
        generated_at=now
    )
    
    # Cache the result
    _analytics_cache[cache_key] = (response, now)
    
    return response


@router.get("/api/v1/analytics/skill-gap-analysis", response_model=SkillGapAnalysisResponse)
async def get_skill_gap_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
    service = ComprehensiveAnalyticsService(db)
    analysis = await service.analyze_skill_gaps(user_id=current_user.id)
    
    response = SkillGapAnalysisResponse(
        analysis=analysis,
        generated_at=now
    )
    
    # Cache the result
    _analytics_cache[cache_key] = (response, now)
    
    return response


@router.delete("/api/v1/analytics/cache")
async def clear_analytics_cache(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear analytics cache for the current user.
    
    This endpoint allows users to force refresh their analytics data
    by clearing the cache. Useful after bulk data imports or updates.
    
    Requirements: 10.4
    """
    service = ComprehensiveAnalyticsService(db)
    count = service.invalidate_user_cache(user_id=current_user.id)
    
    # Also clear in-memory cache
    keys_to_delete = [k for k in _analytics_cache.keys() if str(current_user.id) in k]
    for key in keys_to_delete:
        _analytics_cache.pop(key, None)
    
    return {
        "message": "Analytics cache cleared successfully",
        "entries_cleared": count + len(keys_to_delete)
    }


@router.get("/api/v1/analytics/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics cache statistics.
    
    Provides information about cache performance and usage.
    
    Requirements: 10.4
    """
    from ..services.analytics_cache_service import get_analytics_cache
    
    cache = get_analytics_cache()
    stats = cache.get_stats()
    
    return {
        "cache_stats": stats,
        "in_memory_cache_size": len(_analytics_cache)
    }
