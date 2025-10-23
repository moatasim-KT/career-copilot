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

from ...schemas.analytics import AnalyticsSummaryResponse, InterviewTrendsResponse

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
    analytics_service = AnalyticsService(db=db)
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


@router.get("/api/v1/analytics/comprehensive-dashboard")
async def get_comprehensive_dashboard(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics data for dashboard visualization."""
    analytics_service = AnalyticsService(db=db)
    
    # Get basic summary
    summary = analytics_service.get_user_analytics(current_user)
    
    # Get time-based trends
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Application trends over time
    applications_by_date = db.query(
        func.date(Application.applied_date).label('date'),
        func.count(Application.id).label('count')
    ).filter(
        Application.user_id == current_user.id,
        Application.applied_date >= start_date,
        Application.applied_date <= end_date
    ).group_by(func.date(Application.applied_date)).all()
    
    # Success rate trends (weekly)
    weekly_stats = []
    for i in range(0, days, 7):
        week_start = end_date - timedelta(days=i+7)
        week_end = end_date - timedelta(days=i)
        
        week_applications = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.applied_date >= week_start,
            Application.applied_date <= week_end
        ).count()
        
        week_interviews = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.applied_date >= week_start,
            Application.applied_date <= week_end,
            Application.status == 'interview'
        ).count()
        
        week_offers = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.applied_date >= week_start,
            Application.applied_date <= week_end,
            Application.status.in_(['offer', 'accepted'])
        ).count()
        
        weekly_stats.append({
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'applications': week_applications,
            'interviews': week_interviews,
            'offers': week_offers,
            'interview_rate': (week_interviews / week_applications * 100) if week_applications > 0 else 0,
            'offer_rate': (week_offers / week_applications * 100) if week_applications > 0 else 0
        })
    
    return {
        'summary': summary,
        'application_trends': [
            {'date': date.isoformat(), 'applications': count}
            for date, count in applications_by_date
        ],
        'weekly_performance': weekly_stats[:12],  # Last 12 weeks
        'generated_at': datetime.utcnow().isoformat()
    }
