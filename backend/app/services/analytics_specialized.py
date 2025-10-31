"""
Analytics Specialized Service - Advanced analytics and metrics for user performance
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.models.application import Application
from app.models.job import Job
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AnalyticsSpecializedService:
    """Advanced analytics service for detailed user performance metrics"""
    
    def calculate_detailed_success_rates(
        self, 
        db: Session, 
        user_id: int, 
        days: int = 90
    ) -> Dict[str, Any]:
        """Calculate detailed application success rates and conversion metrics"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            applications = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= start_date
                )
            ).all()
            
            if not applications:
                return {"error": "No applications found in the specified period", "period_days": days}
            
            total_apps = len(applications)
            status_counts = defaultdict(int)
            for app in applications:
                status_counts[app.status] += 1
            
            interview_count = status_counts.get("interview", 0) + status_counts.get("offer", 0) + status_counts.get("accepted", 0)
            offer_count = status_counts.get("offer", 0) + status_counts.get("accepted", 0)
            
            app_to_interview_rate = (interview_count / total_apps * 100) if total_apps > 0 else 0
            interview_to_offer_rate = (offer_count / interview_count * 100) if interview_count > 0 else 0
            overall_success_rate = (offer_count / total_apps * 100) if total_apps > 0 else 0
            rejection_rate = (status_counts.get("rejected", 0) / total_apps * 100) if total_apps > 0 else 0
            
            return {
                "period_days": days,
                "total_applications": total_apps,
                "conversion_rates": {
                    "application_to_interview": round(app_to_interview_rate, 2),
                    "interview_to_offer": round(interview_to_offer_rate, 2),
                    "overall_success": round(overall_success_rate, 2),
                    "rejection_rate": round(rejection_rate, 2)
                },
                "status_distribution": dict(status_counts),
                "insights": [
                    f"Your application-to-interview rate is {'excellent' if app_to_interview_rate > 20 else 'average' if app_to_interview_rate > 10 else 'needs improvement'}",
                    f"Interview conversion rate is {'strong' if interview_to_offer_rate > 50 else 'moderate' if interview_to_offer_rate > 25 else 'needs work'}"
                ]
            }
        except Exception as e:
            logger.error(f"Error calculating success rates: {e}")
            return {"error": str(e)}
    
    def calculate_conversion_rates(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Calculate conversion funnel rates through application stages"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            applications = db.query(Application).filter(
                and_(Application.user_id == user_id, Application.created_at >= start_date)
            ).all()
            
            if not applications:
                return {"error": "No applications found", "period_days": days}
            
            funnel = {"interested": 0, "applied": 0, "interview": 0, "offer": 0, "accepted": 0}
            for app in applications:
                if app.status in funnel:
                    funnel[app.status] += 1
            
            total = len(applications)
            return {
                "stages": {
                    stage: {
                        "count": count,
                        "percentage": round((count / total * 100), 2) if total > 0 else 0
                    }
                    for stage, count in funnel.items()
                },
                "total_applications": total,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error calculating conversion rates: {e}")
            return {"error": str(e)}
    
    def generate_performance_benchmarks(self, db: Session, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Generate performance benchmarks comparing user to platform averages"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            user_apps = db.query(Application).filter(
                and_(Application.user_id == user_id, Application.created_at >= start_date)
            ).count()
            
            user_interviews = db.query(Application).filter(
                and_(
                    Application.user_id == user_id,
                    Application.created_at >= start_date,
                    Application.status.in_(["interview", "offer", "accepted"])
                )
            ).count()
            
            total_users = db.query(func.count(func.distinct(Application.user_id))).filter(
                Application.created_at >= start_date
            ).scalar() or 1
            
            avg_apps = db.query(func.count(Application.id)).filter(
                Application.created_at >= start_date
            ).scalar() / total_users if total_users > 0 else 0
            
            user_rate = (user_interviews / user_apps * 100) if user_apps > 0 else 0
            
            return {
                "period_days": days,
                "user_metrics": {
                    "total_applications": user_apps,
                    "interviews": user_interviews,
                    "interview_rate": round(user_rate, 2)
                },
                "platform_averages": {
                    "applications_per_user": round(avg_apps, 2)
                },
                "recommendations": [
                    f"You've submitted {user_apps} applications vs platform average of {avg_apps:.0f}",
                    "above average performance" if user_apps > avg_apps else "consider increasing application volume"
                ]
            }
        except Exception as e:
            logger.error(f"Error generating benchmarks: {e}")
            return {"error": str(e)}


analytics_specialized_service = AnalyticsSpecializedService()
logger.info("Analytics specialized service initialized")
