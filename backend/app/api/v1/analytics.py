"""Analytics endpoints"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.application import Application
from ...models.user import User
from ...schemas.analytics import (AnalyticsSummaryResponse,
                                  InterviewTrendsResponse)
from ...services.analytics_service import AnalyticsService

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
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, Application.status.in_(["interested", "applied"]))
		)
	)
	pending_applications = pending_result.scalar() or 0
	
	interviews_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, Application.status == "interview")
		)
	)
	interviews_scheduled = interviews_result.scalar() or 0
	
	offers_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, Application.status.in_(["offer", "accepted"]))
		)
	)
	offers_received = offers_result.scalar() or 0
	
	rejections_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, Application.status == "rejected")
		)
	)
	rejections_received = rejections_result.scalar() or 0
	
	accepted_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, Application.status == "accepted")
		)
	)
	accepted_applications = accepted_result.scalar() or 0
	acceptance_rate = (accepted_applications / offers_received * 100) if offers_received > 0 else 0.0
	
	# Time-based queries
	today = datetime.now(timezone.utc).date()
	daily_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, func.date(Application.applied_date) == today)
		)
	)
	daily_applications_today = daily_result.scalar() or 0
	
	one_week_ago = today - timedelta(days=7)
	weekly_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, func.date(Application.applied_date) >= one_week_ago)
		)
	)
	weekly_applications = weekly_result.scalar() or 0
	
	one_month_ago = today - timedelta(days=30)
	monthly_result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, func.date(Application.applied_date) >= one_month_ago)
		)
	)
	monthly_applications = monthly_result.scalar() or 0
	
	daily_application_goal = current_user.daily_application_goal if current_user.daily_application_goal is not None else 10
	goal_progress = (daily_applications_today / daily_application_goal * 100) if daily_application_goal > 0 else 0.0
	
	# Get application status breakdown
	status_result = await db.execute(
		select(Application.status, func.count(Application.id))
		.where(Application.user_id == current_user.id)
		.group_by(Application.status)
	)
	status_breakdown = {status: count for status, count in status_result.all()}
	
	# Get top skills from jobs (simplified version)
	# This would ideally come from job tech_stack analysis
	top_skills_in_jobs = []
	
	# Get top companies applied to
	companies_result = await db.execute(
		select(Job.company, func.count(Application.id).label('count'))
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
	
	result = await db.execute(
		select(Application)
		.where(Application.user_id == current_user.id)
		.order_by(Application.applied_date.desc())
		.limit(50)
	)
	applications = result.scalars().all()

	return [{"date": app.applied_date, "status": app.status, "job_id": app.job_id} for app in applications]


@router.get("/analytics/status")
async def get_status_breakdown(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	from sqlalchemy import select
	
	result = await db.execute(
		select(Application.status, func.count(Application.id))
		.where(Application.user_id == current_user.id)
		.group_by(Application.status)
	)
	status_counts = result.all()

	return {"breakdown": [{"status": status, "count": count} for status, count in status_counts]}


@router.get("/api/v1/analytics/interview-trends", response_model=InterviewTrendsResponse)
async def get_interview_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get analysis of interview trends for the current user."""
	from sqlalchemy import and_, select

	# Count interviews by status
	result = await db.execute(
		select(func.count()).select_from(Application).where(
			and_(Application.user_id == current_user.id, Application.status == "interview")
		)
	)
	total_interviews = result.scalar() or 0
	
	# For now, return basic interview trend data
	# TODO: Implement full interview trends analysis
	return {
		"total_interviews": total_interviews,
		"avg_preparation_time": 0,
		"success_rate": 0.0,
		"common_topics": [],
		"difficulty_distribution": {}
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
		.where(
			and_(
				Application.user_id == current_user.id, 
				Application.applied_date >= start_date, 
				Application.applied_date <= end_date
			)
		)
		.group_by(func.date(Application.applied_date))
	)
	applications_by_date = result.all()

	# For now, return simplified data
	# TODO: Implement full weekly performance analysis with async queries
	return {
		"application_trends": [{"date": date.isoformat() if hasattr(date, 'isoformat') else str(date), "applications": count} for date, count in applications_by_date],
		"weekly_performance": [],
		"generated_at": datetime.now(timezone.utc).isoformat(),
	}

