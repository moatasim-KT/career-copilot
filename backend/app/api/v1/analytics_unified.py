"""
Unified Analytics API endpoints for comprehensive job application tracking and analysis.
Combines functionality from analytics.py, v1/analytics.py, and advanced_user_analytics.py
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
async def get_analytics_timeline(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get analytics timeline data."""
	try:
		# Get applications over time (last 90 days)
		ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)

		timeline_data = await db.execute(
			select(func.date(Application.created_at).label("date"), func.count(Application.id).label("count"))
			.where(and_(Application.user_id == current_user.id, Application.created_at >= ninety_days_ago))
			.group_by(func.date(Application.created_at))
			.order_by(func.date(Application.created_at))
		)

		return [{"date": str(date), "count": count} for date, count in timeline_data]

	except Exception as e:
		logger.error(f"Failed to get analytics timeline: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve analytics timeline")


@router.get("/analytics/status")
async def get_analytics_status(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get current analytics processing status."""
	return {"status": "active", "last_updated": datetime.now(timezone.utc), "cache_size": len(_analytics_cache), "user_id": current_user.id}


# ===== ADVANCED ANALYTICS ENDPOINTS =====


@router.get("/api/v1/analytics/interview-trends", response_model=InterviewTrendsResponse)
async def get_interview_trends(
	days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get interview trends and patterns analysis."""
	try:
		analytics_service = AnalyticsService(db)
		trends = await analytics_service.get_interview_trends(user_id=current_user.id, days=days)

		return InterviewTrendsResponse(
			period_days=days,
			interview_rate=trends.get("interview_rate", 0),
			average_interviews_per_week=trends.get("average_interviews_per_week", 0),
			peak_interview_days=trends.get("peak_interview_days", []),
			trends_data=trends.get("trends_data", []),
			insights=trends.get("insights", []),
		)

	except Exception as e:
		logger.error(f"Failed to get interview trends: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve interview trends")


@router.get("/api/v1/analytics/comprehensive-dashboard")
async def get_comprehensive_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get comprehensive analytics dashboard data."""
	try:
		analytics_service = AnalyticsService(db)

		# Get multiple analytics in parallel
		summary = await get_analytics_summary(current_user, db)
		interview_trends = await get_interview_trends(90, current_user, db)
		success_rates = await get_detailed_success_rates(90, current_user, db)

		return {"summary": summary, "interview_trends": interview_trends, "success_rates": success_rates, "generated_at": datetime.now(timezone.utc)}

	except Exception as e:
		logger.error(f"Failed to get comprehensive dashboard: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve comprehensive dashboard")


@router.get("/api/v1/analytics/comprehensive-summary", response_model=ComprehensiveAnalyticsSummary)
async def get_comprehensive_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get comprehensive analytics summary with all key metrics."""
	try:
		analytics_service = AnalyticsService(db)
		summary = await analytics_service.get_comprehensive_summary(user_id=current_user.id)

		return ComprehensiveAnalyticsSummary(**summary)

	except Exception as e:
		logger.error(f"Failed to get comprehensive summary: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve comprehensive summary")


@router.get("/api/v1/analytics/trends", response_model=TrendAnalysisResponse)
async def get_analytics_trends(
	period: str = Query(default="90d", description="Analysis period"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get analytics trends over time."""
	try:
		analytics_service = AnalyticsService(db)
		trends = await analytics_service.get_trends_analysis(user_id=current_user.id, period=period)

		return TrendAnalysisResponse(**trends)

	except Exception as e:
		logger.error(f"Failed to get analytics trends: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve analytics trends")


@router.get("/api/v1/analytics/skill-gap-analysis", response_model=SkillGapAnalysisResponse)
async def get_skill_gap_analysis(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get skill gap analysis for the current user."""
	try:
		analytics_service = AnalyticsService(db)
		analysis = await analytics_service.get_skill_gap_analysis(user_id=current_user.id)

		return SkillGapAnalysisResponse(**analysis)

	except Exception as e:
		logger.error(f"Failed to get skill gap analysis: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve skill gap analysis")


# ===== CACHE MANAGEMENT =====


@router.delete("/api/v1/analytics/cache")
async def clear_analytics_cache(current_user: User = Depends(get_current_user)):
	"""Clear analytics cache for the current user."""
	try:
		# Clear user-specific cache entries
		keys_to_remove = [key for key in _analytics_cache.keys() if f"_{current_user.id}" in key]
		for key in keys_to_remove:
			del _analytics_cache[key]

		return {"message": f"Cleared {len(keys_to_remove)} cache entries"}

	except Exception as e:
		logger.error(f"Failed to clear analytics cache: {e}")
		raise HTTPException(status_code=500, detail="Failed to clear analytics cache")


@router.get("/api/v1/analytics/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
	"""Get analytics cache statistics."""
	user_cache_entries = [key for key in _analytics_cache.keys() if f"_{current_user.id}" in key]

	return {
		"total_cache_entries": len(_analytics_cache),
		"user_cache_entries": len(user_cache_entries),
		"cache_ttl_minutes": _cache_ttl.total_seconds() / 60,
	}


# ===== DASHBOARD ENDPOINTS =====


@router.get("/api/v1/analytics/dashboard")
async def get_analytics_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get analytics dashboard data."""
	try:
		# Get summary and recent activity
		summary = await get_analytics_summary(current_user, db)
		timeline = await get_analytics_timeline(current_user, db)

		return {"summary": summary, "timeline": timeline, "last_updated": datetime.now(timezone.utc)}

	except Exception as e:
		logger.error(f"Failed to get analytics dashboard: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve analytics dashboard")


@router.get("/api/v1/analytics/performance-metrics")
async def get_performance_metrics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get performance metrics for analytics."""
	try:
		analytics_service = AnalyticsService(db)
		metrics = await analytics_service.get_performance_metrics(user_id=current_user.id)

		return metrics

	except Exception as e:
		logger.error(f"Failed to get performance metrics: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


# ===== RISK ANALYSIS ENDPOINTS =====


@router.get("/api/v1/analytics/risk-trends")
async def get_risk_trends_v1(
	request: Request,
	time_period: str = Query(default="30d", description="Time period for analysis"),
	contract_types: Optional[List[str]] = Query(default=None, description="Filter by contract types"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get risk trend analysis over time (v1 endpoint)."""
	try:
		# Instantiate consolidated analytics service with the request DB session
		analytics_service = AnalyticsService(db)

		# Log analytics request
		log_audit_event(
			"analysis_request",
			user_id=current_user.id,
			details={"action": "risk_trend_analysis", "result": "started", "time_period": time_period},
		)

		# Get risk trends using the service
		trend_data = await analytics_service.analyze_risk_trends(time_period=time_period, contract_types=contract_types, user_id=current_user.id)

		return {
			"period": trend_data.period,
			"average_risk_score": trend_data.average_risk_score,
			"risk_count": trend_data.risk_count,
			"high_risk_percentage": trend_data.high_risk_percentage,
			"trend": trend_data.trend.value,
			"confidence": trend_data.confidence,
			"metadata": trend_data.metadata,
		}

	except Exception as e:
		logger.error(f"Risk trends analysis failed: {e}")
		raise HTTPException(status_code=500, detail="Risk trends analysis failed")


@router.get("/analytics/risk-trends", tags=["Analytics"])
async def get_risk_trends(
	request: Request,
	time_period: str = Query(default="30d", description="Time period for analysis"),
	contract_types: Optional[List[str]] = Query(default=None, description="Filter by contract types"),
	user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
):
	"""Get risk trend analysis over time (legacy endpoint)."""
	# This is a legacy endpoint - redirect to v1
	from fastapi.responses import RedirectResponse

	return RedirectResponse(url=f"/api/v1/analytics/risk-trends?time_period={time_period}")


# ===== SUCCESS ANALYSIS ENDPOINTS =====


@router.get("/api/v1/analytics/success-metrics")
async def get_success_metrics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get success metrics analysis."""
	try:
		analytics_service = AnalyticsService(db)
		metrics = await analytics_service.get_success_metrics(user_id=current_user.id)

		return metrics

	except Exception as e:
		logger.error(f"Failed to get success metrics: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve success metrics")


@router.get("/api/v1/analytics/application-velocity")
async def get_application_velocity(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get application velocity metrics."""
	try:
		analytics_service = AnalyticsService(db)
		velocity = await analytics_service.get_application_velocity(user_id=current_user.id)

		return velocity

	except Exception as e:
		logger.error(f"Failed to get application velocity: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve application velocity")


# ===== ADVANCED USER ANALYTICS ENDPOINTS =====


@router.get("/api/v1/analytics/success-rates")
async def get_detailed_success_rates(
	days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
):
	"""Get detailed application success rate analysis."""
	try:
		analysis = analytics_specialized_service.calculate_detailed_success_rates(db=db, user_id=current_user.id, days=days)

		if "error" in analysis:
			raise HTTPException(status_code=404, detail=analysis["error"])

		return analysis

	except Exception as e:
		logger.error(f"Failed to get detailed success rates: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve detailed success rates")


@router.get("/api/v1/analytics/conversion-funnel")
async def get_conversion_funnel(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get application conversion funnel analysis."""
	try:
		funnel = analytics_specialized_service.analyze_conversion_funnel(db=db, user_id=current_user.id)

		return funnel

	except Exception as e:
		logger.error(f"Failed to get conversion funnel: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve conversion funnel")


@router.get("/api/v1/analytics/performance-benchmarks")
async def get_performance_benchmarks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get performance benchmarks comparison."""
	try:
		benchmarks = analytics_specialized_service.get_performance_benchmarks(db=db, user_id=current_user.id)

		return benchmarks

	except Exception as e:
		logger.error(f"Failed to get performance benchmarks: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve performance benchmarks")


@router.get("/api/v1/analytics/predictive-analytics")
async def get_predictive_analytics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get predictive analytics insights."""
	try:
		predictions = analytics_specialized_service.generate_predictive_insights(db=db, user_id=current_user.id)

		return predictions

	except Exception as e:
		logger.error(f"Failed to get predictive analytics: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve predictive analytics")


@router.get("/api/v1/analytics/performance-trends")
async def get_performance_trends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""Get performance trends analysis."""
	try:
		trends = analytics_specialized_service.analyze_performance_trends(db=db, user_id=current_user.id)

		return trends

	except Exception as e:
		logger.error(f"Failed to get performance trends: {e}")
		raise HTTPException(status_code=500, detail="Failed to retrieve performance trends")


# ===== LEGACY ENDPOINTS (Redirect to v1) =====


@router.get("/analytics/contract-comparison", tags=["Analytics"])
async def compare_contracts(
	request: Request,
	contract_1_id: str = Query(description="First contract ID"),
	contract_2_id: str = Query(description="Second contract ID"),
	comparison_type: str = Query(default="comprehensive", description="Type of comparison"),
):
	"""Compare two contracts (legacy endpoint - deprecated)."""
	# Legacy endpoint - redirect to appropriate service
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")


@router.get("/analytics/compliance-check", tags=["Analytics"])
async def compliance_check(
	request: Request,
	contract_id: str = Query(description="Contract ID to check"),
):
	"""Check contract compliance (legacy endpoint - deprecated)."""
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")


@router.get("/analytics/cost-analysis", tags=["Analytics"])
async def cost_analysis(
	request: Request,
	contract_id: str = Query(description="Contract ID to analyze"),
):
	"""Analyze contract costs (legacy endpoint - deprecated)."""
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")


@router.get("/analytics/performance-metrics", tags=["Analytics"])
async def get_legacy_performance_metrics(
	request: Request,
	contract_id: Optional[str] = Query(default=None, description="Contract ID"),
):
	"""Get performance metrics (legacy endpoint - deprecated)."""
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")


@router.get("/analytics/dashboard", tags=["Analytics"])
async def get_legacy_dashboard(request: Request):
	"""Get analytics dashboard (legacy endpoint - deprecated)."""
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")


@router.get("/analytics/langsmith-metrics", tags=["Analytics"])
async def get_langsmith_metrics(request: Request):
	"""Get LangSmith metrics (legacy endpoint - deprecated)."""
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")


@router.get("/analytics/langsmith-summary", tags=["Analytics"])
async def get_langsmith_summary(request: Request):
	"""Get LangSmith summary (legacy endpoint - deprecated)."""
	raise HTTPException(status_code=410, detail="This endpoint has been deprecated")
