"""
Consolidated Job Recommendation Service

This service consolidates multiple job recommendation and matching modules:
- job_matching_service.py: Real-time job matching and notifications (consolidated)
- job_recommendation_feedback_service.py: Feedback collection and processing (consolidated)
- job_data_normalizer.py: Data normalization and quality scoring (consolidated)

Works in coordination with separate services:
- job_source_manager.py: Job source management and analytics (separate service - see docs/architecture/job-services-architecture.md)
- job_description_parser_service.py: Job description parsing (separate stub service)

Provides unified interface for job recommendations, matching algorithms, and feedback processing.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.application import Application
from app.models.feedback import JobRecommendationFeedback
from app.models.job import Job
from app.models.user import User
from app.models.user_job_preferences import UserJobPreferences
from app.schemas.job import JobCreate
from app.schemas.job_recommendation_feedback import (
	BulkFeedbackCreate,
	FeedbackAnalytics,
	JobRecommendationFeedbackCreate,
	JobRecommendationFeedbackSummary,
	JobRecommendationFeedbackUpdate,
)
from app.services.llm_service import LLMService, get_llm_service
from app.services.recommendation_engine import RecommendationEngine
from app.services.websocket_service import websocket_service
from app.utils.datetime import utc_now
from app.utils.redis_client import redis_client

logger = get_logger(__name__)
settings = get_settings()


class JobRecommendationService:
	"""
	Unified job recommendation service that handles:
	- Job matching and scoring algorithms
	- Recommendation feedback collection and processing
	- Job source management and quality analytics
	- Data normalization and parsing
	- Real-time matching notifications
	"""

	def __init__(self, db: Session):
		self.db = db
		self.settings = settings
		self.recommendation_engine = RecommendationEngine()
		self.llm_manager = get_llm_service()

		# Job match threshold configuration
		self.high_match_threshold = getattr(settings, "high_match_threshold", 80.0)
		self.medium_match_threshold = getattr(settings, "medium_match_threshold", 60.0)
		self.instant_alert_threshold = getattr(settings, "instant_alert_threshold", 85.0)

		# Source priorities for job quality scoring
		self.source_priorities = {"linkedin": 5, "glassdoor": 4, "indeed": 3, "adzuna": 2, "usajobs": 2, "github_jobs": 1, "remoteok": 1, "manual": 5}

		# Source metadata for enhanced management
		self.source_metadata = {
			"linkedin": {
				"display_name": "LinkedIn Jobs",
				"description": "Professional network with comprehensive job data",
				"requires_api_key": True,
				"data_quality": "high",
				"specialties": ["professional", "corporate", "tech", "finance"],
			},
			"glassdoor": {
				"display_name": "Glassdoor",
				"description": "Company reviews and salary data with job postings",
				"requires_api_key": True,
				"data_quality": "high",
				"specialties": ["salary_insights", "company_culture", "reviews"],
			},
			"indeed": {
				"display_name": "Indeed",
				"description": "Large job aggregator with broad coverage",
				"requires_api_key": True,
				"data_quality": "medium",
				"specialties": ["volume", "diverse_industries", "entry_level"],
			},
			"usajobs": {
				"display_name": "USAJobs",
				"description": "Official U.S. government job portal",
				"requires_api_key": False,
				"data_quality": "high",
				"specialties": ["government", "federal", "public_sector"],
			},
			"remoteok": {
				"display_name": "Remote OK",
				"description": "Remote work focused job board",
				"requires_api_key": False,
				"data_quality": "medium",
				"specialties": ["remote", "tech", "digital_nomad"],
			},
			"manual": {
				"display_name": "Manual Entry",
				"description": "Jobs added manually by users",
				"requires_api_key": False,
				"data_quality": "variable",
				"specialties": ["custom", "networking", "referrals"],
			},
		}

		# Tech keywords for job parsing
		self.tech_keywords = {
			"python",
			"java",
			"javascript",
			"typescript",
			"c++",
			"c#",
			"go",
			"rust",
			"php",
			"ruby",
			"swift",
			"kotlin",
			"scala",
			"r",
			"matlab",
			"perl",
			"react",
			"angular",
			"vue",
			"node.js",
			"express",
			"django",
			"flask",
			"spring",
			"laravel",
			"rails",
			"asp.net",
			"blazor",
			"mysql",
			"postgresql",
			"mongodb",
			"redis",
			"elasticsearch",
			"cassandra",
			"aws",
			"azure",
			"gcp",
			"docker",
			"kubernetes",
			"terraform",
			"jenkins",
		}

	# Job Matching and Recommendations

	async def get_personalized_recommendations(
		self, db: Session, user_id: int, limit: int = 10, min_score: float = 0.0, include_applied: bool = False
	) -> List[Dict[str, Any]]:
		"""
		Get personalized job recommendations for a user.

		Args:
		    db: Database session
		    user_id: User ID to get recommendations for
		    limit: Maximum number of recommendations
		    min_score: Minimum score threshold
		    include_applied: Whether to include jobs user already applied to

		Returns:
		    List of dictionaries with job and match information
		"""
		try:
			logger.info(f"Getting personalized recommendations for user {user_id}, limit={limit}")
			# Use the recommendation engine to get scored recommendations
			recommendations = await self.recommendation_engine.get_recommendations(
				db=db,
				user_id=user_id,
				limit=limit * 2,  # Get more to filter
			)
			logger.info(f"Got {len(recommendations)} recommendations from engine")

			# Filter by score if needed
			if min_score > 0:
				recommendations = [r for r in recommendations if r.get("score", 0) >= min_score]

			# Get full job objects and format response
			result = []
			for rec in recommendations[:limit]:
				job_result = await db.execute(select(Job).filter(Job.id == rec["job_id"]))
				job = job_result.scalar_one_or_none()
				if job:
					result.append({"job": job, "match_score": rec["score"], "match_reasons": rec.get("match_reasons", []), "algorithm": "hybrid"})

			logger.info(f"Returning {len(result)} recommendations to endpoint")
			return result

		except Exception as e:
			logger.error(f"Error getting personalized recommendations: {e}", exc_info=True)
			return []

	async def generate_recommendations(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
		"""Generate job recommendations for a user"""
		try:
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				raise ValueError(f"User {user_id} not found")

			# Get user's jobs from last 30 days
			cutoff_date = utc_now() - timedelta(days=30)
			user_jobs = (
				self.db.query(Job)
				.filter(Job.user_id == user_id, Job.created_at >= cutoff_date)
				.order_by(desc(Job.created_at))
				.limit(100)  # Limit for performance
				.all()
			)

			if not user_jobs:
				return []

			recommendations = []

			for job in user_jobs:
				# Calculate match score
				match_score = self.recommendation_engine.calculate_match_score(user, job)

				# Only include matches above medium threshold
				if match_score >= self.medium_match_threshold:
					recommendation = {
						"job_id": job.id,
						"job": {
							"id": job.id,
							"title": job.title,
							"company": job.company,
							"location": job.location,
							"description": job.description,
							"tech_stack": job.tech_stack,
							"salary_range": job.salary_range,
							"job_type": job.job_type,
							"remote_option": job.remote_option,
							"source": job.source,
							"application_url": job.application_url,
							"created_at": job.created_at.isoformat() if job.created_at else None,
						},
						"match_score": match_score,
						"match_level": self._get_match_level(match_score),
						"user_id": user_id,
						"timestamp": utc_now().isoformat(),
						"source_quality": self._get_source_quality_score(job.source),
						"recommendation_reasons": self._get_recommendation_reasons(user, job, match_score),
					}
					recommendations.append(recommendation)

			# Sort by match score and return top recommendations
			recommendations.sort(key=lambda x: x["match_score"], reverse=True)
			return recommendations[:limit]

		except Exception as e:
			logger.error(f"Error generating recommendations for user {user_id}: {e}")
			return []

	async def check_job_matches_for_user(self, user: User, new_jobs: List[Job]) -> List[Dict[str, Any]]:
		"""Check new jobs against a user's profile and return matches above threshold"""
		matches = []

		for job in new_jobs:
			try:
				# Calculate match score
				match_score = self.recommendation_engine.calculate_match_score(user, job)

				# Only include matches above medium threshold
				if match_score >= self.medium_match_threshold:
					match_data = {
						"job_id": job.id,
						"job": {
							"id": job.id,
							"title": job.title,
							"company": job.company,
							"location": job.location,
							"description": job.description,
							"tech_stack": job.tech_stack,
							"salary_range": job.salary_range,
							"job_type": job.job_type,
							"remote_option": job.remote_option,
							"source": job.source,
							"application_url": job.application_url,
							"created_at": job.created_at.isoformat() if job.created_at else None,
						},
						"match_score": match_score,
						"match_level": self._get_match_level(match_score),
						"user_id": user.id,
						"timestamp": utc_now().isoformat(),
					}
					matches.append(match_data)

					logger.debug(f"Job match found for user {user.username}: {job.title} at {job.company} (Score: {match_score:.1f}%)")

			except Exception as e:
				logger.error(f"Error calculating match score for job {job.id} and user {user.id}: {e}")
				continue

		return matches

	async def send_instant_job_alerts(self, user_matches: Dict[int, List[Dict[str, Any]]]):
		"""Send instant WebSocket alerts for high-scoring job matches"""
		for user_id, matches in user_matches.items():
			try:
				# Filter for instant alert threshold
				instant_alerts = [match for match in matches if match["match_score"] >= self.instant_alert_threshold]

				if not instant_alerts:
					continue

				# Send individual alerts for each high-scoring match
				for match in instant_alerts:
					await websocket_service.send_job_match_notification(user_id=user_id, job_data=match["job"], match_score=match["match_score"])

					logger.info(f"Sent instant job alert to user {user_id}: {match['job']['title']} (Score: {match['match_score']:.1f}%)")

				# Send summary notification if multiple matches
				if len(matches) > 1:
					summary_message = f"Found {len(matches)} new job matches! {len(instant_alerts)} high-priority matches."
					await websocket_service.send_system_notification(message=summary_message, notification_type="job_matches", target_users={user_id})

			except Exception as e:
				logger.error(f"Error sending instant alerts to user {user_id}: {e}")
				continue

	def _get_match_level(self, score: float) -> str:
		"""Get match level based on score"""
		if score >= self.instant_alert_threshold:
			return "excellent"
		elif score >= self.high_match_threshold:
			return "high"
		elif score >= self.medium_match_threshold:
			return "medium"
		else:
			return "low"

	def _get_recommendation_reasons(self, user: User, job: Job, match_score: float) -> List[str]:
		"""Get reasons why this job was recommended"""
		reasons = []

		# Skill matching
		user_skills = set(skill.lower() for skill in (user.skills or []))
		job_tech_stack = set(tech.lower() for tech in (job.tech_stack or []))

		skill_overlap = user_skills.intersection(job_tech_stack)
		if skill_overlap:
			reasons.append(f"Matches your skills: {', '.join(list(skill_overlap)[:3])}")

		# Location matching
		if user.preferred_locations and job.location:
			for preferred_loc in user.preferred_locations:
				if preferred_loc.lower() in job.location.lower():
					reasons.append(f"Located in preferred area: {job.location}")
					break

		# Remote work preference
		if job.remote_option and user.profile and user.profile.get("remote_preference"):
			reasons.append("Offers remote work option")

		# Experience level matching
		if user.experience_level and job.description:
			if user.experience_level.lower() in job.description.lower():
				reasons.append(f"Matches your {user.experience_level} experience level")

		# High match score
		if match_score >= self.high_match_threshold:
			reasons.append(f"High compatibility score ({match_score:.1f}%)")

		return reasons[:5]  # Limit to top 5 reasons

	# Feedback Processing

	def process_feedback(
		self, user_id: int, feedback_data: JobRecommendationFeedbackCreate, match_score: Optional[int] = None
	) -> JobRecommendationFeedback:
		"""Process and store job recommendation feedback"""

		# Get user and job for context
		user = self.db.query(User).filter(User.id == user_id).first()
		job = self.db.query(Job).filter(Job.id == feedback_data.job_id).first()

		if not job:
			raise ValueError(f"Job with id {feedback_data.job_id} not found")

		if not user:
			raise ValueError(f"User with id {user_id} not found")

		# Check if feedback already exists for this user-job combination
		existing_feedback = (
			self.db.query(JobRecommendationFeedback)
			.filter(and_(JobRecommendationFeedback.user_id == user_id, JobRecommendationFeedback.job_id == feedback_data.job_id))
			.first()
		)

		if existing_feedback:
			# Update existing feedback instead of creating new one
			update_data = JobRecommendationFeedbackUpdate(is_helpful=feedback_data.is_helpful, comment=feedback_data.comment)
			return self.update_feedback(existing_feedback.id, update_data, user_id)

		# Create new feedback with context
		feedback = JobRecommendationFeedback(
			user_id=user_id,
			job_id=feedback_data.job_id,
			is_helpful=feedback_data.is_helpful,
			match_score=match_score,
			comment=feedback_data.comment,
			# Capture context for model training
			user_skills_at_time=user.skills or [],
			user_experience_level=user.experience_level,
			user_preferred_locations=user.preferred_locations or [],
			job_tech_stack=job.tech_stack or [],
			job_location=job.location,
			# Additional context
			recommendation_context={
				"feedback_timestamp": utc_now().isoformat(),
				"user_daily_goal": getattr(user, "daily_application_goal", None),
				"job_source": job.source,
				"job_created_at": job.created_at.isoformat() if job.created_at else None,
			},
		)

		self.db.add(feedback)
		self.db.commit()
		self.db.refresh(feedback)

		logger.info(f"Created job recommendation feedback: user_id={user_id}, job_id={feedback_data.job_id}, is_helpful={feedback_data.is_helpful}")

		return feedback

	def get_feedback(self, feedback_id: int, user_id: Optional[int] = None) -> Optional[JobRecommendationFeedback]:
		"""Get feedback by ID"""
		query = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.id == feedback_id)
		if user_id:
			query = query.filter(JobRecommendationFeedback.user_id == user_id)
		return query.first()

	def update_feedback(
		self, feedback_id: int, feedback_data: JobRecommendationFeedbackUpdate, user_id: Optional[int] = None
	) -> Optional[JobRecommendationFeedback]:
		"""Update feedback item"""
		query = self.db.query(JobRecommendationFeedback).filter(JobRecommendationFeedback.id == feedback_id)
		if user_id:
			query = query.filter(JobRecommendationFeedback.user_id == user_id)

		feedback = query.first()
		if not feedback:
			return None

		update_data = feedback_data.dict(exclude_unset=True)

		for field, value in update_data.items():
			setattr(feedback, field, value)

		self.db.commit()
		self.db.refresh(feedback)

		logger.info(f"Updated job recommendation feedback: id={feedback_id}")

		return feedback

	def get_feedback_for_recommendation_improvement(self, limit: int = 1000) -> List[Dict[str, Any]]:
		"""Get feedback data for improving recommendation algorithms"""
		feedback_data = self.db.query(JobRecommendationFeedback).order_by(desc(JobRecommendationFeedback.created_at)).limit(limit).all()

		training_data = []
		for feedback in feedback_data:
			training_data.append(
				{
					"user_skills": feedback.user_skills_at_time or [],
					"user_experience_level": feedback.user_experience_level,
					"user_preferred_locations": feedback.user_preferred_locations or [],
					"job_tech_stack": feedback.job_tech_stack or [],
					"job_location": feedback.job_location,
					"match_score": feedback.match_score,
					"is_helpful": feedback.is_helpful,
					"feedback_timestamp": feedback.created_at.isoformat(),
					"recommendation_context": feedback.recommendation_context or {},
				}
			)

		return training_data

	# Job Source Management

	def get_source_priority(self, source: str, user_id: Optional[int] = None) -> int:
		"""Get priority score for a job source"""
		base_priority = self.source_priorities.get(source, 0)

		if user_id:
			user_prefs = self.get_user_preferences(user_id)
			if user_prefs and user_prefs.source_priorities:
				custom_priority = user_prefs.source_priorities.get(source)
				if custom_priority is not None:
					return int(custom_priority)

		return base_priority

	def get_source_metadata(self, source: str) -> Dict[str, Any]:
		"""Get comprehensive metadata for a job source"""
		return self.source_metadata.get(
			source,
			{
				"display_name": source.title(),
				"description": f"Job source: {source}",
				"requires_api_key": False,
				"data_quality": "unknown",
				"specialties": [],
			},
		)

	def _get_source_quality_score(self, source: str) -> float:
		"""Get quality score for a job source"""
		quality_mapping = {
			"linkedin": 90.0,
			"glassdoor": 85.0,
			"indeed": 75.0,
			"usajobs": 95.0,
			"adzuna": 70.0,
			"github_jobs": 60.0,
			"remoteok": 70.0,
			"manual": 80.0,
		}
		return quality_mapping.get(source, 50.0)

	def get_user_preferences(self, user_id: int) -> Optional[UserJobPreferences]:
		"""Get user's job source preferences"""
		return self.db.query(UserJobPreferences).filter(UserJobPreferences.user_id == user_id).first()

	# --- Adaptive algorithm / A/B test integration helpers -----------------

	def get_algorithm_weights(self, user_id: int) -> Dict[str, int]:
		"""Return algorithm weights used for a given user.
		This delegates to the AdaptiveRecommendationEngine when available, otherwise
		returns a reasonable mapping derived from the legacy RecommendationEngine.
		"""
		try:
			# Prefer the adaptive engine when present
			from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

			engine = AdaptiveRecommendationEngine(self.db)
			weights = engine.get_algorithm_weights(user_id)
			return dict(weights)
		except Exception:
			# Fallback: map legacy recommendation weights (fractions) into percentages
			legacy = getattr(self.recommendation_engine, "weights", {})
			return {
				"skill_matching": int(legacy.get("skills_match", 0) * 100),
				"location_matching": int(legacy.get("location_match", 0) * 100),
				"experience_matching": int(legacy.get("experience_match", 0) * 100),
			}

	def _get_active_test_variant(self, user_id: int) -> str:
		"""Return the active A/B test variant for the user (if any).
		Tries adaptive engine first, falls back to 'control'.
		"""
		try:
			from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

			engine = AdaptiveRecommendationEngine(self.db)
			# Return the first active test variant found for simplicity
			for test_name, cfg in engine.ab_test_configs.items():
				if cfg.get("active"):
					return engine.get_user_algorithm_variant(user_id, test_name)
			return "control"
		except Exception:
			return "control"

	def update_algorithm_weights(self, new_weights: Dict[str, int], test_name: Optional[str] = None) -> None:
		"""Update algorithm weights globally or for a named A/B test.
		Delegates to AdaptiveRecommendationEngine when available.
		"""
		try:
			from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

			engine = AdaptiveRecommendationEngine(self.db)
			if test_name:
				# update variant weights or test config depending on API
				engine.ab_test_configs.setdefault(test_name, {})["variant_a"] = dict(new_weights)
			else:
				engine.update_algorithm_weights(new_weights)
			return
		except Exception:
			# Best-effort fallback to update legacy engine default weights
			legacy = self.recommendation_engine
			legacy.weights = {
				"skills_match": new_weights.get("skill_matching", 0) / 100.0,
				"location_match": new_weights.get("location_matching", 0) / 100.0,
				"experience_match": new_weights.get("experience_matching", 0) / 100.0,
			}

	def start_ab_test(
		self, test_name: str, variant_a: Dict[str, int], variant_b: Dict[str, int], traffic_split: float = 0.5, description: str = ""
	) -> None:
		"""Start an A/B test for algorithm variations.
		If AdaptiveRecommendationEngine is available it will be used; otherwise a best-effort
		configuration is stored on the legacy engine instance.
		"""
		try:
			from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

			engine = AdaptiveRecommendationEngine(self.db)
			engine.start_ab_test(test_name, variant_a, variant_b, traffic_split=traffic_split, description=description)
			return
		except Exception:
			# store on local state so callers can inspect
			self.ab_test_configs = getattr(self, "ab_test_configs", {})
			self.ab_test_configs[test_name] = {
				"active": True,
				"traffic_split": traffic_split,
				"variant_a": dict(variant_a),
				"variant_b": dict(variant_b),
				"description": description,
			}

	def stop_ab_test(self, test_name: str) -> None:
		"""Stop a running A/B test"""
		try:
			from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

			engine = AdaptiveRecommendationEngine(self.db)
			engine.stop_ab_test(test_name)
			return
		except Exception:
			if hasattr(self, "ab_test_configs") and test_name in self.ab_test_configs:
				self.ab_test_configs[test_name]["active"] = False

	def get_ab_test_results(self, test_name: str, days: int = 7) -> Dict[str, Any]:
		"""Get A/B test results. Delegates to adaptive engine when available."""
		try:
			from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

			engine = AdaptiveRecommendationEngine(self.db)
			return engine.get_ab_test_results(test_name, days=days)
		except Exception:
			# Return empty/default structure
			return {"variant_a": {}, "variant_b": {}, "control": {}}

	# Data Normalization and Parsing

	def normalize_job_data(self, job_data: Dict[str, Any], source: str) -> JobCreate:
		"""Normalize job data from any source into unified JobCreate schema"""
		try:
			normalized_data = {
				"company": self._normalize_company(job_data.get("company", "")),
				"title": self._normalize_title(job_data.get("title", "")),
				"location": self._normalize_location(job_data.get("location", "")),
				"description": self._normalize_description(job_data.get("description", "")),
				"salary_range": self._normalize_salary(job_data.get("salary_range")),
				"job_type": self._normalize_job_type(job_data.get("job_type", ""), job_data.get("description", "")),
				"remote_option": self._normalize_remote_option(job_data.get("remote_option", ""), job_data.get("description", "")),
				"tech_stack": self._normalize_tech_stack(job_data.get("tech_stack", []), job_data.get("description", "")),
				"requirements": job_data.get("requirements", ""),
				"responsibilities": job_data.get("responsibilities", ""),
				"application_url": self._normalize_url(job_data.get("application_url", "")),
				"source": source,
			}

			return JobCreate(**normalized_data)
		except Exception as e:
			logger.error(f"Error normalizing job data from {source}: {e}")
			# Return minimal valid job data
			return JobCreate(company=job_data.get("company", "Unknown Company"), title=job_data.get("title", "Unknown Position"), source=source)

	def _normalize_company(self, company: str) -> str:
		"""Normalize company name"""
		if not company:
			return "Unknown Company"

		# Remove common suffixes and clean up
		company = company.strip()
		company = re.sub(r"\s+(Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation|Company)", "", company, flags=re.IGNORECASE)

		return company.strip() or "Unknown Company"

	def _normalize_title(self, title: str) -> str:
		"""Normalize job title"""
		if not title:
			return "Unknown Position"

		# Clean up HTML tags and extra whitespace
		title = re.sub(r"<[^>]+>", "", title)
		title = re.sub(r"\s+", " ", title)

		return title.strip() or "Unknown Position"

	def _normalize_location(self, location: str) -> str:
		"""Normalize location string"""
		if not location:
			return "Unknown Location"

		# Clean up and standardize location format
		location = location.strip()
		location = re.sub(r"\s+", " ", location)

		# Handle remote patterns
		remote_patterns = ["remote", "work from home", "wfh", "telecommute", "distributed"]
		if any(pattern in location.lower() for pattern in remote_patterns):
			return "Remote"

		return location or "Unknown Location"

	def _normalize_description(self, description: str) -> str:
		"""Normalize job description"""
		if not description:
			return ""

		# Remove HTML tags
		description = re.sub(r"<[^>]+>", "", description)
		# Clean up extra whitespace
		description = re.sub(r"\s+", " ", description)
		# Remove excessive newlines
		description = re.sub(r"\n\s*\n", "\n\n", description)

		return description.strip()

	def _normalize_salary(self, salary: Any) -> Optional[str]:
		"""Normalize salary information"""
		if not salary:
			return None

		if isinstance(salary, (int, float)):
			return f"${salary:,}"

		if isinstance(salary, str):
			# Clean up salary string
			salary = salary.strip()
			if salary and salary.lower() not in ["not specified", "n/a", "unknown"]:
				return salary

		return None

	def _normalize_job_type(self, job_type: str, description: str) -> str:
		"""Normalize job type"""
		job_type_patterns = {
			"full-time": ["full-time", "full time", "permanent", "regular"],
			"part-time": ["part-time", "part time", "parttime"],
			"contract": ["contract", "contractor", "freelance", "consulting"],
			"temporary": ["temporary", "temp", "seasonal"],
			"internship": ["internship", "intern", "co-op", "coop"],
			"volunteer": ["volunteer", "unpaid"],
		}

		if job_type:
			job_type_lower = job_type.lower()
			for normalized_type, patterns in job_type_patterns.items():
				if any(pattern in job_type_lower for pattern in patterns):
					return normalized_type

		# Try to infer from description
		if description:
			description_lower = description.lower()
			for normalized_type, patterns in job_type_patterns.items():
				if any(pattern in description_lower for pattern in patterns):
					return normalized_type

		return "full-time"  # Default

	def _normalize_remote_option(self, remote_option: str, description: str) -> str:
		"""Normalize remote work option"""
		location_patterns = {
			"remote": ["remote", "work from home", "wfh", "telecommute", "distributed"],
			"hybrid": ["hybrid", "flexible", "part remote"],
			"onsite": ["on-site", "onsite", "office", "in-person"],
		}

		if remote_option:
			remote_lower = remote_option.lower()
			for option, patterns in location_patterns.items():
				if any(pattern in remote_lower for pattern in patterns):
					return option

		# Try to infer from description
		if description:
			description_lower = description.lower()
			for option, patterns in location_patterns.items():
				if any(pattern in description_lower for pattern in patterns):
					return option

		return "onsite"  # Default

	def _normalize_tech_stack(self, tech_stack: List[str], description: str) -> List[str]:
		"""Normalize and enhance tech stack"""
		normalized_stack = set()

		# Add existing tech stack items
		if tech_stack:
			for tech in tech_stack:
				if tech and tech.strip():
					normalized_stack.add(tech.strip().title())

		# Extract additional technologies from description
		if description:
			extracted_tech = self._extract_technologies_from_text(description)
			normalized_stack.update(extracted_tech)

		return sorted(list(normalized_stack))

	def _extract_technologies_from_text(self, text: str) -> List[str]:
		"""Extract technology keywords from text"""
		if not text:
			return []

		text_lower = text.lower()
		found_tech = []

		for tech in self.tech_keywords:
			# Use word boundaries to avoid partial matches
			pattern = r"\b" + re.escape(tech.lower()) + r"\b"
			if re.search(pattern, text_lower):
				found_tech.append(tech.title())

		return found_tech

	def _normalize_url(self, url: str) -> Optional[str]:
		"""Normalize URL"""
		if not url:
			return None

		url = url.strip()
		if url and not url.startswith(("http://", "https://")):
			url = "https://" + url

		return url if url.startswith(("http://", "https://")) else None

	# Job Description Parsing

	async def parse_job_description(self, job_url: Optional[str] = None, description_text: Optional[str] = None) -> Dict[str, Any]:
		"""Parse a job description from URL or text and extract structured data"""
		cache_key = f"job_description:{job_url}:{description_text}"
		if redis_client:
			cached_result = redis_client.get(cache_key)
			if cached_result:
				return json.loads(cached_result)

		try:
			# Get job description text
			if job_url:
				description_text = await self._scrape_job_description(job_url)

			if not description_text or not description_text.strip():
				raise ValueError("No job description text provided or scraped")

			# Use LLM for intelligent parsing
			llm_result = await self._parse_with_llm(description_text)

			# Fallback to rule-based parsing if LLM fails
			if not llm_result or not llm_result.get("tech_stack"):
				logger.warning("LLM parsing failed or incomplete, using fallback parsing")
				fallback_result = self._parse_with_rules(description_text)
				# Merge results, preferring LLM where available
				llm_result = {**fallback_result, **llm_result} if llm_result else fallback_result

			# Structure the final result
			parsed_data = {
				"tech_stack": llm_result.get("tech_stack", []),
				"requirements": llm_result.get("requirements", []),
				"responsibilities": llm_result.get("responsibilities", []),
				"experience_level": llm_result.get("experience_level"),
				"salary_range": llm_result.get("salary_range"),
				"job_type": llm_result.get("job_type"),
				"remote_option": llm_result.get("remote_option"),
				"company_info": llm_result.get("company_info", {}),
				"parsing_method": "llm" if llm_result.get("tech_stack") else "rules",
				"source_url": job_url,
			}

			if redis_client:
				redis_client.set(cache_key, json.dumps(parsed_data), ex=3600)

			logger.info(f"Successfully parsed job description from {'URL' if job_url else 'text'}")
			return parsed_data

		except Exception as e:
			logger.error(f"Error parsing job description: {e!s}")
			raise

	async def _scrape_job_description(self, job_url: str) -> str:
		"""Scrape job description from URL"""
		try:
			# Validate URL
			parsed_url = urlparse(job_url)
			if not parsed_url.scheme or not parsed_url.netloc:
				raise ValueError("Invalid URL provided")

			# Set up headers to mimic a real browser
			headers = {
				"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
				"Accept-Language": "en-US,en;q=0.5",
				"Accept-Encoding": "gzip, deflate",
				"Connection": "keep-alive",
				"Upgrade-Insecure-Requests": "1",
			}

			# Make request with timeout
			response = requests.get(job_url, headers=headers, timeout=30)
			response.raise_for_status()

			# Parse HTML
			soup = BeautifulSoup(response.content, "html.parser")

			# Remove script and style elements
			for script in soup(["script", "style"]):
				script.decompose()

			# Try different strategies to extract job description
			job_text = self._extract_job_text_from_html(soup, job_url)

			if not job_text.strip():
				raise ValueError("Could not extract job description text from the webpage")

			return job_text

		except requests.RequestException as e:
			logger.error(f"Error scraping job URL {job_url}: {e!s}")
			raise ValueError(f"Failed to scrape job description: {e!s}")
		except Exception as e:
			logger.error(f"Error processing scraped content: {e!s}")
			raise

	def _extract_job_text_from_html(self, soup: BeautifulSoup, job_url: str) -> str:
		"""Extract job description text from HTML using various strategies"""
		# Strategy 1: Look for common job description selectors
		job_selectors = [
			".jobs-description-content__text",
			".jobs-box__html-content",
			".description__text",
			".jobsearch-jobDescriptionText",
			".jobsearch-JobComponent-description",
			".jobDescriptionContent",
			".desc",
			".job-description",
			".job-content",
			".description",
			'[data-testid="job-description"]',
			"#job-description",
			".posting-description",
		]

		for selector in job_selectors:
			element = soup.select_one(selector)
			if element:
				text = element.get_text(separator="\n", strip=True)
				if len(text) > 200:  # Ensure we got substantial content
					return text

		# Strategy 2: Look for elements with job-related keywords
		job_keywords = ["responsibilities", "requirements", "qualifications", "experience", "skills"]

		for element in soup.find_all(["div", "section", "article"]):
			text = element.get_text(separator=" ", strip=True).lower()
			if any(keyword in text for keyword in job_keywords) and len(text) > 500:
				return element.get_text(separator="\n", strip=True)

		# Strategy 3: Find the largest text block (likely the job description)
		text_blocks = []
		for element in soup.find_all(["div", "section", "article", "p"]):
			text = element.get_text(separator=" ", strip=True)
			if len(text) > 200:
				text_blocks.append((len(text), text))

		if text_blocks:
			# Return the largest text block
			text_blocks.sort(reverse=True)
			return text_blocks[0][1]

		# Strategy 4: Fallback to body text
		body = soup.find("body")
		if body:
			return body.get_text(separator="\n", strip=True)

		# Last resort: all text
		return soup.get_text(separator="\n", strip=True)

	async def _parse_with_llm(self, description_text: str) -> Dict[str, Any]:
		"""Use LLM to parse job description intelligently"""
		try:
			prompt = f"""
            Please analyze the following job description and extract structured information in JSON format.

            Extract the following information:
            1. tech_stack: Array of technologies, programming languages, frameworks, tools mentioned
            2. requirements: Array of key requirements and qualifications
            3. responsibilities: Array of main job responsibilities and duties
            4. experience_level: One of "junior", "mid", or "senior" based on requirements
            5. salary_range: Salary information if mentioned (e.g., "$80,000 - $120,000")
            6. job_type: One of "full-time", "part-time", "contract", "internship", "temporary"
            7. remote_option: One of "remote", "hybrid", "onsite" based on work arrangement
            8. company_info: Object with company name, industry, size if mentioned

            Job Description:
            {description_text}

            Please respond with valid JSON only, no additional text.
            """

			response = await self.llm_manager.generate_response(prompt)

			# Try to parse JSON response
			try:
				return json.loads(response)
			except json.JSONDecodeError:
				# Try to extract JSON from response if it's wrapped in text
				json_match = re.search(r"\{.*\}", response, re.DOTALL)
				if json_match:
					return json.loads(json_match.group())
				else:
					logger.warning("LLM response was not valid JSON")
					return {}

		except Exception as e:
			logger.error(f"LLM parsing failed: {e!s}")
			return {}

	def _parse_with_rules(self, description_text: str) -> Dict[str, Any]:
		"""Fallback rule-based parsing"""
		try:
			text_lower = description_text.lower()

			# Extract tech stack
			tech_stack = set()
			for tech in self.tech_keywords:
				pattern = r"\b" + re.escape(tech.lower()) + r"\b"
				if re.search(pattern, text_lower):
					tech_stack.add(tech.title())

			# Extract experience level
			experience_level = self._extract_experience_level_rules(text_lower)

			# Extract salary range
			salary_range = self._extract_salary_range(description_text)

			# Extract job type
			job_type = self._extract_job_type(text_lower)

			# Extract remote option
			remote_option = self._extract_remote_option_rules(text_lower)

			return {
				"tech_stack": list(tech_stack),
				"requirements": [],
				"responsibilities": [],
				"experience_level": experience_level,
				"salary_range": salary_range,
				"job_type": job_type,
				"remote_option": remote_option,
				"company_info": {},
			}
		except Exception as e:
			logger.error(f"Rule-based parsing failed: {e!s}")
			return {
				"tech_stack": [],
				"requirements": [],
				"responsibilities": [],
				"experience_level": None,
				"salary_range": None,
				"job_type": None,
				"remote_option": None,
				"company_info": {},
			}

	def _extract_experience_level_rules(self, text: str) -> Optional[str]:
		"""Extract experience level using regex patterns"""
		# Check for explicit years of experience
		years_match = re.search(r"(\d+)[\+\-\s]*years?\s+(?:of\s+)?experience", text)
		if years_match:
			years = int(years_match.group(1))
			if years <= 2:
				return "junior"
			elif years <= 5:
				return "mid"
			else:
				return "senior"

		# Check for level keywords
		experience_patterns = {
			"junior": [r"\b(?:junior|entry.?level|0-2\s+years?|1-3\s+years?|intern|graduate|new\s+grad)\b"],
			"mid": [r"\b(?:mid.?level|intermediate|2-5\s+years?|3-7\s+years?|4-6\s+years?)\b"],
			"senior": [r"\b(?:senior|lead|principal|architect|5\+\s+years?|7\+\s+years?|expert|staff)\b"],
		}

		for level, patterns in experience_patterns.items():
			for pattern in patterns:
				if re.search(pattern, text):
					return level

		return None

	def _extract_salary_range(self, text: str) -> Optional[str]:
		"""Extract salary range using regex patterns"""
		salary_patterns = [
			r"\$[\d,]+\s*-\s*\$[\d,]+",
			r"\$[\d,]+k?\s*-\s*\$?[\d,]+k?",
			r"[\d,]+k?\s*-\s*[\d,]+k?\s*(?:USD|dollars?)",
			r"salary:?\s*\$?[\d,]+\s*-\s*\$?[\d,]+",
		]

		for pattern in salary_patterns:
			match = re.search(pattern, text, re.IGNORECASE)
			if match:
				return match.group().strip()
		return None

	def _extract_job_type(self, text: str) -> Optional[str]:
		"""Extract job type using regex patterns"""
		job_type_patterns = {
			"full-time": [r"\b(?:full.?time|permanent|FTE)\b"],
			"part-time": [r"\b(?:part.?time|PTE)\b"],
			"contract": [r"\b(?:contract|contractor|freelance|consulting)\b"],
			"internship": [r"\b(?:intern|internship|co-op|coop)\b"],
			"temporary": [r"\b(?:temporary|temp|seasonal)\b"],
		}

		for job_type, patterns in job_type_patterns.items():
			for pattern in patterns:
				if re.search(pattern, text):
					return job_type
		return None

	def _extract_remote_option_rules(self, text: str) -> Optional[str]:
		"""Extract remote work option using regex patterns"""
		remote_patterns = {
			"remote": [r"\b(?:remote|work\s+from\s+home|WFH|distributed)\b"],
			"hybrid": [r"\b(?:hybrid|flexible|mixed)\b"],
			"onsite": [r"\b(?:on.?site|office|in.?person|local)\b"],
		}

		for remote_type, patterns in remote_patterns.items():
			for pattern in patterns:
				if re.search(pattern, text):
					return remote_type
		return None

	# Utility Methods

	def validate_job_data_quality(self, job: JobCreate) -> Dict[str, Any]:
		"""Validate and score job data quality"""
		quality_score = 0
		max_score = 10
		issues = []

		# Check required fields
		if job.company and job.company != "Unknown Company":
			quality_score += 2
		else:
			issues.append("Missing or invalid company name")

		if job.title and job.title != "Unknown Position":
			quality_score += 2
		else:
			issues.append("Missing or invalid job title")

		# Check optional but important fields
		if job.location and job.location != "Unknown Location":
			quality_score += 1
		else:
			issues.append("Missing location information")

		if job.description and len(job.description) > 50:
			quality_score += 2
		else:
			issues.append("Missing or insufficient job description")

		if job.tech_stack and len(job.tech_stack) > 0:
			quality_score += 1
		else:
			issues.append("No technology stack information")

		if job.salary_range:
			quality_score += 1
		else:
			issues.append("No salary information")

		if job.application_url:
			quality_score += 1
		else:
			issues.append("No job posting URL")

		quality_percentage = (quality_score / max_score) * 100

		return {
			"quality_score": quality_score,
			"max_score": max_score,
			"quality_percentage": quality_percentage,
			"quality_grade": self._get_quality_grade(quality_percentage),
			"issues": issues,
		}

	def _get_quality_grade(self, percentage: float) -> str:
		"""Get quality grade based on percentage"""
		if percentage >= 90:
			return "Excellent"
		elif percentage >= 80:
			return "Good"
		elif percentage >= 70:
			return "Fair"
		elif percentage >= 60:
			return "Poor"
		else:
			return "Very Poor"

	# Methods for backward compatibility with JobMatchingService

	def get_match_thresholds(self) -> Dict[str, float]:
		"""Get current match thresholds."""
		return {
			"instant_alert_threshold": self.instant_alert_threshold,
			"high_match_threshold": self.high_match_threshold,
			"medium_match_threshold": self.medium_match_threshold,
		}

	def update_match_thresholds(
		self, instant_alert: Optional[float] = None, high_match: Optional[float] = None, medium_match: Optional[float] = None
	):
		"""Update match thresholds."""
		if instant_alert is not None:
			self.instant_alert_threshold = instant_alert
		if high_match is not None:
			self.high_match_threshold = high_match
		if medium_match is not None:
			self.medium_match_threshold = medium_match

		logger.info(
			f"Updated match thresholds: instant={self.instant_alert_threshold}, high={self.high_match_threshold}, medium={self.medium_match_threshold}"
		)


# Factory function for dependency injection
def get_job_recommendation_service(db: Session) -> JobRecommendationService:
	"""Get JobRecommendationService instance"""
	return JobRecommendationService(db)
	return JobRecommendationService(db)
