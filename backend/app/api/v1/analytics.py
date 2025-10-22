"""Analytics endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime, timedelta
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.application import Application
from ...models.job import Job
from ...services.analytics import AnalyticsService

from ...schemas.analytics import AnalyticsSummaryResponse

_analytics_cache = {}
_cache_ttl = timedelta(minutes=5) # Cache for 5 minutes

router = APIRouter(tags=["analytics"])


@router.get("/api/v1/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a summary of job application analytics for the current user."""
    # Check cache first
    cache_key = f"analytics_summary_{current_user.id}"
    now = datetime.utcnow()
    
    if cache_key in _analytics_cache:
        cached_data, cached_time = _analytics_cache[cache_key]
        if now - cached_time < _cache_ttl:
            return cached_data
    
    # Generate fresh analytics data
    analytics_service = JobAnalyticsService(db=db)
    summary = analytics_service.get_user_analytics(current_user)
    
    # Cache the result
    _analytics_cache[cache_key] = (summary, now)
    
    return summary


@router.get("/analytics/timeline")
async def get_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    applications = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.applied_date.desc()).limit(50).all()
    
    return [
        {
            "date": app.applied_date,
            "status": app.status,
            "job_id": app.job_id
        }
        for app in applications
    ]


@router.get("/analytics/status")
async def get_status_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    status_counts = db.query(
        Application.status,
        func.count(Application.id)
    ).filter(
        Application.user_id == current_user.id
    ).group_by(Application.status).all()
    
    return {
        "breakdown": [
            {"status": status, "count": count}
            for status, count in status_counts
        ]
    }


@router.get("/api/v1/analytics/interview-trends", response_model=InterviewTrendsResponse)
async def get_interview_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis of interview trends for the current user."""
    analytics_service = AnalyticsService(db=db)
    trends = analytics_service.get_interview_trends(current_user)
    return trends
