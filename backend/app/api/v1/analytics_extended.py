"""
Analytics and Reporting Endpoints
Provides comprehensive analytics dashboards, metrics, and insights
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.logging import get_logger
from ...models.application import Application
from ...models.job import Job
from ...models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard")
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
		start_date = datetime(2020, 1, 1)

	# Get applications in time range
	apps_stmt = select(Application).where(Application.user_id == current_user.id, Application.created_at >= start_date)
	apps_result = await db.execute(apps_stmt)
	applications = apps_result.scalars().all()

	# Get jobs in time range
	jobs_stmt = select(Job).where(Job.user_id == current_user.id, Job.created_at >= start_date)
	jobs_result = await db.execute(jobs_stmt)
	jobs = jobs_result.scalars().all()

	# Calculate metrics
	total_applications = len(applications)
	total_jobs = len(jobs)

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
	responded_apps = sum(status_counts.get(status, 0) for status in ["interview", "offer", "rejected"])
	response_rate = (responded_apps / total_applications * 100) if total_applications > 0 else 0

	return {
		"time_range": time_range,
		"period_start": start_date.isoformat(),
		"period_end": now.isoformat(),
		"summary": {
			"total_jobs_tracked": total_jobs,
			"total_applications": total_applications,
			"success_rate": round(success_rate, 2),
			"response_rate": round(response_rate, 2),
			"active_applications": status_counts.get("applied", 0) + status_counts.get("interview", 0),
		},
		"application_status_breakdown": status_counts,
		"top_companies": [{"company": c[0], "count": c[1]} for c in top_companies],
		"top_technologies": [{"technology": t[0], "count": t[1]} for t in top_technologies],
		"timeline": {
			"applications_over_time": _get_timeline_data(applications),
			"jobs_over_time": _get_timeline_data(jobs),
		},
	}


@router.get("/performance-metrics")
async def get_performance_metrics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get user performance metrics and KPIs.

	Returns:
		dict: Performance metrics including conversion rates, avg time to response, etc.
	"""
	# Get all applications
	apps_stmt = select(Application).where(Application.user_id == current_user.id)
	apps_result = await db.execute(apps_stmt)
	applications = apps_result.scalars().all()

	if not applications:
		return {
			"total_applications": 0,
			"conversion_rates": {
				"applied_to_interview": 0,
				"interview_to_offer": 0,
				"offer_to_accepted": 0,
			},
			"average_time_metrics": {},
			"weekly_application_rate": 0,
		}

	# Calculate conversion rates
	applied_count = sum(1 for a in applications if a.status == "applied")
	interview_count = sum(1 for a in applications if a.status == "interview")
	offer_count = sum(1 for a in applications if a.status == "offer")
	accepted_count = sum(1 for a in applications if a.status == "accepted")

	applied_to_interview = (interview_count / applied_count * 100) if applied_count > 0 else 0
	interview_to_offer = (offer_count / interview_count * 100) if interview_count > 0 else 0
	offer_to_accepted = (accepted_count / offer_count * 100) if offer_count > 0 else 0

	# Calculate time metrics
	time_to_first_response = _calculate_avg_time_to_response(applications)

	# Weekly application rate
	now = datetime.utcnow()
	last_30_days = now - timedelta(days=30)
	recent_apps = [a for a in applications if a.created_at >= last_30_days]
	weekly_rate = len(recent_apps) / 4.3  # Average weeks in a month

	return {
		"total_applications": len(applications),
		"conversion_rates": {
			"applied_to_interview": round(applied_to_interview, 2),
			"interview_to_offer": round(interview_to_offer, 2),
			"offer_to_accepted": round(offer_to_accepted, 2),
		},
		"average_time_metrics": {
			"days_to_first_response": round(time_to_first_response, 1) if time_to_first_response else None,
		},
		"weekly_application_rate": round(weekly_rate, 1),
		"status_breakdown": {
			"applied": applied_count,
			"interview": interview_count,
			"offer": offer_count,
			"accepted": accepted_count,
			"rejected": sum(1 for a in applications if a.status == "rejected"),
		},
	}


@router.get("/risk-trends")
async def get_risk_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Analyze risk factors and trends in job search.

	Returns:
		dict: Risk analysis including application velocity, response rates, market trends
	"""
	# Get recent applications (last 60 days)
	sixty_days_ago = datetime.utcnow() - timedelta(days=60)

	apps_stmt = select(Application).where(Application.user_id == current_user.id, Application.created_at >= sixty_days_ago)
	apps_result = await db.execute(apps_stmt)
	recent_apps = apps_result.scalars().all()

	# Calculate risk indicators
	total_apps = len(recent_apps)

	if total_apps == 0:
		return {
			"risk_level": "high",
			"risk_score": 85,
			"risk_factors": ["No recent applications - job search appears inactive"],
			"recommendations": ["Start applying to positions regularly", "Set weekly application goals"],
		}

	# Calculate application velocity (apps per week)
	velocity = total_apps / 8.6  # 60 days ≈ 8.6 weeks

	# Response rate
	responded = sum(1 for a in recent_apps if a.status in ["interview", "offer", "rejected"])
	response_rate = (responded / total_apps * 100) if total_apps > 0 else 0

	# Rejection rate
	rejections = sum(1 for a in recent_apps if a.status == "rejected")
	rejection_rate = (rejections / total_apps * 100) if total_apps > 0 else 0

	# Determine risk level
	risk_factors = []
	risk_score = 0

	if velocity < 2:
		risk_factors.append("Low application velocity (< 2 per week)")
		risk_score += 25

	if response_rate < 20:
		risk_factors.append("Low response rate from employers")
		risk_score += 20

	if rejection_rate > 50:
		risk_factors.append("High rejection rate - may need to adjust targeting")
		risk_score += 25

	if total_apps < 10:
		risk_factors.append("Small sample size - need more applications for better insights")
		risk_score += 15

	# Determine risk level
	if risk_score < 20:
		risk_level = "low"
	elif risk_score < 50:
		risk_level = "medium"
	else:
		risk_level = "high"

	# Generate recommendations
	recommendations = []
	if velocity < 3:
		recommendations.append("Increase application volume to 5-10 per week")
	if response_rate < 20:
		recommendations.append("Review and improve resume/cover letter quality")
	if rejection_rate > 50:
		recommendations.append("Focus on better-matching positions")

	return {
		"risk_level": risk_level,
		"risk_score": risk_score,
		"risk_factors": risk_factors if risk_factors else ["Job search is healthy"],
		"recommendations": recommendations if recommendations else ["Keep up the good work!"],
		"metrics": {
			"application_velocity": round(velocity, 1),
			"response_rate": round(response_rate, 1),
			"rejection_rate": round(rejection_rate, 1),
			"total_applications_60d": total_apps,
		},
	}


@router.get("/success-metrics")
async def get_success_metrics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get success metrics and achievement tracking.

	Returns:
		dict: Success indicators, milestones, and achievements
	"""
	# Get all applications
	apps_stmt = select(Application).where(Application.user_id == current_user.id)
	apps_result = await db.execute(apps_stmt)
	applications = apps_result.scalars().all()

	# Calculate success metrics
	total_apps = len(applications)
	interviews = sum(1 for a in applications if a.status == "interview")
	offers = sum(1 for a in applications if a.status == "offer")
	accepted = sum(1 for a in applications if a.status == "accepted")

	# Milestones
	milestones = []
	if total_apps >= 10:
		milestones.append({"name": "First 10 Applications", "achieved": True})
	if total_apps >= 50:
		milestones.append({"name": "50 Applications Milestone", "achieved": True})
	if total_apps >= 100:
		milestones.append({"name": "Century Club", "achieved": True})
	if interviews >= 5:
		milestones.append({"name": "5 Interviews", "achieved": True})
	if offers >= 1:
		milestones.append({"name": "First Offer", "achieved": True})
	if accepted >= 1:
		milestones.append({"name": "Job Secured", "achieved": True})

	# Next milestones
	next_milestones = []
	if total_apps < 10:
		next_milestones.append({"name": "First 10 Applications", "progress": total_apps, "goal": 10})
	elif total_apps < 50:
		next_milestones.append({"name": "50 Applications", "progress": total_apps, "goal": 50})
	elif total_apps < 100:
		next_milestones.append({"name": "Century Club", "progress": total_apps, "goal": 100})

	if interviews < 5:
		next_milestones.append({"name": "5 Interviews", "progress": interviews, "goal": 5})

	return {
		"success_summary": {
			"total_applications": total_apps,
			"interviews_secured": interviews,
			"offers_received": offers,
			"jobs_accepted": accepted,
			"success_rate": round((offers / total_apps * 100) if total_apps > 0 else 0, 2),
		},
		"milestones_achieved": milestones,
		"next_milestones": next_milestones,
		"streaks": {
			"current_application_streak": _calculate_current_streak(applications),
			"longest_application_streak": _calculate_longest_streak(applications),
		},
	}


@router.get("/application-velocity")
async def get_application_velocity(
	current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), days: int = Query(30, description="Number of days to analyze")
):
	"""
	Analyze application velocity and trends over time.

	Args:
		current_user: Current authenticated user
		db: Database session
		days: Number of days to analyze

	Returns:
		dict: Velocity metrics and trends
	"""
	# Get applications in time range
	start_date = datetime.utcnow() - timedelta(days=days)

	apps_stmt = select(Application).where(Application.user_id == current_user.id, Application.created_at >= start_date)
	apps_result = await db.execute(apps_stmt)
	applications = apps_result.scalars().all()

	# Calculate daily counts
	daily_counts = {}
	for app in applications:
		date_key = app.created_at.date().isoformat()
		daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

	# Calculate weekly average
	weeks = days / 7
	weekly_avg = len(applications) / weeks if weeks > 0 else 0

	# Calculate trend (comparing first half to second half)
	midpoint = start_date + timedelta(days=days / 2)
	first_half = [a for a in applications if a.created_at < midpoint]
	second_half = [a for a in applications if a.created_at >= midpoint]

	if len(first_half) > 0:
		trend_change = ((len(second_half) - len(first_half)) / len(first_half)) * 100
	else:
		trend_change = 100 if len(second_half) > 0 else 0

	trend = "increasing" if trend_change > 10 else "decreasing" if trend_change < -10 else "stable"

	return {
		"period_days": days,
		"total_applications": len(applications),
		"weekly_average": round(weekly_avg, 1),
		"daily_average": round(len(applications) / days, 1),
		"trend": trend,
		"trend_change_percent": round(trend_change, 1),
		"daily_breakdown": daily_counts,
		"recommendations": _get_velocity_recommendations(weekly_avg, trend),
	}


# ==================== Helper Functions ====================


def _get_timeline_data(items: List[Any]) -> List[Dict[str, Any]]:
	"""Group items by date for timeline visualization."""
	timeline = {}
	for item in items:
		date_key = item.created_at.date().isoformat()
		timeline[date_key] = timeline.get(date_key, 0) + 1

	return [{"date": date, "count": count} for date, count in sorted(timeline.items())]


def _calculate_avg_time_to_response(applications: List[Application]) -> float | None:
	"""Calculate average days from application to first response."""
	response_times = []

	for app in applications:
		if app.status in ["interview", "offer", "rejected"] and app.updated_at and app.created_at:
			days = (app.updated_at - app.created_at).days
			if days > 0:  # Only count actual responses
				response_times.append(days)

	if not response_times:
		return None

	return sum(response_times) / len(response_times)


def _calculate_current_streak(applications: List[Application]) -> int:
	"""Calculate current daily application streak."""
	if not applications:
		return 0

	# Sort by date descending
	sorted_apps = sorted(applications, key=lambda a: a.created_at, reverse=True)

	current_date = datetime.utcnow().date()
	streak = 0

	# Check if there was an application today or yesterday
	most_recent = sorted_apps[0].created_at.date()
	if (current_date - most_recent).days > 1:
		return 0

	# Count consecutive days
	for i, app in enumerate(sorted_apps):
		app_date = app.created_at.date()
		if i == 0:
			streak = 1
			continue

		prev_date = sorted_apps[i - 1].created_at.date()
		if (prev_date - app_date).days == 1:
			streak += 1
		else:
			break

	return streak


def _calculate_longest_streak(applications: List[Application]) -> int:
	"""Calculate longest daily application streak."""
	if not applications:
		return 0

	sorted_apps = sorted(applications, key=lambda a: a.created_at)

	max_streak = 1
	current_streak = 1

	for i in range(1, len(sorted_apps)):
		prev_date = sorted_apps[i - 1].created_at.date()
		curr_date = sorted_apps[i].created_at.date()

		if (curr_date - prev_date).days == 1:
			current_streak += 1
			max_streak = max(max_streak, current_streak)
		elif (curr_date - prev_date).days > 1:
			current_streak = 1

	return max_streak


def _get_velocity_recommendations(weekly_avg: float, trend: str) -> List[str]:
	"""Generate recommendations based on application velocity."""
	recommendations = []

	if weekly_avg < 3:
		recommendations.append("Consider increasing application volume to 5-10 per week")

	if trend == "decreasing":
		recommendations.append("Application rate is declining - set reminders to maintain momentum")
	elif trend == "increasing":
		recommendations.append("Great momentum! Keep up the consistent application pace")

	if weekly_avg > 15:
		recommendations.append("High application volume - ensure quality isn't sacrificed for quantity")

	return recommendations if recommendations else ["Maintain current application pace"]
