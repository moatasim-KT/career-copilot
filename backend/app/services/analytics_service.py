"""
Consolidated Analytics Service for Career Copilot.

This service will integrate functionalities from various analytics-related services
to provide a single, unified interface for all analytics operations,
including collection, processing, querying, and reporting.
"""

import json
import logging
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone, date
from enum import Enum
from typing import Any, Deque, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import and_, desc, func, select, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analytics import Analytics # Assuming Analytics model exists for event storage
from ..models.application import Application
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

class AnalyticsService:
    """
    The ultimate consolidated analytics service.
    Integrates functionalities from ComprehensiveAnalyticsService and AnalyticsCollectionService.
    """
    def __init__(self, db: AsyncSession, use_cache: bool = True):
        self.db = db
        self.use_cache = use_cache
        self.cache = get_analytics_cache() if use_cache else None
        self._cache_ttl = timedelta(minutes=5)
        logger.info("New Consolidated AnalyticsService initialized with ComprehensiveAnalyticsService features")

        # From AnalyticsCollectionService
        self._event_queue: Deque[Dict[str, Any]] = deque(maxlen=10000)
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self._batch_size = 100
        self._flush_interval = timedelta(seconds=30)
        self._last_flush = datetime.now(timezone.utc)
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_open = False
        logger.info("AnalyticsCollectionService features integrated")

    # --- Methods from ComprehensiveAnalyticsService ---
    async def get_application_counts_by_status(self, user_id: int) -> List[ApplicationStatusCount]:
        """Get application counts grouped by status"""
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
        """Calculate interview rate, offer rate, and acceptance rate"""
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
        """Calculate trend analysis for a specific time period"""
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
        """Calculate application trends for daily, weekly, and monthly periods"""
        today = datetime.now(timezone.utc).date()
        
        # Daily trend (today vs yesterday)
        daily_trend = await self.calculate_trend_for_period(
            user_id=user_id,
            current_start=today,
            current_end=today,
            previous_start=today - timedelta(days=1),
            previous_end=today - timedelta(days=1)
        )
        
        # Weekly trend (this week vs last week)
        week_start = today - timedelta(days=today.weekday())
        last_week_start = week_start - timedelta(days=7)
        weekly_trend = await self.calculate_trend_for_period(
            user_id=user_id,
            current_start=week_start,
            current_end=today,
            previous_start=last_week_start,
            previous_end=week_start - timedelta(days=1)
        )
        
        # Monthly trend (this month vs last month)
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
        """Identify top skills from jobs the user has applied to or is interested in"""
        # Get all jobs for the user
        result = await self.db.execute(
            select(Job.tech_stack)
            .where(Job.user_id == user_id)
        )
        
        # Collect all skills
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
        
        # Count skill occurrences
        skill_counts = Counter(all_skills)
        
        # Create SkillData objects
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
        """Identify top companies the user has applied to"""
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
        """Get comprehensive analytics summary with all metrics (cached)"""
        # Check cache first
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
        
        # Get status breakdown
        status_counts = await self.get_application_counts_by_status(user_id)
        
        # Calculate rate metrics
        rates = await self.calculate_rate_metrics(user_id)
        
        # Calculate trends
        trends = await self.calculate_application_trends(user_id)
        
        # Get top skills and companies
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
        
        # Get user's daily goal
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
        
        # Cache the result
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
        """Get time series data for applications over a date range"""
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
        """Analyze skill gaps between user skills and market demand (cached)"""
        # Check cache first
        if self.cache:
            cache_key = self.cache._make_key("skill_gap", user_id)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for skill gap analysis: {cache_key}")
                return SkillGapAnalysis(**cached)
        
        # Get user's skills from their profile
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
        
        # Get market skills (from all jobs in the system)
        market_skills = await self.get_top_skills_in_jobs(user_id, limit=50)
        
        # Normalize user skills for comparison
        user_skills_normalized = set(skill.lower().strip() for skill in user_skills)
        
        # Identify missing skills
        missing_skills = []
        for skill_data in market_skills:
            if skill_data.skill.lower() not in user_skills_normalized:
                missing_skills.append(skill_data)
        
        # Calculate skill coverage
        if market_skills:
            skills_covered = len([s for s in market_skills if s.skill.lower() in user_skills_normalized])
            coverage_percentage = (skills_covered / len(market_skills)) * 100
        else:
            coverage_percentage = 0.0
        
        # Generate recommendations (top 5 missing skills)
        recommendations = [
            f"Consider learning {skill.skill} (appears in {skill.percentage}% of jobs)"
            for skill in missing_skills[:5]
        ]
        
        analysis = SkillGapAnalysis(
            user_skills=list(user_skills),
            market_skills=market_skills[:20],  # Top 20 market skills
            missing_skills=missing_skills[:10],  # Top 10 missing skills
            skill_coverage_percentage=round(coverage_percentage, 2),
            recommendations=recommendations
        )
        
        # Cache the result
        if self.cache:
            cache_key = self.cache._make_key("skill_gap", user_id)
            self.cache.set(cache_key, analysis.model_dump(), ttl=self._cache_ttl)
            logger.debug(f"Cached skill gap analysis: {cache_key}")
        
        return analysis
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """
        Invalidate all cached analytics for a user.
        Should be called when user data changes (new application, job, etc.)
        
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
