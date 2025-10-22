"""
Service for tracking feedback impact and generating improvement reports
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from collections import defaultdict
import json

from app.models.feedback import JobRecommendationFeedback
from app.models.job import Job
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeedbackImpactService:
    """Service for tracking the impact of feedback on system improvements"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_algorithm_change_impact(
        self, 
        change_description: str,
        old_weights: Dict[str, float],
        new_weights: Dict[str, float],
        change_type: str = "weight_adjustment"
    ) -> Dict[str, Any]:
        """
        Track the impact of an algorithm change
        """
        change_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "change_type": change_type,
            "description": change_description,
            "old_weights": old_weights,
            "new_weights": new_weights,
            "weight_changes": {
                key: new_weights.get(key, 0) - old_weights.get(key, 0)
                for key in set(list(old_weights.keys()) + list(new_weights.keys()))
            }
        }
        
        # Store in a simple JSON file for now (in production, use proper database table)
        self._store_change_record(change_record)
        
        logger.info(f"Tracked algorithm change: {change_description}")
        
        return change_record
    
    def _store_change_record(self, record: Dict[str, Any]):
        """Store algorithm change record (simplified implementation)"""
        # In production, this would be stored in a proper database table
        # For now, we'll just log it
        logger.info(f"Algorithm change record: {json.dumps(record, indent=2)}")
    
    def generate_improvement_report(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate a comprehensive report on system improvements based on feedback
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get feedback data for the period
        feedback_data = self.db.query(JobRecommendationFeedback).filter(
            JobRecommendationFeedback.created_at >= cutoff_date
        ).all()
        
        # Calculate baseline metrics
        baseline_metrics = self._calculate_baseline_metrics(feedback_data)
        
        # Analyze improvement trends
        improvement_trends = self._analyze_improvement_trends(feedback_data, days_back)
        
        # Generate recommendations for further improvements
        recommendations = self._generate_improvement_recommendations(baseline_metrics, improvement_trends)
        
        return {
            "report_period": {
                "days_back": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "baseline_metrics": baseline_metrics,
            "improvement_trends": improvement_trends,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_baseline_metrics(self, feedback_data: List[JobRecommendationFeedback]) -> Dict[str, Any]:
        """Calculate baseline performance metrics"""
        if not feedback_data:
            return {
                "total_feedback": 0,
                "satisfaction_rate": 0,
                "feedback_volume_trend": "no_data"
            }
        
        total_feedback = len(feedback_data)
        helpful_feedback = sum(1 for f in feedback_data if f.is_helpful)
        satisfaction_rate = helpful_feedback / total_feedback if total_feedback > 0 else 0
        
        # Calculate daily feedback volume
        daily_counts = defaultdict(int)
        for feedback in feedback_data:
            date_key = feedback.created_at.date()
            daily_counts[date_key] += 1
        
        # Determine volume trend
        if len(daily_counts) > 1:
            dates = sorted(daily_counts.keys())
            early_avg = sum(daily_counts[date] for date in dates[:len(dates)//2]) / (len(dates)//2)
            late_avg = sum(daily_counts[date] for date in dates[len(dates)//2:]) / (len(dates) - len(dates)//2)
            
            if late_avg > early_avg * 1.1:
                volume_trend = "increasing"
            elif late_avg < early_avg * 0.9:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"
        else:
            volume_trend = "insufficient_data"
        
        return {
            "total_feedback": total_feedback,
            "helpful_feedback": helpful_feedback,
            "unhelpful_feedback": total_feedback - helpful_feedback,
            "satisfaction_rate": satisfaction_rate,
            "daily_average": total_feedback / max(1, len(daily_counts)),
            "feedback_volume_trend": volume_trend
        }
    
    def _analyze_improvement_trends(self, feedback_data: List[JobRecommendationFeedback], days_back: int) -> Dict[str, Any]:
        """Analyze trends in user satisfaction over time"""
        if not feedback_data:
            return {"trend": "no_data", "weekly_breakdown": []}
        
        # Group feedback by week
        weekly_data = defaultdict(lambda: {"helpful": 0, "total": 0})
        
        for feedback in feedback_data:
            # Get week start (Monday)
            week_start = feedback.created_at.date() - timedelta(days=feedback.created_at.weekday())
            
            weekly_data[week_start]["total"] += 1
            if feedback.is_helpful:
                weekly_data[week_start]["helpful"] += 1
        
        # Calculate weekly satisfaction rates
        weekly_breakdown = []
        for week_start in sorted(weekly_data.keys()):
            data = weekly_data[week_start]
            satisfaction_rate = data["helpful"] / data["total"] if data["total"] > 0 else 0
            
            weekly_breakdown.append({
                "week_start": week_start.isoformat(),
                "total_feedback": data["total"],
                "helpful_feedback": data["helpful"],
                "satisfaction_rate": satisfaction_rate
            })
        
        # Determine overall trend
        if len(weekly_breakdown) >= 2:
            first_half_avg = sum(w["satisfaction_rate"] for w in weekly_breakdown[:len(weekly_breakdown)//2]) / (len(weekly_breakdown)//2)
            second_half_avg = sum(w["satisfaction_rate"] for w in weekly_breakdown[len(weekly_breakdown)//2:]) / (len(weekly_breakdown) - len(weekly_breakdown)//2)
            
            if second_half_avg > first_half_avg + 0.05:
                trend = "improving"
            elif second_half_avg < first_half_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "weekly_breakdown": weekly_breakdown,
            "trend_strength": abs(weekly_breakdown[-1]["satisfaction_rate"] - weekly_breakdown[0]["satisfaction_rate"]) if len(weekly_breakdown) >= 2 else 0
        }
    
    def _generate_improvement_recommendations(
        self, 
        baseline_metrics: Dict[str, Any], 
        improvement_trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on metrics and trends"""
        recommendations = []
        
        satisfaction_rate = baseline_metrics.get("satisfaction_rate", 0)
        trend = improvement_trends.get("trend", "unknown")
        
        # Low satisfaction rate recommendations
        if satisfaction_rate < 0.6:
            recommendations.append({
                "priority": "high",
                "category": "algorithm_tuning",
                "title": "Improve recommendation algorithm",
                "description": f"Current satisfaction rate is {satisfaction_rate:.1%}, which is below the 60% threshold",
                "suggested_actions": [
                    "Analyze feedback patterns to identify weak areas",
                    "Consider A/B testing new algorithm weights",
                    "Review skill matching logic for accuracy"
                ]
            })
        
        # Declining trend recommendations
        if trend == "declining":
            recommendations.append({
                "priority": "critical",
                "category": "urgent_review",
                "title": "Address declining satisfaction trend",
                "description": "User satisfaction is declining over time",
                "suggested_actions": [
                    "Immediate review of recent algorithm changes",
                    "Analyze user feedback comments for common issues",
                    "Consider rolling back recent changes if necessary"
                ]
            })
        
        # Low feedback volume recommendations
        if baseline_metrics.get("total_feedback", 0) < 20:
            recommendations.append({
                "priority": "medium",
                "category": "data_collection",
                "title": "Increase feedback collection",
                "description": "Low feedback volume limits improvement insights",
                "suggested_actions": [
                    "Add more prominent feedback collection UI",
                    "Implement feedback incentives or gamification",
                    "Send periodic feedback request emails"
                ]
            })
        
        # High satisfaction but stable trend
        if satisfaction_rate > 0.8 and trend == "stable":
            recommendations.append({
                "priority": "low",
                "category": "optimization",
                "title": "Explore advanced features",
                "description": "High satisfaction provides opportunity for feature expansion",
                "suggested_actions": [
                    "Test advanced personalization features",
                    "Implement machine learning improvements",
                    "Add new recommendation factors"
                ]
            })
        
        return recommendations
    
    def get_feedback_roi_analysis(self, days_back: int = 90) -> Dict[str, Any]:
        """
        Analyze the return on investment of feedback collection and improvements
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get feedback data
        feedback_data = self.db.query(JobRecommendationFeedback).filter(
            JobRecommendationFeedback.created_at >= cutoff_date
        ).all()
        
        if not feedback_data:
            return {
                "roi_analysis": "insufficient_data",
                "feedback_count": 0
            }
        
        # Calculate engagement metrics
        total_feedback = len(feedback_data)
        unique_users = len(set(f.user_id for f in feedback_data))
        unique_jobs = len(set(f.job_id for f in feedback_data))
        
        # Calculate satisfaction improvement over time
        early_period = cutoff_date + timedelta(days=days_back//3)
        early_feedback = [f for f in feedback_data if f.created_at < early_period]
        late_feedback = [f for f in feedback_data if f.created_at >= early_period]
        
        early_satisfaction = sum(1 for f in early_feedback if f.is_helpful) / len(early_feedback) if early_feedback else 0
        late_satisfaction = sum(1 for f in late_feedback if f.is_helpful) / len(late_feedback) if late_feedback else 0
        
        satisfaction_improvement = late_satisfaction - early_satisfaction
        
        # Estimate business impact
        # Assume each satisfied user applies to 20% more jobs
        estimated_additional_applications = unique_users * satisfaction_improvement * 0.2 * 10  # 10 jobs per user average
        
        return {
            "analysis_period_days": days_back,
            "feedback_metrics": {
                "total_feedback": total_feedback,
                "unique_users_providing_feedback": unique_users,
                "unique_jobs_with_feedback": unique_jobs,
                "feedback_rate": total_feedback / max(1, unique_users)  # Feedback per user
            },
            "satisfaction_metrics": {
                "early_period_satisfaction": early_satisfaction,
                "late_period_satisfaction": late_satisfaction,
                "satisfaction_improvement": satisfaction_improvement,
                "improvement_percentage": (satisfaction_improvement / early_satisfaction * 100) if early_satisfaction > 0 else 0
            },
            "estimated_business_impact": {
                "additional_applications_estimated": estimated_additional_applications,
                "user_engagement_improvement": satisfaction_improvement,
                "roi_category": "positive" if satisfaction_improvement > 0.05 else "neutral" if satisfaction_improvement > -0.05 else "negative"
            },
            "recommendations": self._generate_roi_recommendations(satisfaction_improvement, total_feedback)
        }
    
    def _generate_roi_recommendations(self, satisfaction_improvement: float, feedback_count: int) -> List[str]:
        """Generate ROI-focused recommendations"""
        recommendations = []
        
        if satisfaction_improvement > 0.1:
            recommendations.append("Strong positive ROI - continue current feedback-driven improvement strategy")
        elif satisfaction_improvement > 0.05:
            recommendations.append("Moderate positive ROI - consider expanding feedback collection efforts")
        elif satisfaction_improvement > -0.05:
            recommendations.append("Neutral ROI - review feedback implementation strategy")
        else:
            recommendations.append("Negative ROI - urgent review of feedback system needed")
        
        if feedback_count < 50:
            recommendations.append("Increase feedback collection volume for more reliable insights")
        elif feedback_count > 200:
            recommendations.append("Good feedback volume - focus on quality analysis and implementation")
        
        return recommendations