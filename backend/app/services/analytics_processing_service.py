"""Production-grade Analytics Processing Service.

Features:
- User behavior analysis and segmentation
- Event aggregation and time-series processing
- Funnel analysis and conversion tracking
- Cohort analysis
- Real-time and batch processing modes
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AnalyticsProcessingService:
	"""
	Comprehensive analytics data processing service.

	Processes raw event data into meaningful metrics, insights,
	and aggregations for reporting and analysis.
	"""

	def __init__(self, db: Session | None = None) -> None:
		"""
		Initialize analytics processing service.

		Args:
		    db: Database session for queries
		"""
		self.db = db
		logger.info("AnalyticsProcessingService initialized")

	def get_user_analytics(self, user: Any, days: int = 30) -> Dict[str, Any]:
		"""
		Get comprehensive analytics for a user.

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

			# Fetch user data
			jobs = getattr(user, "jobs", []) or []
			applications = getattr(user, "applications", []) or []
			interviews = getattr(user, "interviews", []) or []

			# Calculate metrics
			total_jobs = len(jobs)
			total_applications = len(applications)
			total_interviews = len(interviews)

			# Application status breakdown
			status_counts = defaultdict(int)
			for app in applications:
				status = getattr(app, "status", "unknown")
				status_counts[status] += 1

			# Interview outcomes
			interview_outcomes = defaultdict(int)
			for interview in interviews:
				outcome = getattr(interview, "outcome", "pending")
				interview_outcomes[outcome] += 1

			# Time-based metrics
			recent_cutoff = datetime.now(timezone.utc) - timedelta(days=days)
			recent_applications = [
				app for app in applications if getattr(app, "created_at", datetime.min.replace(tzinfo=timezone.utc)) >= recent_cutoff
			]

			# Success metrics
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
		Analyze user's application funnel stages.

		Args:
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    Dict with funnel metrics and conversion rates
		"""
		try:
			if not self.db:
				return {"error": "Database connection required"}

			from ..models.application import Application
			from ..models.interview import Interview

			cutoff = datetime.now(timezone.utc) - timedelta(days=days)

			# Count applications at each stage
			total_viewed = (
				self.db.query(func.count(Application.id)).filter(and_(Application.user_id == user_id, Application.created_at >= cutoff)).scalar() or 0
			)

			applied = (
				self.db.query(func.count(Application.id))
				.filter(
					and_(
						Application.user_id == user_id,
						Application.status.in_(["applied", "in_review", "interview", "offer"]),
						Application.created_at >= cutoff,
					)
				)
				.scalar()
				or 0
			)

			interviews = (
				self.db.query(func.count(Interview.id)).filter(and_(Interview.user_id == user_id, Interview.scheduled_at >= cutoff)).scalar() or 0
			)

			offers = (
				self.db.query(func.count(Application.id))
				.filter(and_(Application.user_id == user_id, Application.status == "offer", Application.created_at >= cutoff))
				.scalar()
				or 0
			)

			# Calculate conversion rates
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

	def aggregate_events_by_type(self, user_id: int, days: int = 7) -> Dict[str, int]:
		"""
		Aggregate events by type for a user.

		Args:
		    user_id: User identifier
		    days: Number of days to aggregate

		Returns:
		    Dict mapping event type to count
		"""
		# In production, query analytics_events table
		# For now, return placeholder
		return {
			"page_view": 0,
			"job_view": 0,
			"application_submit": 0,
			"profile_update": 0,
			"search": 0,
		}

	def calculate_engagement_score(self, user_id: int, days: int = 7) -> float:
		"""
		Calculate user engagement score based on activity.

		Args:
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    float: Engagement score from 0-100
		"""
		try:
			if not self.db:
				return 0.0

			from ..models.application import Application
			from ..models.job import Job

			cutoff = datetime.now(timezone.utc) - timedelta(days=days)

			# Count different types of activities
			job_views = self.db.query(func.count(Job.id)).filter(and_(Job.user_id == user_id, Job.date_added >= cutoff)).scalar() or 0

			applications = (
				self.db.query(func.count(Application.id)).filter(and_(Application.user_id == user_id, Application.created_at >= cutoff)).scalar() or 0
			)

			# Weight different activities
			score = (job_views * 1) + (applications * 10)

			# Normalize to 0-100 scale
			max_score = days * 20  # Assume max 20 activities per day
			normalized_score = min(100.0, (score / max_score) * 100)

			return round(normalized_score, 2)

		except Exception as e:
			logger.error(f"Failed to calculate engagement score: {e!s}")
			return 0.0

	def segment_users(self, days: int = 30) -> Dict[str, List[int]]:
		"""
		Segment all users based on behavior patterns.

		Args:
		    days: Number of days to analyze

		Returns:
		    Dict mapping segment name to list of user IDs
		"""
		try:
			if not self.db:
				return {}

			from ..models.application import Application
			from ..models.user import User

			cutoff = datetime.now(timezone.utc) - timedelta(days=days)

			# Query all users
			users = self.db.query(User).all()

			segments: Dict[str, List[int]] = {
				"highly_active": [],
				"moderately_active": [],
				"low_activity": [],
				"inactive": [],
			}

			for user in users:
				# Count applications
				app_count = (
					self.db.query(func.count(Application.id)).filter(and_(Application.user_id == user.id, Application.created_at >= cutoff)).scalar()
					or 0
				)

				# Segment based on activity
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

	async def health_check(self) -> Dict[str, Any]:
		"""
		Perform health check on processing service.

		Returns:
		    Dict with health status
		"""
		try:
			if not self.db:
				return {"status": "degraded", "message": "No database connection"}

			from ..models.user import User

			# Test database connectivity
			user_count = self.db.query(func.count(User.id)).scalar()

			return {"status": "healthy", "total_users": user_count}

		except Exception as e:
			logger.error(f"Health check failed: {e!s}")
			return {"status": "unhealthy", "error": str(e)}
