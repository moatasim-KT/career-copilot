"""
Consolidated Analytics Service for Career Copilot.

This service integrates all analytics functionality including:
- Collection (event tracking, batch processing)
- Processing (user behavior, funnels, engagement)
- Querying (metrics retrieval, time-series)
- Reporting (market trends, insights, benchmarks)
- Specialized analytics (success rates, conversion, performance)

Single source of truth for all analytics operations.
"""

import json
import logging
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone, date
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..models.analytics import Analytics
from ..models.application import Application
from ..models.interview import InterviewSession
from ..models.job import Job
from ..models.user import User
from ..schemas.analytics import (
    ApplicationStatusCount,
    TrendDataPoint,
    SkillData,
    CompanyData,
    RateMetrics,
    TrendAnalysis,
    ApplicationTrends,
    SkillGapAnalysis,
    ComprehensiveAnalyticsSummary,
)
from .analytics_cache_service import get_analytics_cache

logger = logging.getLogger(__name__)


class SlackEventType(str, Enum):
    """Slack event types for tracking."""
    MESSAGE = "message"
    REACTION = "reaction"
    FILE_UPLOAD = "file_upload"
    CHANNEL_JOIN = "channel_join"
    CHANNEL_LEAVE = "channel_leave"


class SlackEvent(BaseModel):
    """Slack event model."""
    event_type: SlackEventType
    user_id: str
    channel_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class AnalyticsService:
    """
    Comprehensive consolidated analytics service.
    
    Integrates all analytics functionality:
    - Event collection and batch processing
    - User behavior and funnel analysis
    - Metrics querying and time-series data
    - Market trend analysis and reporting
    - Specialized analytics (success rates, benchmarks)
    """

    def __init__(self, db: AsyncSession | Session | None = None, use_cache: bool = True):
        """
        Initialize consolidated analytics service.
        
        Args:
            db: Database session (AsyncSession or sync Session)
            use_cache: Whether to use caching
        """
        self.db = db
        self.use_cache = use_cache
        self.cache = get_analytics_cache() if use_cache else None
        self._cache_ttl = timedelta(minutes=5)
        
        # Event collection features
        self._event_queue: Deque[Dict[str, Any]] = deque(maxlen=10000)
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self._batch_size = 100
        self._flush_interval = timedelta(seconds=30)
        self._last_flush = datetime.now(timezone.utc)
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_open = False
        
        logger.info("Consolidated AnalyticsService initialized with all features")

    # ========================================================================
    # SECTION 1: COMPREHENSIVE ANALYTICS (from original analytics_service.py)
    # ========================================================================

    async def get_application_counts_by_status(self, user_id: int) -> List[ApplicationStatusCount]:
        """Get application counts grouped by status."""
        result = await self.db.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        
        status_counts = []
        for status, count in result.all():
            status_counts.append(ApplicationStatusCount(status=status, count=count))
        
        return status_counts
    
    async def calculate_rate_metrics(self, user_id: int) -> RateMetrics:
        """Calculate interview rate, offer rate, and acceptance rate."""
        # Total applications
        total_apps_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id)
        )
        total_applications = total_apps_result.scalar() or 0
        
        # Applications that led to interviews
        interviews_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.status.in_(["interview", "offer", "accepted"])
            ))
        )
        interviews = interviews_result.scalar() or 0
        
        # Applications that led to offers
        offers_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.status.in_(["offer", "accepted"])
            ))
        )
        offers = offers_result.scalar() or 0
        
        # Offers that were accepted
        accepted_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.status == "accepted"
            ))
        )
        accepted = accepted_result.scalar() or 0
        
        # Calculate rates
        interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0.0
        offer_rate = (offers / interviews * 100) if interviews > 0 else 0.0
        acceptance_rate = (accepted / offers * 100) if offers > 0 else 0.0
        
        return RateMetrics(
            interview_rate=round(interview_rate, 2),
            offer_rate=round(offer_rate, 2),
            acceptance_rate=round(acceptance_rate, 2)
        )
    
    async def calculate_trend_for_period(
        self,
        user_id: int,
        current_start: date,
        current_end: date,
        previous_start: date,
        previous_end: date
    ) -> TrendAnalysis:
        """Calculate trend analysis for a specific time period."""
        # Current period count
        current_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.applied_date >= current_start,
                Application.applied_date <= current_end
            ))
        )
        current_value = current_result.scalar() or 0
        
        # Previous period count
        previous_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.applied_date >= previous_start,
                Application.applied_date < current_start
            ))
        )
        previous_value = previous_result.scalar() or 0
        
        # Calculate percentage change
        if previous_value > 0:
            percentage_change = ((current_value - previous_value) / previous_value) * 100
        else:
            percentage_change = 100.0 if current_value > 0 else 0.0
        
        # Determine direction
        if percentage_change > 5:
            direction = "up"
        elif percentage_change < -5:
            direction = "down"
        else:
            direction = "neutral"
        
        return TrendAnalysis(
            direction=direction,
            percentage_change=round(percentage_change, 2),
            current_value=current_value,
            previous_value=previous_value
        )
    
    async def calculate_application_trends(self, user_id: int) -> ApplicationTrends:
        """Calculate application trends for daily, weekly, and monthly periods."""
        today = datetime.now(timezone.utc).date()
        
        # Daily trend
        daily_trend = await self.calculate_trend_for_period(
            user_id=user_id,
            current_start=today,
            current_end=today,
            previous_start=today - timedelta(days=1),
            previous_end=today - timedelta(days=1)
        )
        
        # Weekly trend
        week_start = today - timedelta(days=today.weekday())
        last_week_start = week_start - timedelta(days=7)
        weekly_trend = await self.calculate_trend_for_period(
            user_id=user_id,
            current_start=week_start,
            current_end=today,
            previous_start=last_week_start,
            previous_end=week_start - timedelta(days=1)
        )
        
        # Monthly trend
        month_start = today.replace(day=1)
        if month_start.month == 1:
            last_month_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            last_month_start = month_start.replace(month=month_start.month - 1)
        
        monthly_trend = await self.calculate_trend_for_period(
            user_id=user_id,
            current_start=month_start,
            current_end=today,
            previous_start=last_month_start,
            previous_end=month_start - timedelta(days=1)
        )
        
        return ApplicationTrends(
            daily=daily_trend,
            weekly=weekly_trend,
            monthly=monthly_trend
        )
    
    async def get_top_skills_in_jobs(self, user_id: int, limit: int = 10) -> List[SkillData]:
        """Identify top skills from jobs the user has applied to or is interested in."""
        result = await self.db.execute(
            select(Job.tech_stack)
            .where(Job.user_id == user_id)
        )
        
        all_skills = []
        total_jobs = 0
        for (tech_stack,) in result.all():
            if tech_stack:
                total_jobs += 1
                if isinstance(tech_stack, str):
                    try:
                        skills = json.loads(tech_stack)
                    except json.JSONDecodeError:
                        skills = [s.strip() for s in tech_stack.split(',')]
                elif isinstance(tech_stack, list):
                    skills = tech_stack
                else:
                    continue
                
                all_skills.extend([skill.lower().strip() for skill in skills if skill])
        
        skill_counts = Counter(all_skills)
        
        top_skills = []
        for skill, count in skill_counts.most_common(limit):
            percentage = (count / total_jobs * 100) if total_jobs > 0 else 0.0
            top_skills.append(SkillData(
                skill=skill,
                count=count,
                percentage=round(percentage, 2)
            ))
        
        return top_skills
    
    async def get_top_companies_applied(self, user_id: int, limit: int = 10) -> List[CompanyData]:
        """Identify top companies the user has applied to."""
        result = await self.db.execute(
            select(Job.company, func.count(Application.id).label("count"))
            .join(Application, Application.job_id == Job.id)
            .where(Application.user_id == user_id)
            .group_by(Job.company)
            .order_by(desc("count"))
            .limit(limit)
        )
        
        companies = []
        for company, count in result.all():
            companies.append(CompanyData(company=company, count=count))
        
        return companies
    
    async def get_comprehensive_summary(
        self,
        user_id: int,
        analysis_period_days: int = 90
    ) -> ComprehensiveAnalyticsSummary:
        """Get comprehensive analytics summary with all metrics (cached)."""
        # Check cache
        if self.cache:
            cache_key = self.cache._make_key(
                "comprehensive_summary",
                user_id,
                days=analysis_period_days
            )
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for comprehensive summary: {cache_key}")
                return ComprehensiveAnalyticsSummary(**cached)
        
        # Basic counts
        total_jobs_result = await self.db.execute(
            select(func.count()).select_from(Job).where(Job.user_id == user_id)
        )
        total_jobs = total_jobs_result.scalar() or 0
        
        total_apps_result = await self.db.execute(
            select(func.count()).select_from(Application).where(Application.user_id == user_id)
        )
        total_applications = total_apps_result.scalar() or 0
        
        status_counts = await self.get_application_counts_by_status(user_id)
        rates = await self.calculate_rate_metrics(user_id)
        trends = await self.calculate_application_trends(user_id)
        top_skills = await self.get_top_skills_in_jobs(user_id)
        top_companies = await self.get_top_companies_applied(user_id)
        
        # Time-based counts
        today = datetime.now(timezone.utc).date()
        
        daily_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                func.date(Application.applied_date) == today
            ))
        )
        daily_applications = daily_result.scalar() or 0
        
        week_start = today - timedelta(days=7)
        weekly_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.applied_date >= week_start
            ))
        )
        weekly_applications = weekly_result.scalar() or 0
        
        month_start = today - timedelta(days=30)
        monthly_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(and_(
                Application.user_id == user_id,
                Application.applied_date >= month_start
            ))
        )
        monthly_applications = monthly_result.scalar() or 0
        
        user_result = await self.db.execute(
            select(User.daily_application_goal).where(User.id == user_id)
        )
        user_data = user_result.first()
        daily_goal = user_data[0] if user_data and user_data[0] else 10
        
        goal_progress = (daily_applications / daily_goal * 100) if daily_goal > 0 else 0.0
        
        summary = ComprehensiveAnalyticsSummary(
            total_jobs=total_jobs,
            total_applications=total_applications,
            application_counts_by_status=status_counts,
            rates=rates,
            trends=trends,
            top_skills_in_jobs=top_skills,
            top_companies_applied=top_companies,
            daily_applications_today=daily_applications,
            weekly_applications=weekly_applications,
            monthly_applications=monthly_applications,
            daily_application_goal=daily_goal,
            daily_goal_progress=round(goal_progress, 2),
            generated_at=datetime.now(timezone.utc),
            analysis_period_days=analysis_period_days
        )
        
        # Cache result
        if self.cache:
            cache_key = self.cache._make_key(
                "comprehensive_summary",
                user_id,
                days=analysis_period_days
            )
            self.cache.set(cache_key, summary.model_dump(), ttl=self._cache_ttl)
            logger.debug(f"Cached comprehensive summary: {cache_key}")
        
        return summary
    
    async def get_time_series_data(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[TrendDataPoint]:
        """Get time series data for applications over a date range."""
        result = await self.db.execute(
            select(
                func.date(Application.applied_date).label("date"),
                func.count(Application.id).label("count")
            )
            .where(and_(
                Application.user_id == user_id,
                Application.applied_date >= start_date,
                Application.applied_date <= end_date
            ))
            .group_by(func.date(Application.applied_date))
            .order_by(func.date(Application.applied_date))
        )
        
        data_points = []
        for app_date, count in result.all():
            data_points.append(TrendDataPoint(date=app_date, count=count))
        
        return data_points
    
    async def analyze_skill_gaps(self, user_id: int) -> SkillGapAnalysis:
        """Analyze skill gaps between user skills and market demand (cached)."""
        if self.cache:
            cache_key = self.cache._make_key("skill_gap", user_id)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for skill gap analysis: {cache_key}")
                return SkillGapAnalysis(**cached)
        
        user_result = await self.db.execute(
            select(User.skills).where(User.id == user_id)
        )
        user_data = user_result.first()
        
        user_skills = []
        if user_data and user_data[0]:
            skills_data = user_data[0]
            if isinstance(skills_data, str):
                try:
                    user_skills = json.loads(skills_data)
                except json.JSONDecodeError:
                    user_skills = [s.strip().lower() for s in skills_data.split(',')]
            elif isinstance(skills_data, list):
                user_skills = [s.lower().strip() for s in skills_data]
        
        market_skills = await self.get_top_skills_in_jobs(user_id, limit=50)
        user_skills_normalized = set(skill.lower().strip() for skill in user_skills)
        
        missing_skills = []
        for skill_data in market_skills:
            if skill_data.skill.lower() not in user_skills_normalized:
                missing_skills.append(skill_data)
        
        if market_skills:
            skills_covered = len([s for s in market_skills if s.skill.lower() in user_skills_normalized])
            coverage_percentage = (skills_covered / len(market_skills)) * 100
        else:
            coverage_percentage = 0.0
        
        recommendations = [
            f"Consider learning {skill.skill} (appears in {skill.percentage}% of jobs)"
            for skill in missing_skills[:5]
        ]
        
        analysis = SkillGapAnalysis(
            user_skills=list(user_skills),
            market_skills=market_skills[:20],
            missing_skills=missing_skills[:10],
            skill_coverage_percentage=round(coverage_percentage, 2),
            recommendations=recommendations
        )
        
        if self.cache:
            cache_key = self.cache._make_key("skill_gap", user_id)
            self.cache.set(cache_key, analysis.model_dump(), ttl=self._cache_ttl)
            logger.debug(f"Cached skill gap analysis: {cache_key}")
        
        return analysis

    # ========================================================================
    # SECTION 2: USER BEHAVIOR & PROCESSING
    # ========================================================================

    def get_user_analytics(self, user: Any, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a user (sync method for compatibility).
        
        Args:
            user: User object
            days: Number of days to analyze
            
        Returns:
            Dict with user analytics and metrics
        """
        try:
            user_id = getattr(user, "id", None)
            if not user_id:
                return {"error": "Invalid user"}

            jobs = getattr(user, "jobs", []) or []
            applications = getattr(user, "applications", []) or []
            interviews = getattr(user, "interviews", []) or []

            total_jobs = len(jobs)
            total_applications = len(applications)
            total_interviews = len(interviews)

            status_counts = defaultdict(int)
            for app in applications:
                status = getattr(app, "status", "unknown")
                status_counts[status] += 1

            interview_outcomes = defaultdict(int)
            for interview in interviews:
                outcome = getattr(interview, "outcome", "pending")
                interview_outcomes[outcome] += 1

            recent_cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            recent_applications = [
                app for app in applications 
                if getattr(app, "created_at", datetime.min.replace(tzinfo=timezone.utc)) >= recent_cutoff
            ]

            offers = status_counts.get("offer", 0)
            conversion_rate = (offers / total_applications * 100) if total_applications > 0 else 0

            return {
                "user_id": user_id,
                "total_jobs": total_jobs,
                "total_applications": total_applications,
                "total_interviews": total_interviews,
                "application_status_breakdown": dict(status_counts),
                "interview_outcomes": dict(interview_outcomes),
                "offers_received": offers,
                "conversion_rate": round(conversion_rate, 2),
                "recent_applications_count": len(recent_applications),
                "analysis_period_days": days,
            }

        except Exception as e:
            logger.error(f"Failed to get user analytics: {e!s}")
            return {"error": str(e)}

    def process_user_funnel(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze user's application funnel stages (sync method).
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with funnel metrics and conversion rates
        """
        try:
            if not self.db:
                return {"error": "Database connection required"}

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            # Handle both sync and async session
            if hasattr(self.db, 'execute'):  # Sync session
                total_viewed = (
                    self.db.query(func.count(Application.id))
                    .filter(and_(Application.user_id == user_id, Application.created_at >= cutoff))
                    .scalar() or 0
                )

                applied = (
                    self.db.query(func.count(Application.id))
                    .filter(and_(
                        Application.user_id == user_id,
                        Application.status.in_(["applied", "in_review", "interview", "offer"]),
                        Application.created_at >= cutoff,
                    ))
                    .scalar() or 0
                )

                interviews = (
                    self.db.query(func.count(InterviewSession.id))
                    .filter(and_(InterviewSession.user_id == user_id, InterviewSession.scheduled_at >= cutoff))
                    .scalar() or 0
                )

                offers = (
                    self.db.query(func.count(Application.id))
                    .filter(and_(Application.user_id == user_id, Application.status == "offer", Application.created_at >= cutoff))
                    .scalar() or 0
                )

            view_to_apply = (applied / total_viewed * 100) if total_viewed > 0 else 0
            apply_to_interview = (interviews / applied * 100) if applied > 0 else 0
            interview_to_offer = (offers / interviews * 100) if interviews > 0 else 0

            return {
                "funnel_stages": {
                    "viewed": total_viewed,
                    "applied": applied,
                    "interviews": interviews,
                    "offers": offers,
                },
                "conversion_rates": {
                    "view_to_apply": round(view_to_apply, 2),
                    "apply_to_interview": round(apply_to_interview, 2),
                    "interview_to_offer": round(interview_to_offer, 2),
                },
                "overall_conversion": round((offers / total_viewed * 100) if total_viewed > 0 else 0, 2),
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"Failed to process user funnel: {e!s}")
            return {"error": str(e)}

    def calculate_engagement_score(self, user_id: int, days: int = 7) -> float:
        """
        Calculate user engagement score based on activity (sync method).
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            float: Engagement score from 0-100
        """
        try:
            if not self.db:
                return 0.0

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            if hasattr(self.db, 'query'):  # Sync session
                job_views = (
                    self.db.query(func.count(Job.id))
                    .filter(and_(Job.user_id == user_id, Job.date_added >= cutoff))
                    .scalar() or 0
                )

                applications = (
                    self.db.query(func.count(Application.id))
                    .filter(and_(Application.user_id == user_id, Application.created_at >= cutoff))
                    .scalar() or 0
                )

            score = (job_views * 1) + (applications * 10)
            max_score = days * 20
            normalized_score = min(100.0, (score / max_score) * 100)

            return round(normalized_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e!s}")
            return 0.0

    def segment_users(self, days: int = 30) -> Dict[str, List[int]]:
        """
        Segment all users based on behavior patterns (sync method).
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict mapping segment name to list of user IDs
        """
        try:
            if not self.db:
                return {}

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            if hasattr(self.db, 'query'):  # Sync session
                users = self.db.query(User).all()

            segments: Dict[str, List[int]] = {
                "highly_active": [],
                "moderately_active": [],
                "low_activity": [],
                "inactive": [],
            }

            for user in users:
                if hasattr(self.db, 'query'):
                    app_count = (
                        self.db.query(func.count(Application.id))
                        .filter(and_(Application.user_id == user.id, Application.created_at >= cutoff))
                        .scalar() or 0
                    )

                if app_count >= 10:
                    segments["highly_active"].append(user.id)
                elif app_count >= 5:
                    segments["moderately_active"].append(user.id)
                elif app_count >= 1:
                    segments["low_activity"].append(user.id)
                else:
                    segments["inactive"].append(user.id)

            logger.info(f"Segmented {len(users)} users into {len(segments)} segments")
            return segments

        except Exception as e:
            logger.error(f"Failed to segment users: {e!s}")
            return {}

    # ========================================================================
    # SECTION 3: METRICS QUERYING
    # ========================================================================

    def get_metrics(
        self,
        user_id: int,
        timeframe: str | None = None,
        metric_types: List[str] | None = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve analytics metrics for a user (sync method).
        
        Args:
            user_id: User identifier
            timeframe: Time period ('day', 'week', 'month', 'year', 'all')
            metric_types: Specific metrics to retrieve
            use_cache: Whether to use cached results
            
        Returns:
            Dict with requested metrics
        """
        cache_key = f"metrics_{user_id}_{timeframe}_{metric_types}"

        # Check cache
        if use_cache and self.cache and cache_key in self.cache._cache:
            cached_data, cache_time = self.cache._cache[cache_key]
            if datetime.now(timezone.utc) - cache_time < self._cache_ttl:
                logger.debug(f"Returning cached metrics for user {user_id}")
                return cached_data

        try:
            start_date, end_date = self._parse_timeframe(timeframe)

            if not self.db:
                return {"user_id": user_id, "timeframe": timeframe or "all", "metrics": {}}

            metrics: Dict[str, Any] = {}

            if hasattr(self.db, 'query'):  # Sync session
                # Job metrics
                if not metric_types or "jobs" in metric_types:
                    job_query = self.db.query(func.count(Job.id)).filter(Job.user_id == user_id)
                    if start_date:
                        job_query = job_query.filter(Job.date_added >= start_date)
                    if end_date:
                        job_query = job_query.filter(Job.date_added <= end_date)
                    metrics["jobs_saved"] = job_query.scalar() or 0

                # Application metrics
                if not metric_types or "applications" in metric_types:
                    app_query = self.db.query(func.count(Application.id)).filter(Application.user_id == user_id)
                    if start_date:
                        app_query = app_query.filter(Application.created_at >= start_date)
                    if end_date:
                        app_query = app_query.filter(Application.created_at <= end_date)
                    metrics["applications_submitted"] = app_query.scalar() or 0

                    status_query = (
                        self.db.query(Application.status, func.count(Application.id))
                        .filter(Application.user_id == user_id)
                    )
                    if start_date:
                        status_query = status_query.filter(Application.created_at >= start_date)
                    if end_date:
                        status_query = status_query.filter(Application.created_at <= end_date)
                    
                    status_counts = dict(status_query.group_by(Application.status).all())
                    metrics["application_status_breakdown"] = status_counts

                # Interview metrics
                if not metric_types or "interviews" in metric_types:
                    interview_query = self.db.query(func.count(InterviewSession.id)).filter(InterviewSession.user_id == user_id)
                    if start_date:
                        interview_query = interview_query.filter(InterviewSession.scheduled_at >= start_date)
                    if end_date:
                        interview_query = interview_query.filter(InterviewSession.scheduled_at <= end_date)
                    metrics["interviews_scheduled"] = interview_query.scalar() or 0

            result = {
                "user_id": user_id,
                "timeframe": timeframe or "all",
                "start_date": start_date,
                "end_date": end_date,
                "metrics": metrics
            }

            # Cache result
            if self.cache:
                self.cache._cache[cache_key] = (result, datetime.now(timezone.utc))

            logger.info(f"Retrieved metrics for user {user_id} (timeframe: {timeframe})")
            return result

        except Exception as e:
            logger.error(f"Failed to get metrics for user {user_id}: {e!s}")
            return {"user_id": user_id, "error": str(e)}

    def _parse_timeframe(self, timeframe: str | None) -> Tuple[datetime | None, datetime | None]:
        """
        Parse timeframe string into start and end dates.
        
        Args:
            timeframe: Timeframe string
            
        Returns:
            Tuple of (start_date, end_date)
        """
        now = datetime.now(timezone.utc)

        if not timeframe or timeframe == "all":
            return (None, None)
        elif timeframe in ("day", "today"):
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return (start, now)
        elif timeframe == "week":
            start = now - timedelta(days=7)
            return (start, now)
        elif timeframe == "month":
            start = now - timedelta(days=30)
            return (start, now)
        elif timeframe == "year":
            start = now - timedelta(days=365)
            return (start, now)
        else:
            try:
                days = int(timeframe)
                start = now - timedelta(days=days)
                return (start, now)
            except ValueError:
                logger.warning(f"Invalid timeframe: {timeframe}, using 'all'")
                return (None, None)

    def clear_cache(self, user_id: int | None = None) -> None:
        """
        Clear query cache.
        
        Args:
            user_id: Optional user ID to clear specific cache
        """
        if not self.cache:
            return
            
        if user_id:
            keys_to_remove = [k for k in self.cache._cache.keys() if f"_{user_id}_" in k]
            for key in keys_to_remove:
                del self.cache._cache[key]
            logger.info(f"Cleared cache for user {user_id}")
        else:
            self.cache._cache.clear()
            logger.info("Cleared all query cache")

    # ========================================================================
    # SECTION 4: MARKET TRENDS & REPORTING
    # ========================================================================

    def analyze_market_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze market trends relevant to user (sync method).
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with market trend insights
        """
        try:
            if not self.db:
                return {"user_id": user_id, "error": "Database connection required"}

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            if hasattr(self.db, 'query'):  # Sync session
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"error": "User not found"}

                user_skills = set(getattr(user, "skills", []) or [])

                company_counts = (
                    self.db.query(Job.company, func.count(Job.id))
                    .filter(Job.date_added >= cutoff)
                    .group_by(Job.company)
                    .order_by(desc(func.count(Job.id)))
                    .limit(10)
                    .all()
                )

                location_counts = (
                    self.db.query(Job.location, func.count(Job.id))
                    .filter(Job.date_added >= cutoff)
                    .group_by(Job.location)
                    .order_by(desc(func.count(Job.id)))
                    .limit(10)
                    .all()
                )

                jobs = self.db.query(Job).filter(Job.date_added >= cutoff).all()

            skill_demand: Dict[str, int] = defaultdict(int)
            for job in jobs:
                tech_stack = getattr(job, "tech_stack", []) or []
                for skill in tech_stack:
                    if skill:
                        skill_demand[skill.lower()] += 1

            top_skills = sorted(skill_demand.items(), key=lambda x: x[1], reverse=True)[:15]
            user_skill_demand = {skill: skill_demand.get(skill.lower(), 0) for skill in user_skills}

            return {
                "user_id": user_id,
                "days": days,
                "market_overview": {
                    "total_jobs_posted": len(jobs),
                    "companies_hiring": len(set(job.company for job in jobs if job.company)),
                    "locations_with_jobs": len(set(job.location for job in jobs if job.location)),
                },
                "top_companies": [{"company": company, "job_count": count} for company, count in company_counts],
                "top_locations": [{"location": location, "job_count": count} for location, count in location_counts],
                "skill_demand": {
                    "top_skills": [{"skill": skill, "demand": count} for skill, count in top_skills],
                    "user_skills_demand": user_skill_demand,
                },
                "analysis_date": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to analyze market trends for user {user_id}: {e!s}")
            return {"user_id": user_id, "error": str(e)}

    def generate_user_insights(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Generate personalized insights for user (sync method).
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with user-specific insights and recommendations
        """
        try:
            if not self.db:
                return {"error": "Database connection required"}

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            if hasattr(self.db, 'query'):  # Sync session
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {"error": "User not found"}

                applications = (
                    self.db.query(Application)
                    .filter(and_(Application.user_id == user_id, Application.created_at >= cutoff))
                    .all()
                )

                interviews = (
                    self.db.query(InterviewSession)
                    .filter(and_(InterviewSession.user_id == user_id, InterviewSession.scheduled_at >= cutoff))
                    .all()
                )

            total_apps = len(applications)
            total_interviews = len(interviews)
            offers = sum(1 for app in applications if getattr(app, "status", "") == "offer")
            rejections = sum(1 for app in applications if getattr(app, "status", "") == "rejected")

            avg_apps_per_week = total_apps / (days / 7) if total_apps > 0 else 0

            insights = []

            if total_apps == 0:
                insights.append({
                    "type": "action",
                    "priority": "high",
                    "message": "No applications submitted. Start applying to recommended jobs!"
                })
            elif avg_apps_per_week < 2:
                insights.append({
                    "type": "action",
                    "priority": "medium",
                    "message": f"Your application rate is low ({avg_apps_per_week:.1f}/week). Consider increasing to 5-10/week for better results."
                })

            if total_apps > 0 and total_interviews == 0:
                insights.append({
                    "type": "improvement",
                    "priority": "high",
                    "message": "No interviews yet. Consider improving your resume and tailoring applications to job requirements."
                })

            interview_rate = (total_interviews / total_apps * 100) if total_apps > 0 else 0
            if interview_rate > 0:
                insights.append({
                    "type": "success",
                    "priority": "low",
                    "message": f"Great! You're getting interviews at a {interview_rate:.1f}% rate. Keep it up!"
                })

            if offers > 0:
                insights.append({
                    "type": "success",
                    "priority": "high",
                    "message": f"Congratulations on {offers} offer(s)! You're doing great."
                })

            return {
                "user_id": user_id,
                "period_days": days,
                "metrics": {
                    "applications": total_apps,
                    "interviews": total_interviews,
                    "offers": offers,
                    "rejections": rejections,
                    "interview_rate": round(interview_rate, 2),
                    "avg_apps_per_week": round(avg_apps_per_week, 2),
                },
                "insights": insights,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate insights for user {user_id}: {e!s}")
            return {"error": str(e)}

    def generate_weekly_summary(self, user_id: int) -> Dict[str, Any]:
        """Generate weekly summary report for user."""
        return self.generate_user_insights(user_id, days=7)

    # ========================================================================
    # SECTION 5: SPECIALIZED ANALYTICS (SUCCESS RATES, BENCHMARKS)
    # ========================================================================

    def calculate_detailed_success_rates(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Calculate detailed success rates for user applications.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with success rate analysis
        """
        try:
            analytics = self.get_user_analytics(user_id=user_id, days=days)
            
            total_apps = analytics.get("total_applications", 0)
            interviews = analytics.get("total_interviews", 0)
            offers = analytics.get("offers_received", 0)

            interview_rate = (interviews / total_apps * 100) if total_apps > 0 else 0
            offer_rate = (offers / total_apps * 100) if total_apps > 0 else 0

            return {
                "user_id": user_id,
                "period_days": days,
                "total_applications": total_apps,
                "total_interviews": interviews,
                "total_offers": offers,
                "interview_rate": round(interview_rate, 2),
                "offer_rate": round(offer_rate, 2),
                "success_rate": round(offer_rate, 2),
            }

        except Exception as e:
            logger.error(f"Failed to calculate success rates: {e!s}")
            return {"error": str(e), "user_id": user_id}

    def calculate_conversion_rates(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Calculate conversion funnel rates.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with conversion funnel analysis
        """
        try:
            funnel = self.process_user_funnel(user_id=user_id, days=days)

            return {
                "user_id": user_id,
                "period_days": days,
                "funnel": funnel,
                "overall_conversion": funnel.get("overall_conversion", 0),
            }

        except Exception as e:
            logger.error(f"Failed to calculate conversion rates: {e!s}")
            return {"error": str(e), "user_id": user_id}

    def generate_performance_benchmarks(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Generate performance benchmarks comparing user to averages.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with benchmark comparison
        """
        try:
            insights = self.generate_user_insights(user_id=user_id, days=days)
            trends = self.analyze_market_trends(user_id=user_id, days=days)

            metrics = insights.get("metrics", {})

            return {
                "user_id": user_id,
                "period_days": days,
                "user_metrics": metrics,
                "market_overview": trends.get("market_overview", {}),
                "insights": insights.get("insights", []),
                "performance_summary": {
                    "applications": metrics.get("applications", 0),
                    "interviews": metrics.get("interviews", 0),
                    "offers": metrics.get("offers", 0),
                    "interview_rate": metrics.get("interview_rate", 0),
                },
            }

        except Exception as e:
            logger.error(f"Failed to generate benchmarks: {e!s}")
            return {"error": str(e), "user_id": user_id}

    def track_slack_event(self, event: SlackEvent) -> bool:
        """
        Track Slack integration event.
        
        Args:
            event: Slack event to track
            
        Returns:
            Success status
        """
        try:
            logger.info(f"Slack event tracked: {event.event_type} from user {event.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to track Slack event: {e!s}")
            return False

    # ========================================================================
    # SECTION 6: JOB-SPECIFIC ANALYTICS
    # ========================================================================

    async def get_summary_metrics(self, user: User) -> Dict[str, Any]:
        """
        Get summary metrics for a user's job search activity (async).
        
        Args:
            user: User object
            
        Returns:
            Dict with summary metrics
        """
        total_jobs_result = await self.db.execute(
            select(func.count()).select_from(Job).where(Job.user_id == user.id)
        )
        total_jobs = total_jobs_result.scalar() or 0
        
        total_apps_result = await self.db.execute(
            select(func.count()).select_from(Application).where(Application.user_id == user.id)
        )
        total_applications = total_apps_result.scalar() or 0
        
        pending_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.status == 'pending')
        )
        pending = pending_result.scalar() or 0
        
        interviews_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.status == 'interview')
        )
        interviews = interviews_result.scalar() or 0
        
        offers_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.status == 'offer')
        )
        offers = offers_result.scalar() or 0
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_apps_result = await self.db.execute(
            select(func.count()).select_from(Application)
            .where(Application.user_id == user.id, Application.created_at >= week_ago)
        )
        recent_applications = recent_apps_result.scalar() or 0
        
        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "pending_applications": pending,
            "interviews_scheduled": interviews,
            "offers_received": offers,
            "recent_applications": recent_applications,
            "last_updated": datetime.utcnow().isoformat()
        }

    # ========================================================================
    # SECTION 7: CACHE MANAGEMENT
    # ========================================================================

    def invalidate_user_cache(self, user_id: int) -> int:
        """
        Invalidate all cached analytics for a user.
        Should be called when user data changes.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of cache entries cleared
        """
        if self.cache:
            count = self.cache.clear_user_cache(user_id)
            logger.info(f"Invalidated {count} cache entries for user {user_id}")
            return count
        return 0

    # ========================================================================
    # SECTION 8: HEALTH CHECKS
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on analytics service.
        
        Returns:
            Dict with health status
        """
        try:
            if not self.db:
                return {"status": "degraded", "message": "No database connection"}

            # Test database connectivity
            user_count_result = await self.db.execute(select(func.count()).select_from(User))
            user_count = user_count_result.scalar()

            return {
                "status": "healthy",
                "total_users": user_count,
                "cache_enabled": self.use_cache,
                "circuit_breaker_status": "open" if self._circuit_open else "closed"
            }

        except Exception as e:
            logger.error(f"Health check failed: {e!s}")
            return {"status": "unhealthy", "error": str(e)}
