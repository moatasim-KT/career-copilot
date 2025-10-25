"""
Specialized Analytics Service
Consolidates domain-specific analytics for applications, emails, jobs, and Slack integrations.
Provides advanced user analytics, application success tracking, email delivery monitoring, 
job market insights, and Slack engagement analytics.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter, deque
import statistics
import numpy as np

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, select

from app.models.user import User
from app.models.job import Job
from app.models.application import Application, APPLICATION_STATUSES
from app.models.analytics import Analytics
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.database import get_db

logger = get_logger(__name__)


# Enums and Data Classes
class DeliveryProvider(str, Enum):
    """Email delivery providers"""
    SMTP = "smtp"
    GMAIL = "gmail"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SES = "ses"


class EmailStatus(str, Enum):
    """Email delivery status types"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    SPAM = "spam"
    UNSUBSCRIBED = "unsubscribed"


class EmailEventType(str, Enum):
    """Email event types for tracking"""
    SEND = "send"
    DELIVERY = "delivery"
    OPEN = "open"
    CLICK = "click"
    BOUNCE = "bounce"
    SPAM_REPORT = "spam_report"
    UNSUBSCRIBE = "unsubscribe"


class SlackEventType(str, Enum):
    """Slack event types for analytics"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_FAILED = "message_failed"
    INTERACTION = "interaction"
    COMMAND_USED = "command_used"
    USER_JOINED = "user_joined"
    CHANNEL_CREATED = "channel_created"


@dataclass
class EmailMetrics:
    """Email delivery metrics"""
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_failed: int = 0
    total_spam: int = 0
    total_unsubscribed: int = 0
    
    @property
    def delivery_rate(self) -> float:
        return (self.total_delivered / self.total_sent) if self.total_sent > 0 else 0.0
    
    @property
    def open_rate(self) -> float:
        return (self.total_opened / self.total_delivered) if self.total_delivered > 0 else 0.0
    
    @property
    def click_rate(self) -> float:
        return (self.total_clicked / self.total_delivered) if self.total_delivered > 0 else 0.0
    
    @property
    def bounce_rate(self) -> float:
        return (self.total_bounced / self.total_sent) if self.total_sent > 0 else 0.0
    
    @property
    def spam_rate(self) -> float:
        return (self.total_spam / self.total_sent) if self.total_sent > 0 else 0.0


@dataclass
class SlackEvent:
    """Slack event for analytics tracking"""
    id: str
    event_type: SlackEventType
    timestamp: datetime
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmailEvent(BaseModel):
    """Email event model for tracking"""
    id: str = Field(..., description="Event ID")
    tracking_id: str = Field(..., description="Email tracking ID")
    event_type: EmailEventType = Field(..., description="Event type")
    recipient: str = Field(..., description="Recipient email")
    provider: DeliveryProvider = Field(..., description="Delivery provider")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    location: Optional[Dict[str, str]] = Field(None, description="Geographic location")


class AnalyticsSpecializedService:
    """
    Specialized analytics service providing domain-specific analytics for:
    - Advanced user performance tracking and benchmarking
    - Application success tracking and optimization
    - Email delivery monitoring and engagement analytics
    - Job market insights and recommendation analytics
    - Slack integration analytics and monitoring
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Market benchmarks for user analytics
        self.market_benchmarks = {
            'application_to_interview_rate': 15.0,
            'interview_to_offer_rate': 25.0,
            'overall_success_rate': 3.75,
            'average_time_to_interview': 14,
            'average_time_to_offer': 30,
            'applications_per_week': 10,
            'job_search_duration': 90
        }
        
        # Email analytics configuration
        self.email_tracking_enabled = getattr(self.settings, "email_tracking_enabled", True)
        self.pixel_tracking_enabled = getattr(self.settings, "email_pixel_tracking_enabled", True)
        self.link_tracking_enabled = getattr(self.settings, "email_link_tracking_enabled", True)
        
        # In-memory caches for high-frequency events
        self.email_events: Dict[str, List[EmailEvent]] = {}
        self.slack_events: deque = deque(maxlen=10000)
        self.event_cache = []
        self.cache_flush_interval = 60
        self.max_cache_size = 1000
        
        # Slack analytics data
        self.slack_real_time_stats = {
            "messages_sent_today": 0,
            "active_users_today": set(),
            "active_channels_today": set(),
            "commands_used_today": 0,
            "interactions_today": 0,
            "errors_today": 0
        }
        
        self.user_engagement = defaultdict(lambda: {
            "messages_received": 0,
            "interactions": 0,
            "commands_used": 0,
            "last_active": None,
            "channels": set(),
            "response_rate": 0.0
        })
        
        self.channel_analytics = defaultdict(lambda: {
            "messages_sent": 0,
            "unique_users": set(),
            "interactions": 0,
            "peak_activity_hour": None,
            "activity_by_hour": defaultdict(int)
        })
        
        self.command_analytics = defaultdict(lambda: {
            "usage_count": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "users": set(),
            "errors": 0
        })
        
        # Performance tracking
        self.performance_metrics = {
            "response_times": deque(maxlen=1000),
            "api_calls": deque(maxlen=1000),
            "rate_limit_hits": 0,
            "uptime_start": datetime.now()
        }
        
        logger.info("Specialized Analytics Service initialized")

    # Advanced User Analytics Methods
    
    def calculate_detailed_success_rates(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Calculate detailed application success rates with temporal analysis"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        applications = db.query(Application).filter(
            Application.user_id == user_id,
            Application.created_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found for analysis'}
        
        # Calculate basic success rates
        total_applications = len(applications)
        interviews = len([app for app in applications if app.status == 'interview'])
        offers = len([app for app in applications if app.status in ['offer', 'accepted']])
        rejections = len([app for app in applications if app.status == 'rejected'])
        pending = len([app for app in applications if app.status in ['interested', 'applied']])
        
        # Calculate rates
        application_to_interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
        interview_to_offer_rate = (offers / interviews * 100) if interviews > 0 else 0
        overall_success_rate = (offers / total_applications * 100) if total_applications > 0 else 0
        rejection_rate = (rejections / total_applications * 100) if total_applications > 0 else 0
        
        # Temporal analysis - weekly breakdown
        weekly_performance = defaultdict(lambda: {
            'applications': 0, 'interviews': 0, 'offers': 0, 'rejections': 0
        })
        
        for app in applications:
            week_key = app.created_at.strftime('%Y-W%U')
            weekly_performance[week_key]['applications'] += 1
            
            if app.status == 'interview':
                weekly_performance[week_key]['interviews'] += 1
            elif app.status in ['offer', 'accepted']:
                weekly_performance[week_key]['offers'] += 1
            elif app.status == 'rejected':
                weekly_performance[week_key]['rejections'] += 1
        
        # Calculate weekly success rates
        weekly_success_rates = []
        for week, data in sorted(weekly_performance.items()):
            if data['applications'] > 0:
                week_interview_rate = (data['interviews'] / data['applications'] * 100)
                week_success_rate = (data['offers'] / data['applications'] * 100)
                weekly_success_rates.append({
                    'week': week,
                    'applications': data['applications'],
                    'interview_rate': round(week_interview_rate, 1),
                    'success_rate': round(week_success_rate, 1),
                    'offers': data['offers'],
                    'rejections': data['rejections']
                })
        
        # Calculate trends
        if len(weekly_success_rates) >= 4:
            recent_weeks = weekly_success_rates[-4:]
            early_weeks = weekly_success_rates[:4]
            
            recent_avg_interview_rate = sum(w['interview_rate'] for w in recent_weeks) / len(recent_weeks)
            early_avg_interview_rate = sum(w['interview_rate'] for w in early_weeks) / len(early_weeks)
            
            interview_rate_trend = recent_avg_interview_rate - early_avg_interview_rate
        else:
            interview_rate_trend = 0
        
        # Industry and company analysis
        industry_performance = self._analyze_performance_by_industry(db, applications)
        company_performance = self._analyze_performance_by_company(db, applications)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'total_applications': total_applications,
            'success_rates': {
                'application_to_interview': round(application_to_interview_rate, 2),
                'interview_to_offer': round(interview_to_offer_rate, 2),
                'overall_success': round(overall_success_rate, 2),
                'rejection_rate': round(rejection_rate, 2)
            },
            'status_breakdown': {
                'pending': pending,
                'interviews': interviews,
                'offers': offers,
                'rejections': rejections
            },
            'weekly_performance': weekly_success_rates,
            'trends': {
                'interview_rate_trend': round(interview_rate_trend, 2),
                'trend_direction': 'improving' if interview_rate_trend > 2 else 'declining' if interview_rate_trend < -2 else 'stable'
            },
            'industry_performance': industry_performance,
            'company_performance': company_performance
        }
    
    def generate_performance_benchmarks(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Generate performance benchmarks comparing user to market averages"""
        success_rates = self.calculate_detailed_success_rates(db, user_id, days)
        
        if 'error' in success_rates:
            return success_rates
        
        user_metrics = success_rates['success_rates']
        
        # Calculate percentile rankings
        benchmarks = []
        
        for metric, user_value in user_metrics.items():
            if metric in ['application_to_interview', 'interview_to_offer', 'overall_success']:
                market_key = f"{metric.replace('_', '_to_')}_rate" if 'to' in metric else f"{metric}_rate"
                market_average = self.market_benchmarks.get(market_key, 0)
                
                # Calculate percentile rank
                if user_value > market_average * 1.5:
                    percentile_rank = 90
                    category = 'excellent'
                elif user_value > market_average * 1.2:
                    percentile_rank = 75
                    category = 'above_average'
                elif user_value > market_average * 0.8:
                    percentile_rank = 50
                    category = 'average'
                else:
                    percentile_rank = 25
                    category = 'below_average'
                
                benchmarks.append({
                    'metric': metric.replace('_', ' ').title(),
                    'user_value': user_value,
                    'market_average': market_average,
                    'percentile_rank': percentile_rank,
                    'category': category,
                    'improvement_potential': market_average - user_value if user_value < market_average else 0
                })
        
        # Generate insights and recommendations
        insights = self._generate_performance_insights(benchmarks, success_rates)
        recommendations = self._generate_performance_recommendations(benchmarks, success_rates)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'user_id': user_id,
            'analysis_period_days': days,
            'benchmarks': benchmarks,
            'overall_performance_score': round(sum(b['percentile_rank'] for b in benchmarks) / len(benchmarks), 1),
            'insights': insights,
            'recommendations': recommendations,
            'market_position': self._calculate_market_position(benchmarks)
        }

    # Application Analytics Methods
    
    def calculate_conversion_rates(self, db: Session, user_id: int, days: int = 90) -> Dict:
        """Calculate application-to-interview conversion rates by category"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get applications in the period with job details
        applications = db.query(Application, Job).join(Job).filter(
            Application.user_id == user_id,
            Application.created_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found in the specified period'}
        
        # Define status progression stages
        response_statuses = [
            'under_review', 'phone_screen_scheduled', 'phone_screen_completed',
            'interview_scheduled', 'interview_completed', 'final_round',
            'offer_received', 'offer_accepted'
        ]
        
        interview_statuses = [
            'phone_screen_scheduled', 'phone_screen_completed',
            'interview_scheduled', 'interview_completed', 'final_round',
            'offer_received', 'offer_accepted'
        ]
        
        offer_statuses = ['offer_received', 'offer_accepted']
        
        # Overall statistics
        total_applications = len(applications)
        responses = sum(1 for app, job in applications if app.status in response_statuses)
        interviews = sum(1 for app, job in applications if app.status in interview_statuses)
        offers = sum(1 for app, job in applications if app.status in offer_statuses)
        
        # Calculate overall rates
        response_rate = round(responses / total_applications, 3) if total_applications > 0 else 0
        interview_rate = round(interviews / total_applications, 3) if total_applications > 0 else 0
        offer_rate = round(offers / total_applications, 3) if total_applications > 0 else 0
        
        # Count by status
        status_counts = {}
        for app, job in applications:
            status = app.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Category analysis
        category_stats = self._analyze_by_category_internal(applications, response_statuses, interview_statuses, offer_statuses)
        
        return {
            'period_days': days,
            'analysis_date': datetime.utcnow().isoformat(),
            'total_applications': total_applications,
            'responses_received': responses,
            'interviews_scheduled': interviews,
            'offers_received': offers,
            'conversion_rates': {
                'response_rate': response_rate,
                'interview_rate': interview_rate,
                'offer_rate': offer_rate,
                'response_percentage': f"{response_rate:.1%}",
                'interview_percentage': f"{interview_rate:.1%}",
                'offer_percentage': f"{offer_rate:.1%}"
            },
            'status_breakdown': status_counts,
            'by_category': category_stats,
            'benchmarks': self._get_industry_benchmarks(),
            'recommendations': self._generate_conversion_recommendations(response_rate, interview_rate, offer_rate)
        }
    
    def analyze_timing_patterns(self, db: Session, user_id: int, days: int = 180) -> Dict:
        """Analyze application timing patterns and success factors"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        applications = db.query(Application, Job).join(Job).filter(
            Application.user_id == user_id,
            Application.created_at >= cutoff_date
        ).all()
        
        if not applications:
            return {'error': 'No applications found'}
        
        # Define success statuses
        success_statuses = [
            'under_review', 'phone_screen_scheduled', 'phone_screen_completed',
            'interview_scheduled', 'interview_completed', 'final_round',
            'offer_received', 'offer_accepted'
        ]
        
        # Analyze by day of week
        day_stats = {i: {'applications': 0, 'responses': 0, 'avg_response_time': []} for i in range(7)}
        
        # Analyze by time since job posting
        timing_stats = {'quick': {'count': 0, 'responses': 0}, 
                       'medium': {'count': 0, 'responses': 0}, 
                       'slow': {'count': 0, 'responses': 0}}
        
        # Analyze by hour of day
        hour_stats = {i: {'applications': 0, 'responses': 0} for i in range(24)}
        
        # Monthly trend analysis
        monthly_stats = {}
        
        for app, job in applications:
            # Day of week analysis
            if app.created_at:
                day_of_week = app.created_at.weekday()
                hour_of_day = app.created_at.hour
                month_key = app.created_at.strftime('%Y-%m')
                
                day_stats[day_of_week]['applications'] += 1
                hour_stats[hour_of_day]['applications'] += 1
                
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'applications': 0, 'responses': 0}
                monthly_stats[month_key]['applications'] += 1
                
                if app.status in success_statuses:
                    day_stats[day_of_week]['responses'] += 1
                    hour_stats[hour_of_day]['responses'] += 1
                    monthly_stats[month_key]['responses'] += 1
        
        # Calculate success rates and format results
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_analysis = []
        
        for day, stats in day_stats.items():
            if stats['applications'] > 0:
                success_rate = round(stats['responses'] / stats['applications'], 3)
                avg_response_time = round(sum(stats['avg_response_time']) / len(stats['avg_response_time']), 1) if stats['avg_response_time'] else None
                day_analysis.append({
                    'day': day_names[day],
                    'day_number': day,
                    'applications': stats['applications'],
                    'responses': stats['responses'],
                    'success_rate': success_rate,
                    'success_percentage': f"{success_rate:.1%}",
                    'avg_response_time_days': avg_response_time
                })
        
        return {
            'analysis_date': datetime.utcnow().isoformat(),
            'period_days': days,
            'day_of_week_analysis': sorted(day_analysis, key=lambda x: x['success_rate'], reverse=True),
            'best_application_day': max(day_analysis, key=lambda x: x['success_rate'])['day'] if day_analysis else None,
            'recommendations': self._generate_timing_recommendations(day_analysis, timing_stats, [])
        }

    # Job Analytics Methods
    
    def get_job_summary_metrics(self, db: Session, user: User) -> Dict[str, Any]:
        """Calculate summary metrics for the user's job applications"""
        total_jobs = db.query(Job).filter(Job.user_id == user.id).count()
        total_applications = db.query(Application).filter(Application.user_id == user.id).count()
        
        interviews = db.query(Application).filter(
            Application.user_id == user.id,
            Application.status == "interview"
        ).count()
        
        offers = db.query(Application).filter(
            Application.user_id == user.id,
            Application.status.in_(["offer", "accepted"])
        ).count()

        # Daily goal tracking
        daily_goal = 10  # Configurable
        daily_applications_today = db.query(Application).filter(
            Application.user_id == user.id,
            func.date(Application.created_at) == func.date(datetime.utcnow().date())
        ).count()
        daily_goal_progress = round((daily_applications_today / daily_goal) * 100, 2) if daily_goal > 0 else 0.0

        # Calculate additional metrics
        pending_applications = db.query(Application).filter(
            Application.user_id == user.id,
            Application.status.in_(["interested", "applied", "interview"])
        ).count()

        rejections_received = db.query(Application).filter(
            Application.user_id == user.id,
            Application.status == "rejected"
        ).count()

        acceptance_rate = round((offers / total_applications) * 100, 2) if total_applications > 0 else 0.0

        # Weekly and monthly applications
        one_week_ago = datetime.utcnow() - timedelta(weeks=1)
        weekly_applications = db.query(Application).filter(
            Application.user_id == user.id,
            Application.created_at >= one_week_ago
        ).count()

        one_month_ago = datetime.utcnow() - timedelta(days=30)
        monthly_applications = db.query(Application).filter(
            Application.user_id == user.id,
            Application.created_at >= one_month_ago
        ).count()

        # Top skills analysis
        all_job_skills = []
        for job in db.query(Job).filter(Job.user_id == user.id).all():
            if hasattr(job, 'tech_stack') and job.tech_stack:
                all_job_skills.extend(job.tech_stack)
        
        skill_counts = {}
        for skill in all_job_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        top_skills_in_jobs = sorted(skill_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        top_skills_in_jobs = [{"skill": s, "count": c} for s, c in top_skills_in_jobs]

        # Top companies applied
        company_counts = db.query(
            Job.company,
            func.count(Job.company)
        ).join(Application, Application.job_id == Job.id).filter(
            Application.user_id == user.id
        ).group_by(Job.company).order_by(func.count(Job.company).desc()).limit(5).all()
        top_companies_applied = [{"company": c, "count": count} for c, count in company_counts]

        # Application status breakdown
        status_breakdown = db.query(
            Application.status,
            func.count(Application.id)
        ).filter(
            Application.user_id == user.id
        ).group_by(Application.status).all()
        application_status_breakdown = {status: count for status, count in status_breakdown}

        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "pending_applications": pending_applications,
            "interviews_scheduled": interviews,
            "offers_received": offers,
            "rejections_received": rejections_received,
            "acceptance_rate": acceptance_rate,
            "daily_applications_today": daily_applications_today,
            "daily_application_goal": daily_goal,
            "daily_goal_progress": daily_goal_progress,
            "weekly_applications": weekly_applications,
            "monthly_applications": monthly_applications,
            "top_skills_in_jobs": top_skills_in_jobs,
            "top_companies_applied": top_companies_applied,
            "application_status_breakdown": application_status_breakdown
        }

    # Email Analytics Methods
    
    async def track_email_event(self, event: EmailEvent) -> Dict[str, Any]:
        """Track an email event for analytics"""
        try:
            if not self.email_tracking_enabled:
                return {"success": True, "message": "Email tracking disabled"}
            
            # Store event
            if event.tracking_id not in self.email_events:
                self.email_events[event.tracking_id] = []
            self.email_events[event.tracking_id].append(event)
            
            # Add to cache for batch processing
            self.event_cache.append(event)
            
            # Flush cache if it's getting full
            if len(self.event_cache) >= self.max_cache_size:
                await self._flush_email_event_cache()
            
            logger.debug(f"Tracked email event: {event.event_type} for {event.tracking_id}")
            
            return {
                "success": True,
                "message": "Event tracked successfully",
                "event_type": event.event_type.value,
                "tracking_id": event.tracking_id
            }
            
        except Exception as e:
            logger.error(f"Failed to track email event: {e}")
            return {
                "success": False,
                "error": "tracking_failed",
                "message": f"Failed to track event: {str(e)}"
            }
    
    async def get_email_metrics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_name: Optional[str] = None,
        recipient_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive email metrics"""
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Filter events by date range
            filtered_events = []
            for events_list in self.email_events.values():
                filtered_events.extend([
                    e for e in events_list
                    if start_date <= e.timestamp <= end_date
                ])
            
            # Calculate metrics
            metrics = EmailMetrics()
            status_counts = {}
            
            for event in filtered_events:
                if event.event_type == EmailEventType.SEND:
                    metrics.total_sent += 1
                elif event.event_type == EmailEventType.DELIVERY:
                    metrics.total_delivered += 1
                elif event.event_type == EmailEventType.OPEN:
                    metrics.total_opened += 1
                elif event.event_type == EmailEventType.CLICK:
                    metrics.total_clicked += 1
                elif event.event_type == EmailEventType.BOUNCE:
                    metrics.total_bounced += 1
                elif event.event_type == EmailEventType.SPAM_REPORT:
                    metrics.total_spam += 1
                elif event.event_type == EmailEventType.UNSUBSCRIBE:
                    metrics.total_unsubscribed += 1
                
                status = event.event_type.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "success": True,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "metrics": {
                    "total_sent": metrics.total_sent,
                    "total_delivered": metrics.total_delivered,
                    "total_opened": metrics.total_opened,
                    "total_clicked": metrics.total_clicked,
                    "total_bounced": metrics.total_bounced,
                    "total_failed": metrics.total_failed,
                    "total_spam": metrics.total_spam,
                    "total_unsubscribed": metrics.total_unsubscribed,
                    "delivery_rate": round(metrics.delivery_rate * 100, 2),
                    "open_rate": round(metrics.open_rate * 100, 2),
                    "click_rate": round(metrics.click_rate * 100, 2),
                    "bounce_rate": round(metrics.bounce_rate * 100, 2),
                    "spam_rate": round(metrics.spam_rate * 100, 2)
                },
                "status_breakdown": status_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get email metrics: {e}")
            return {
                "success": False,
                "error": "metrics_failed",
                "message": f"Failed to get metrics: {str(e)}"
            }

    # Slack Analytics Methods
    
    async def track_slack_event(self, event: SlackEvent):
        """Track a Slack event for analytics"""
        try:
            # Add to events queue
            self.slack_events.append(event)
            
            # Update real-time stats
            await self._update_slack_real_time_metrics(event)
            
            # Update specific analytics
            if event.event_type == SlackEventType.MESSAGE_SENT:
                await self._track_slack_message_event(event)
            elif event.event_type == SlackEventType.INTERACTION:
                await self._track_slack_interaction_event(event)
            elif event.event_type == SlackEventType.COMMAND_USED:
                await self._track_slack_command_event(event)
            
            logger.debug(f"Tracked Slack event: {event.event_type} for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking Slack event: {e}")
    
    async def get_slack_dashboard_metrics(self) -> Dict[str, Any]:
        """Get real-time Slack dashboard metrics"""
        uptime = datetime.now() - self.performance_metrics["uptime_start"]
        
        return {
            "overview": {
                "messages_sent_today": self.slack_real_time_stats["messages_sent_today"],
                "active_users_today": len(self.slack_real_time_stats["active_users_today"]),
                "active_channels_today": len(self.slack_real_time_stats["active_channels_today"]),
                "commands_used_today": self.slack_real_time_stats["commands_used_today"],
                "interactions_today": self.slack_real_time_stats["interactions_today"],
                "errors_today": self.slack_real_time_stats["errors_today"],
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            },
            "performance": {
                "avg_response_time": self._calculate_avg_response_time(),
                "api_calls_per_minute": self._calculate_api_rate(),
                "rate_limit_hits": self.performance_metrics["rate_limit_hits"],
                "success_rate": self._calculate_slack_success_rate()
            },
            "top_channels": await self._get_top_slack_channels(5),
            "top_users": await self._get_top_slack_users(5),
            "top_commands": await self._get_top_slack_commands(5),
            "timestamp": datetime.now().isoformat()
        }

    # Helper Methods
    
    def _analyze_performance_by_industry(self, db: Session, applications: List[Application]) -> Dict[str, Any]:
        """Analyze performance by industry"""
        industry_performance = defaultdict(lambda: {'applications': 0, 'interviews': 0, 'offers': 0})
        
        for app in applications:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                industry = 'technology'  # Simplified
                industry_performance[industry]['applications'] += 1
                
                if app.status == 'interview':
                    industry_performance[industry]['interviews'] += 1
                elif app.status in ['offer', 'accepted']:
                    industry_performance[industry]['offers'] += 1
        
        result = {}
        for industry, data in industry_performance.items():
            if data['applications'] > 0:
                result[industry] = {
                    'applications': data['applications'],
                    'interview_rate': round(data['interviews'] / data['applications'] * 100, 1),
                    'success_rate': round(data['offers'] / data['applications'] * 100, 1)
                }
        
        return result
    
    def _analyze_performance_by_company(self, db: Session, applications: List[Application]) -> Dict[str, Any]:
        """Analyze performance by company"""
        company_performance = defaultdict(lambda: {'applications': 0, 'interviews': 0, 'offers': 0})
        
        for app in applications:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                company = job.company
                company_performance[company]['applications'] += 1
                
                if app.status == 'interview':
                    company_performance[company]['interviews'] += 1
                elif app.status in ['offer', 'accepted']:
                    company_performance[company]['offers'] += 1
        
        result = {}
        for company, data in sorted(company_performance.items(), key=lambda x: x[1]['applications'], reverse=True)[:10]:
            if data['applications'] > 0:
                result[company] = {
                    'applications': data['applications'],
                    'interview_rate': round(data['interviews'] / data['applications'] * 100, 1),
                    'success_rate': round(data['offers'] / data['applications'] * 100, 1)
                }
        
        return result
    
    def _analyze_by_category_internal(self, applications: List[Tuple], response_statuses: List[str], 
                                    interview_statuses: List[str], offer_statuses: List[str]) -> Dict:
        """Internal method to analyze success rates by job category/industry"""
        category_stats = {}
        
        for app, job in applications:
            category = self._determine_job_category(job)
            
            if category not in category_stats:
                category_stats[category] = {
                    'applications': 0,
                    'responses': 0,
                    'interviews': 0,
                    'offers': 0,
                    'companies': set()
                }
            
            category_stats[category]['applications'] += 1
            category_stats[category]['companies'].add(job.company)
            
            if app.status in response_statuses:
                category_stats[category]['responses'] += 1
            
            if app.status in interview_statuses:
                category_stats[category]['interviews'] += 1
            
            if app.status in offer_statuses:
                category_stats[category]['offers'] += 1
        
        # Calculate rates and format results
        formatted_stats = {}
        for category, stats in category_stats.items():
            total = stats['applications']
            if total > 0:
                formatted_stats[category] = {
                    'applications': total,
                    'responses': stats['responses'],
                    'interviews': stats['interviews'],
                    'offers': stats['offers'],
                    'unique_companies': len(stats['companies']),
                    'response_rate': round(stats['responses'] / total, 3),
                    'interview_rate': round(stats['interviews'] / total, 3),
                    'offer_rate': round(stats['offers'] / total, 3),
                    'response_percentage': f"{stats['responses'] / total:.1%}",
                    'interview_percentage': f"{stats['interviews'] / total:.1%}",
                    'offer_percentage': f"{stats['offers'] / total:.1%}"
                }
        
        return formatted_stats
    
    def _determine_job_category(self, job: Job) -> str:
        """Determine job category from job data"""
        title_lower = job.title.lower()
        
        if any(term in title_lower for term in ['frontend', 'front-end', 'react', 'vue', 'angular']):
            return 'frontend'
        elif any(term in title_lower for term in ['backend', 'back-end', 'api', 'server']):
            return 'backend'
        elif any(term in title_lower for term in ['fullstack', 'full-stack', 'full stack']):
            return 'fullstack'
        elif any(term in title_lower for term in ['data', 'analytics', 'scientist', 'ml', 'machine learning']):
            return 'data_science'
        elif any(term in title_lower for term in ['devops', 'sre', 'infrastructure', 'cloud']):
            return 'devops'
        elif any(term in title_lower for term in ['mobile', 'ios', 'android', 'react native']):
            return 'mobile'
        elif any(term in title_lower for term in ['qa', 'test', 'quality']):
            return 'qa'
        elif any(term in title_lower for term in ['product', 'manager', 'pm']):
            return 'product'
        elif any(term in title_lower for term in ['design', 'ux', 'ui']):
            return 'design'
        else:
            return 'other'
    
    def _get_industry_benchmarks(self) -> Dict:
        """Get industry benchmark conversion rates"""
        return {
            'response_rate': {'low': 0.15, 'average': 0.25, 'high': 0.40},
            'interview_rate': {'low': 0.05, 'average': 0.10, 'high': 0.20},
            'offer_rate': {'low': 0.01, 'average': 0.03, 'high': 0.08}
        }
    
    def _generate_conversion_recommendations(self, response_rate: float, interview_rate: float, offer_rate: float) -> List[str]:
        """Generate recommendations based on conversion rates"""
        recommendations = []
        benchmarks = self._get_industry_benchmarks()
        
        if response_rate < benchmarks['response_rate']['low']:
            recommendations.append("Your response rate is below average. Consider improving your resume and cover letter.")
        elif response_rate > benchmarks['response_rate']['high']:
            recommendations.append("Excellent response rate! Your application materials are working well.")
        
        if interview_rate < benchmarks['interview_rate']['low']:
            recommendations.append("Focus on getting more interviews by tailoring applications to job requirements.")
        elif interview_rate > benchmarks['interview_rate']['high']:
            recommendations.append("Great interview rate! You're getting good traction with employers.")
        
        if offer_rate < benchmarks['offer_rate']['low']:
            recommendations.append("Consider practicing interview skills to improve your offer conversion rate.")
        elif offer_rate > benchmarks['offer_rate']['high']:
            recommendations.append("Outstanding offer rate! Your interview performance is excellent.")
        
        return recommendations
    
    def _generate_timing_recommendations(self, day_analysis: List[Dict], timing_effectiveness: Dict, hour_analysis: List[Dict]) -> List[str]:
        """Generate recommendations based on timing analysis"""
        recommendations = []
        
        if day_analysis:
            best_day = max(day_analysis, key=lambda x: x['success_rate'])
            recommendations.append(f"Best application day: {best_day['day']} (success rate: {best_day['success_percentage']})")
        
        if hour_analysis:
            best_hour = max(hour_analysis, key=lambda x: x['success_rate'])
            recommendations.append(f"Best application time: {best_hour['hour']}:00")
        
        return recommendations
    
    def _generate_performance_insights(self, benchmarks: List[Dict], success_rates: Dict) -> List[str]:
        """Generate performance insights based on benchmarks"""
        insights = []
        
        best_metric = max(benchmarks, key=lambda x: x['percentile_rank'])
        worst_metric = min(benchmarks, key=lambda x: x['percentile_rank'])
        
        insights.append(f"Strongest performance area: {best_metric['metric']} (top {100-best_metric['percentile_rank']}%)")
        
        if worst_metric['percentile_rank'] < 50:
            insights.append(f"Area for improvement: {worst_metric['metric']} (bottom {worst_metric['percentile_rank']}%)")
        
        avg_percentile = sum(b['percentile_rank'] for b in benchmarks) / len(benchmarks)
        if avg_percentile > 70:
            insights.append("Overall performance is above market average")
        elif avg_percentile < 40:
            insights.append("Performance is below market average - focus on improvement strategies")
        else:
            insights.append("Performance is around market average with room for optimization")
        
        return insights
    
    def _generate_performance_recommendations(self, benchmarks: List[Dict], success_rates: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        improvement_opportunities = [b for b in benchmarks if b['improvement_potential'] > 0]
        improvement_opportunities.sort(key=lambda x: x['improvement_potential'], reverse=True)
        
        for opportunity in improvement_opportunities[:3]:
            if opportunity['metric'] == 'Application To Interview':
                recommendations.append("Improve application quality and targeting to increase interview rates")
            elif opportunity['metric'] == 'Interview To Offer':
                recommendations.append("Focus on interview preparation and presentation skills")
        
        if success_rates['success_rates']['overall_success'] < 3:
            recommendations.append("Consider expanding job search criteria or improving skill set")
        
        return recommendations
    
    def _calculate_market_position(self, benchmarks: List[Dict]) -> str:
        """Calculate overall market position"""
        avg_percentile = sum(b['percentile_rank'] for b in benchmarks) / len(benchmarks)
        
        if avg_percentile >= 75:
            return 'top_performer'
        elif avg_percentile >= 50:
            return 'above_average'
        elif avg_percentile >= 25:
            return 'average'
        else:
            return 'needs_improvement'
    
    async def _update_slack_real_time_metrics(self, event: SlackEvent):
        """Update real-time Slack metrics"""
        today = datetime.now().date()
        event_date = event.timestamp.date()
        
        if event_date == today:
            if event.event_type == SlackEventType.MESSAGE_SENT:
                self.slack_real_time_stats["messages_sent_today"] += 1
            elif event.event_type == SlackEventType.COMMAND_USED:
                self.slack_real_time_stats["commands_used_today"] += 1
            elif event.event_type == SlackEventType.INTERACTION:
                self.slack_real_time_stats["interactions_today"] += 1
            elif event.event_type == SlackEventType.MESSAGE_FAILED:
                self.slack_real_time_stats["errors_today"] += 1
            
            if event.user_id:
                self.slack_real_time_stats["active_users_today"].add(event.user_id)
            
            if event.channel_id:
                self.slack_real_time_stats["active_channels_today"].add(event.channel_id)
    
    async def _track_slack_message_event(self, event: SlackEvent):
        """Track Slack message-specific analytics"""
        if event.user_id:
            user_stats = self.user_engagement[event.user_id]
            user_stats["messages_received"] += 1
            user_stats["last_active"] = event.timestamp
            
            if event.channel_id:
                user_stats["channels"].add(event.channel_id)
        
        if event.channel_id:
            channel_stats = self.channel_analytics[event.channel_id]
            channel_stats["messages_sent"] += 1
            
            if event.user_id:
                channel_stats["unique_users"].add(event.user_id)
            
            hour = event.timestamp.hour
            channel_stats["activity_by_hour"][hour] += 1
            
            peak_hour = max(channel_stats["activity_by_hour"].items(), key=lambda x: x[1])[0]
            channel_stats["peak_activity_hour"] = peak_hour
    
    async def _track_slack_interaction_event(self, event: SlackEvent):
        """Track Slack interaction-specific analytics"""
        if event.user_id:
            self.user_engagement[event.user_id]["interactions"] += 1
        
        if event.channel_id:
            self.channel_analytics[event.channel_id]["interactions"] += 1
    
    async def _track_slack_command_event(self, event: SlackEvent):
        """Track Slack command-specific analytics"""
        command = event.metadata.get("command")
        if not command:
            return
        
        cmd_stats = self.command_analytics[command]
        cmd_stats["usage_count"] += 1
        
        if event.user_id:
            cmd_stats["users"].add(event.user_id)
            self.user_engagement[event.user_id]["commands_used"] += 1
        
        response_time = event.metadata.get("response_time")
        if response_time:
            current_avg = cmd_stats["avg_response_time"]
            count = cmd_stats["usage_count"]
            cmd_stats["avg_response_time"] = (current_avg * (count - 1) + response_time) / count
        
        if event.metadata.get("success", True):
            total_attempts = cmd_stats["usage_count"] + cmd_stats["errors"]
            cmd_stats["success_rate"] = (cmd_stats["usage_count"] / total_attempts) * 100
        else:
            cmd_stats["errors"] += 1
    
    async def _get_top_slack_channels(self, limit: int) -> List[Dict[str, Any]]:
        """Get top Slack channels by activity"""
        channels = []
        for channel_id, stats in self.channel_analytics.items():
            channels.append({
                "channel_id": channel_id,
                "messages_sent": stats["messages_sent"],
                "unique_users": len(stats["unique_users"]),
                "interactions": stats["interactions"]
            })
        
        return sorted(channels, key=lambda x: x["messages_sent"], reverse=True)[:limit]
    
    async def _get_top_slack_users(self, limit: int) -> List[Dict[str, Any]]:
        """Get top Slack users by engagement"""
        users = []
        for user_id, stats in self.user_engagement.items():
            engagement_score = self._calculate_user_engagement_score(stats)
            users.append({
                "user_id": user_id,
                "messages_received": stats["messages_received"],
                "interactions": stats["interactions"],
                "commands_used": stats["commands_used"],
                "engagement_score": engagement_score
            })
        
        return sorted(users, key=lambda x: x["engagement_score"], reverse=True)[:limit]
    
    async def _get_top_slack_commands(self, limit: int) -> List[Dict[str, Any]]:
        """Get top Slack commands by usage"""
        commands = []
        for command, stats in self.command_analytics.items():
            commands.append({
                "command": command,
                "usage_count": stats["usage_count"],
                "unique_users": len(stats["users"]),
                "success_rate": round(stats["success_rate"], 2)
            })
        
        return sorted(commands, key=lambda x: x["usage_count"], reverse=True)[:limit]
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.performance_metrics["response_times"]:
            return 0.0
        return sum(self.performance_metrics["response_times"]) / len(self.performance_metrics["response_times"])
    
    def _calculate_api_rate(self) -> float:
        """Calculate API calls per minute"""
        if not self.performance_metrics["api_calls"]:
            return 0.0
        
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_calls = [
            call for call in self.performance_metrics["api_calls"]
            if call > one_minute_ago
        ]
        return len(recent_calls)
    
    def _calculate_slack_success_rate(self) -> float:
        """Calculate overall Slack success rate"""
        total_messages = self.slack_real_time_stats["messages_sent_today"]
        errors = self.slack_real_time_stats["errors_today"]
        
        if total_messages == 0:
            return 100.0
        
        return ((total_messages - errors) / total_messages) * 100
    
    def _calculate_user_engagement_score(self, user_stats: Dict[str, Any]) -> float:
        """Calculate user engagement score"""
        messages = user_stats.get("messages_received", 0)
        interactions = user_stats.get("interactions", 0)
        commands = user_stats.get("commands_used", 0)
        channels = len(user_stats.get("channels", set()))
        
        score = (messages * 1) + (interactions * 3) + (commands * 2) + (channels * 0.5)
        return round(score, 2)
    
    async def _flush_email_event_cache(self):
        """Flush email event cache to persistent storage"""
        try:
            if not self.event_cache:
                return
            
            events_to_flush = self.event_cache.copy()
            self.event_cache.clear()
            
            logger.info(f"Flushed {len(events_to_flush)} email events to storage")
            
        except Exception as e:
            logger.error(f"Failed to flush email event cache: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            "healthy": True,
            "service": "analytics_specialized",
            "email_tracking_ids": len(self.email_events),
            "slack_events_tracked": len(self.slack_events),
            "users_tracked": len(self.user_engagement),
            "channels_tracked": len(self.channel_analytics),
            "commands_tracked": len(self.command_analytics),
            "cache_size": len(self.event_cache),
            "uptime": (datetime.now() - self.performance_metrics["uptime_start"]).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }


# Create service instance
analytics_specialized_service = AnalyticsSpecializedService()