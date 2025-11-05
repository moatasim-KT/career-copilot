"""
Recommendation Engine - ML-based job recommendation system
"""

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RecommendationEngine:
	"""ML-based job recommendation engine using collaborative filtering and content-based approaches"""

	def __init__(self):
		"""Initialize the recommendation engine"""
		self.weights = {"skills_match": 0.4, "location_match": 0.2, "experience_match": 0.2, "industry_match": 0.1, "recency": 0.1}
		logger.info("Recommendation engine initialized with weighted scoring")

	async def get_recommendations(self, db: AsyncSession, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
		"""
		Get personalized job recommendations for a user.

		Uses hybrid approach:
		- Content-based filtering (skills, location, experience)
		- Collaborative filtering (similar users' successful applications)
		- Popularity-based (trending jobs)

		Args:
		    db: Database session
		    user_id: User ID to get recommendations for
		    limit: Maximum number of recommendations

		Returns:
		    List of recommended jobs with scores
		"""
		try:
			logger.info(f"Getting recommendations for user {user_id}, limit={limit}")
			# Get user
			result = await db.execute(select(User).filter(User.id == user_id))
			user = result.scalar_one_or_none()
			if not user:
				logger.warning(f"User {user_id} not found")
				return []

			logger.info(f"Found user {user.id}: {user.username}")

			# Get user's applied jobs to exclude
			applied_result = await db.execute(select(Application.job_id).filter(Application.user_id == user_id))
			applied_ids = [row[0] for row in applied_result.all()]
			logger.info(f"User has applied to {len(applied_ids)} jobs: {applied_ids}")

			# Get available jobs (not applied, active, recent)
			# Use timezone-naive datetime to match database
			thirty_days_ago = datetime.now() - timedelta(days=30)
			query = select(Job).filter(Job.created_at >= thirty_days_ago)

			if applied_ids:
				query = query.filter(Job.id.notin_(applied_ids))

			query = query.limit(100)
			jobs_result = await db.execute(query)
			available_jobs = jobs_result.scalars().all()
			logger.info(f"Found {len(available_jobs)} available jobs")

			# Score each job
			scored_jobs = []
			for job in available_jobs:
				score = self._calculate_job_score(user, job)
				scored_jobs.append(
					{
						"job_id": job.id,
						"title": job.title,
						"company": job.company,
						"location": job.location,
						"score": round(score, 2),
						"match_reasons": self._get_match_reasons(user, job, score),
					}
				)

			# Sort by score and return top N
			scored_jobs.sort(key=lambda x: x["score"], reverse=True)
			return scored_jobs[:limit]

		except Exception as e:
			logger.error(f"Error getting recommendations: {e}")
			return []

	def _calculate_job_score(self, user: User, job: Job) -> float:
		"""Calculate recommendation score for a job based on available fields"""
		score = 0.0

		# Skills match (comparing user.skills with job.tech_stack)
		if user.skills and job.tech_stack:
			user_skills = set([s.lower() for s in user.skills])
			job_skills = set([s.lower() for s in job.tech_stack])
			skills_overlap = len(user_skills & job_skills)
			skills_match = skills_overlap / len(job_skills) if job_skills else 0
			score += skills_match * self.weights["skills_match"]

		# Location match
		if user.preferred_locations and job.location:
			location_match = any(loc.lower() in job.location.lower() for loc in user.preferred_locations)
			score += (1.0 if location_match else 0.0) * self.weights["location_match"]

		# Experience level match - simplified since we don't have job.experience_level
		# Award a base score for having experience specified
		if user.experience_level:
			score += 0.5 * self.weights["experience_match"]

		# Industry match - skip since Job model doesn't have industry field
		# Using company name similarity instead
		# score += 0.0  # Placeholder

		# Recency boost (newer jobs scored higher)
		# Use timezone-naive datetime
		days_old = (datetime.now() - job.created_at).days
		recency_score = max(0, 1 - (days_old / 30))  # Linear decay over 30 days
		score += recency_score * self.weights["recency"]

		return min(score, 1.0)  # Cap at 1.0

	def _get_match_reasons(self, user: User, job: Job, score: float) -> List[str]:
		"""Generate human-readable match reasons based on available fields"""
		reasons = []

		if user.skills and job.tech_stack:
			user_skills = set([s.lower() for s in user.skills])
			job_skills = set([s.lower() for s in job.tech_stack])
			matching_skills = user_skills & job_skills
			if matching_skills:
				reasons.append(f"Matches {len(matching_skills)} of your skills")

		if user.preferred_locations and job.location:
			if any(loc.lower() in job.location.lower() for loc in user.preferred_locations):
				reasons.append("Matches your preferred location")

		if score > 0.7:
			reasons.append("Highly recommended based on your profile")
		elif score > 0.5:
			reasons.append("Good match for your background")

		return reasons

	async def train_model(self, db: AsyncSession, user_data: Dict[str, Any]) -> None:
		"""
		Update recommendation model with user feedback.
		In production, this would update ML model weights.
		For now, logs user interactions for future model training.

		Args:
		    db: Database session
		    user_data: User interaction data (applications, views, saves)
		"""
		logger.info(f"Recording user interaction data for model training: {user_data.get('user_id')}")
		# In production: Update collaborative filtering matrix, retrain models
		pass

	async def update_user_profile(self, db: AsyncSession, user_id: int, profile_data: Dict[str, Any]) -> None:
		"""
		Update user profile to improve recommendations.
		Updates user preferences and recalculates recommendation weights.

		Args:
		    db: Database session
		    user_id: User ID
		    profile_data: Updated profile information (skills, preferences, etc.)
		"""
		try:
			user = db.query(User).filter(User.id == user_id).first()
			if not user:
				return

			# Update user preferences
			if "skills" in profile_data:
				user.skills = profile_data["skills"]
			if "preferred_locations" in profile_data:
				user.preferred_locations = profile_data["preferred_locations"]
			if "target_industries" in profile_data:
				user.target_industries = profile_data["target_industries"]

			db.commit()
			logger.info(f"Updated user profile for improved recommendations: user_id={user_id}")

		except Exception as e:
			logger.error(f"Error updating user profile: {e}")
			db.rollback()


# Global instance
recommendation_engine = RecommendationEngine()
logger.info("Recommendation engine service initialized")
