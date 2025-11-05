"""
Minimal, import-safe Feedback Impact Service.

Provides basic reporting over feedback data with graceful fallbacks when the
database or models are unavailable. Designed to be lightweight and compile-safe.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.core.logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)

try:
	# Optional import; code falls back if unavailable
	from app.models.feedback import JobRecommendationFeedback  # type: ignore
except Exception:  # pragma: no cover - optional dependency
	JobRecommendationFeedback = None  # type: ignore


class FeedbackImpactService:
	"""Service for tracking the impact of feedback on system improvements."""

	def __init__(self, db: Session):
		self.db = db

	def generate_improvement_report(self, days_back: int = 30) -> Dict[str, Any]:
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
		feedback_data: List[Any] = []
		if JobRecommendationFeedback is not None:
			try:
				feedback_data = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.created_at >= cutoff_date).all()
			except Exception:
				feedback_data = []

		baseline_metrics = self._calculate_baseline_metrics(feedback_data)
		improvement_trends = self._analyze_improvement_trends(feedback_data)
		recommendations = self._generate_improvement_recommendations(baseline_metrics, improvement_trends)

		return {
			"report_period": {
				"days_back": days_back,
				"start_date": cutoff_date.isoformat(),
				"end_date": datetime.now(timezone.utc).isoformat(),
			},
			"baseline_metrics": baseline_metrics,
			"improvement_trends": improvement_trends,
			"recommendations": recommendations,
			"generated_at": datetime.now(timezone.utc).isoformat(),
		}

	def get_feedback_roi_analysis(self, days_back: int = 90) -> Dict[str, Any]:
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
		feedback_data: List[Any] = []
		if JobRecommendationFeedback is not None:
			try:
				feedback_data = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.created_at >= cutoff_date).all()
			except Exception:
				feedback_data = []

		if not feedback_data:
			return {"roi_analysis": "insufficient_data", "feedback_count": 0}

		total_feedback = len(feedback_data)
		unique_users = len({getattr(f, "user_id", None) for f in feedback_data})
		unique_jobs = len({getattr(f, "job_id", None) for f in feedback_data})

		early_period = cutoff_date + timedelta(days=days_back // 3)
		early_feedback = [f for f in feedback_data if getattr(f, "created_at", cutoff_date) < early_period]
		late_feedback = [f for f in feedback_data if getattr(f, "created_at", cutoff_date) >= early_period]

		def sat(items: List[Any]) -> float:
			n = len(items)
			if n == 0:
				return 0.0
			helpful = sum(1 for f in items if bool(getattr(f, "is_helpful", False)))
			return helpful / n

		early_satisfaction = sat(early_feedback)
		late_satisfaction = sat(late_feedback)
		satisfaction_improvement = late_satisfaction - early_satisfaction

		estimated_additional_applications = int(unique_users * satisfaction_improvement * 0.2 * 10)

		return {
			"analysis_period_days": days_back,
			"feedback_metrics": {
				"total_feedback": total_feedback,
				"unique_users_providing_feedback": unique_users,
				"unique_jobs_with_feedback": unique_jobs,
				"feedback_rate": total_feedback / max(1, unique_users),
			},
			"satisfaction_metrics": {
				"early_period_satisfaction": early_satisfaction,
				"late_period_satisfaction": late_satisfaction,
				"satisfaction_improvement": satisfaction_improvement,
				"improvement_percentage": (satisfaction_improvement / early_satisfaction * 100) if early_satisfaction > 0 else 0,
			},
			"estimated_business_impact": {
				"additional_applications_estimated": estimated_additional_applications,
				"user_engagement_improvement": satisfaction_improvement,
				"roi_category": "positive" if satisfaction_improvement > 0.05 else ("neutral" if satisfaction_improvement > -0.05 else "negative"),
			},
			"recommendations": self._generate_roi_recommendations(satisfaction_improvement, total_feedback),
		}

	def _calculate_baseline_metrics(self, feedback_data: List[Any]) -> Dict[str, Any]:
		if not feedback_data:
			return {"total_feedback": 0, "satisfaction_rate": 0.0, "feedback_volume_trend": "no_data"}

		total_feedback = len(feedback_data)
		helpful_feedback = sum(1 for f in feedback_data if bool(getattr(f, "is_helpful", False)))
		satisfaction_rate = helpful_feedback / total_feedback if total_feedback > 0 else 0.0

		daily_counts: Dict[datetime, int] = defaultdict(int)
		for f in feedback_data:
			dt = getattr(f, "created_at", datetime.now(timezone.utc))
			daily_counts[dt.date()] += 1

		if len(daily_counts) > 1:
			dates = sorted(daily_counts.keys())
			mid = len(dates) // 2
			early_avg = sum(daily_counts[d] for d in dates[:mid]) / max(1, mid)
			late_avg = sum(daily_counts[d] for d in dates[mid:]) / max(1, len(dates) - mid)
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
			"feedback_volume_trend": volume_trend,
		}

	def _analyze_improvement_trends(self, feedback_data: List[Any]) -> Dict[str, Any]:
		if not feedback_data:
			return {"trend": "no_data", "weekly_breakdown": []}

		weekly: Dict[str, Dict[str, int]] = defaultdict(lambda: {"helpful": 0, "total": 0})
		for f in feedback_data:
			dt = getattr(f, "created_at", datetime.now(timezone.utc))
			week_start = (dt.date() - timedelta(days=dt.weekday())).isoformat()
			weekly[week_start]["total"] += 1
			if bool(getattr(f, "is_helpful", False)):
				weekly[week_start]["helpful"] += 1

		weekly_breakdown: List[Dict[str, Any]] = []
		for week_start in sorted(weekly.keys()):
			data = weekly[week_start]
			rate = data["helpful"] / data["total"] if data["total"] > 0 else 0.0
			weekly_breakdown.append(
				{
					"week_start": week_start,
					"total_feedback": data["total"],
					"helpful_feedback": data["helpful"],
					"satisfaction_rate": rate,
				}
			)

		if len(weekly_breakdown) >= 2:
			mid = len(weekly_breakdown) // 2
			first = sum(w["satisfaction_rate"] for w in weekly_breakdown[:mid]) / max(1, mid)
			second = sum(w["satisfaction_rate"] for w in weekly_breakdown[mid:]) / max(1, len(weekly_breakdown) - mid)
			if second > first + 0.05:
				trend = "improving"
			elif second < first - 0.05:
				trend = "declining"
			else:
				trend = "stable"
		else:
			trend = "insufficient_data"

		return {"trend": trend, "weekly_breakdown": weekly_breakdown}

	def _generate_improvement_recommendations(self, baseline: Dict[str, Any], trends: Dict[str, Any]) -> List[Dict[str, Any]]:
		recs: List[Dict[str, Any]] = []
		satisfaction_rate = float(baseline.get("satisfaction_rate", 0.0))
		trend = str(trends.get("trend", "unknown"))
		if satisfaction_rate < 0.6:
			recs.append(
				{
					"priority": "high",
					"category": "algorithm_tuning",
					"title": "Improve recommendation algorithm",
					"description": f"Current satisfaction rate is {satisfaction_rate:.1%}, below threshold",
				}
			)
		if trend == "declining":
			recs.append(
				{
					"priority": "critical",
					"category": "urgent_review",
					"title": "Address declining satisfaction trend",
					"description": "User satisfaction is declining over time",
				}
			)
		if int(baseline.get("total_feedback", 0)) < 20:
			recs.append(
				{
					"priority": "medium",
					"category": "data_collection",
					"title": "Increase feedback collection",
					"description": "Low feedback volume limits insights",
				}
			)
		return recs
