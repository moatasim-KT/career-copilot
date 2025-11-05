"""Production-grade Analytics Reporting Service.

Features:
- Comprehensive market trend analysis
- User insight generation
- Comparative analytics
- Report templating and export
- Scheduled report generation
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


class AnalyticsReportingService:
	"""
	Comprehensive analytics reporting service.

	Generates insights, trends, and formatted reports
	from processed analytics data.
	"""

	def __init__(self, db: Session | None = None) -> None:
		"""
		Initialize analytics reporting service.

		Args:
		    db: Database session for queries
		"""
		self.db = db
		logger.info("AnalyticsReportingService initialized")

	def analyze_market_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
		"""
		Analyze market trends relevant to user.

		Args:
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    Dict with market trend insights
		"""
		try:
			if not self.db:
				return {"user_id": user_id, "error": "Database connection required"}

			from ..models.job import Job
			from ..models.user import User

			cutoff = datetime.now(timezone.utc) - timedelta(days=days)

			# Get user preferences
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				return {"error": "User not found"}

			# Analyze jobs matching user skills
			user_skills = set(getattr(user, "skills", []) or [])

			# Top companies posting jobs
			company_counts = (
				self.db.query(Job.company, func.count(Job.id))
				.filter(Job.date_added >= cutoff)
				.group_by(Job.company)
				.order_by(desc(func.count(Job.id)))
				.limit(10)
				.all()
			)

			# Top locations
			location_counts = (
				self.db.query(Job.location, func.count(Job.id))
				.filter(Job.date_added >= cutoff)
				.group_by(Job.location)
				.order_by(desc(func.count(Job.id)))
				.limit(10)
				.all()
			)

			# Skill demand analysis (from job tech_stack)
			skill_demand: Dict[str, int] = defaultdict(int)
			jobs = self.db.query(Job).filter(Job.date_added >= cutoff).all()

			for job in jobs:
				tech_stack = getattr(job, "tech_stack", []) or []
				for skill in tech_stack:
					if skill:
						skill_demand[skill.lower()] += 1

			# Top demanded skills
			top_skills = sorted(skill_demand.items(), key=lambda x: x[1], reverse=True)[:15]

			# User skill coverage
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
		Generate personalized insights for user.

		Args:
		    user_id: User identifier
		    days: Number of days to analyze

		Returns:
		    Dict with user-specific insights and recommendations
		"""
		try:
			if not self.db:
				return {"error": "Database connection required"}

			from ..models.application import Application
			from ..models.interview import Interview
			from ..models.user import User

			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				return {"error": "User not found"}

			cutoff = datetime.now(timezone.utc) - timedelta(days=days)

			# Application patterns
			applications = self.db.query(Application).filter(and_(Application.user_id == user_id, Application.created_at >= cutoff)).all()

			# Interview performance
			interviews = self.db.query(Interview).filter(and_(Interview.user_id == user_id, Interview.scheduled_at >= cutoff)).all()

			# Calculate metrics
			total_apps = len(applications)
			total_interviews = len(interviews)

			# Success rates
			offers = sum(1 for app in applications if getattr(app, "status", "") == "offer")
			rejections = sum(1 for app in applications if getattr(app, "status", "") == "rejected")

			# Application velocity
			if total_apps > 0:
				avg_apps_per_week = total_apps / (days / 7)
			else:
				avg_apps_per_week = 0

			# Generate insights
			insights = []

			if total_apps == 0:
				insights.append({"type": "action", "priority": "high", "message": "No applications submitted. Start applying to recommended jobs!"})
			elif avg_apps_per_week < 2:
				insights.append(
					{
						"type": "action",
						"priority": "medium",
						"message": f"Your application rate is low ({avg_apps_per_week:.1f}/week). Consider increasing to 5-10/week for better results.",
					}
				)

			if total_apps > 0 and total_interviews == 0:
				insights.append(
					{
						"type": "improvement",
						"priority": "high",
						"message": "No interviews yet. Consider improving your resume and tailoring applications to job requirements.",
					}
				)

			interview_rate = (total_interviews / total_apps * 100) if total_apps > 0 else 0
			if interview_rate > 0:
				insights.append(
					{
						"type": "success",
						"priority": "low",
						"message": f"Great! You're getting interviews at a {interview_rate:.1f}% rate. Keep it up!",
					}
				)

			if offers > 0:
				insights.append({"type": "success", "priority": "high", "message": f"Congratulations on {offers} offer(s)! You're doing great."})

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
		"""
		Generate weekly summary report for user.

		Args:
		    user_id: User identifier

		Returns:
		    Dict with weekly activity summary
		"""
		return self.generate_user_insights(user_id, days=7)

	def compare_users(self, user_id1: int, user_id2: int, days: int = 30) -> Dict[str, Any]:
		"""
		Compare metrics between two users (for benchmarking).

		Args:
		    user_id1: First user ID
		    user_id2: Second user ID
		    days: Number of days to compare

		Returns:
		    Dict with comparison metrics
		"""
		try:
			if not self.db:
				return {"error": "Database connection required"}

			from ..models.application import Application

			cutoff = datetime.now(timezone.utc) - timedelta(days=days)

			# Get metrics for both users
			user1_apps = (
				self.db.query(func.count(Application.id)).filter(and_(Application.user_id == user_id1, Application.created_at >= cutoff)).scalar()
				or 0
			)

			user2_apps = (
				self.db.query(func.count(Application.id)).filter(and_(Application.user_id == user_id2, Application.created_at >= cutoff)).scalar()
				or 0
			)

			return {
				"comparison": {
					"user_1": {"user_id": user_id1, "applications": user1_apps},
					"user_2": {"user_id": user_id2, "applications": user2_apps},
				},
				"difference": user1_apps - user2_apps,
				"period_days": days,
			}

		except Exception as e:
			logger.error(f"Failed to compare users: {e!s}")
			return {"error": str(e)}

	async def health_check(self) -> Dict[str, Any]:
		"""
		Perform health check on reporting service.

		Returns:
		    Dict with health status
		"""
		try:
			if not self.db:
				return {"status": "degraded", "message": "No database connection"}

			return {"status": "healthy"}

		except Exception as e:
			logger.error(f"Health check failed: {e!s}")
			return {"status": "unhealthy", "error": str(e)}
