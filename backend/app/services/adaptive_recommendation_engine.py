"""Production-grade Adaptive Recommendation Engine with A/B testing and ML capabilities.

Features:
- Multi-factor recommendation scoring with configurable weights
- A/B testing framework for algorithm optimization
- User feedback integration for continuous improvement
- Caching for performance optimization
- Analytics tracking for recommendation effectiveness
- Explainable recommendations with detailed scoring breakdown
- Diversity and freshness balancing
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RecommendationConfig:
	"""Configuration for recommendation algorithm"""

	# Default scoring weights (should sum to 100)
	DEFAULT_WEIGHTS: ClassVar[Dict[str, int]] = {
		"skill_matching": 40,
		"location_matching": 20,
		"experience_matching": 15,
		"salary_matching": 10,
		"company_culture": 5,
		"growth_potential": 5,
		"recency": 5,
	}

	# Minimum match score to include in recommendations
	MIN_MATCH_SCORE = 30.0

	# Diversity parameters
	DIVERSITY_FACTOR = 0.15  # How much to boost diverse recommendations
	MAX_SAME_COMPANY = 3  # Max recommendations from same company

	# Freshness decay
	FRESHNESS_HALF_LIFE_DAYS = 7  # Jobs older than this get 50% recency score


class AdaptiveRecommendationEngine:
	"""
	Advanced recommendation engine with adaptive algorithms and A/B testing.

	Provides personalized job recommendations based on user profiles,
	with continuous optimization through user feedback and A/B experiments.
	"""

	def __init__(self, db: Session | None = None) -> None:
		"""
		Initialize recommendation engine.

		Args:
		    db: Database session for queries and persistence
		"""
		self.db = db
		self.default_weights = dict(RecommendationConfig.DEFAULT_WEIGHTS)
		self.ab_test_configs: Dict[str, Dict[str, Any]] = {}
		self._cache: Dict[str, Tuple[List[Dict[str, Any]], datetime]] = {}
		self._cache_ttl = timedelta(minutes=15)
		logger.info("AdaptiveRecommendationEngine initialized")

	def get_user_algorithm_variant(self, user_id: int, test_name: str) -> str:
		"""
		Determine which A/B test variant the user belongs to.

		Uses deterministic hashing to ensure consistent assignment.

		Args:
		    user_id: User identifier
		    test_name: Name of the A/B test

		Returns:
		    str: Variant identifier ('control', 'variant_a', 'variant_b')
		"""
		cfg = self.ab_test_configs.get(test_name)
		if not cfg or not cfg.get("active"):
			return "control"

		# Deterministic assignment based on user ID and test name
		hash_input = f"{user_id}_{test_name}".encode("utf-8")
		hash_digest = hashlib.md5(hash_input, usedforsecurity=False).hexdigest()
		bucket = int(hash_digest[:8], 16) % 100

		traffic_split = float(cfg.get("traffic_split", 0.5))
		threshold = int(traffic_split * 100)

		return "variant_a" if bucket < threshold else "variant_b"

	def get_algorithm_weights(self, user_id: int) -> Dict[str, int]:
		"""
		Get algorithm weights for user, considering active A/B tests.

		Args:
		    user_id: User identifier

		Returns:
		    Dict mapping feature to weight percentage
		"""
		# Check for active A/B tests
		for test_name, config in self.ab_test_configs.items():
			if config.get("active"):
				variant = self.get_user_algorithm_variant(user_id, test_name)
				weights = config.get(variant)
				if weights:
					logger.debug(f"User {user_id} assigned to {variant} in test {test_name}")
					return dict(weights)

		return dict(self.default_weights)

	def update_algorithm_weights(self, new_weights: Dict[str, int]) -> None:
		"""
		Update default algorithm weights.

		Args:
		    new_weights: New weight configuration
		"""
		if sum(new_weights.values()) != 100:
			logger.warning(f"Weights sum to {sum(new_weights.values())}, expected 100")

		self.default_weights = dict(new_weights)
		logger.info(f"Algorithm weights updated: {new_weights}")

	def start_ab_test(
		self, test_name: str, variant_a: Dict[str, int], variant_b: Dict[str, int], traffic_split: float = 0.5, description: str = ""
	) -> None:
		"""
		Start a new A/B test for algorithm optimization.

		Args:
		    test_name: Unique identifier for the test
		    variant_a: Weight configuration for variant A
		    variant_b: Weight configuration for variant B
		    traffic_split: Fraction of traffic for variant A (0.0-1.0)
		    description: Human-readable test description
		"""
		if not (0.0 <= traffic_split <= 1.0):
			raise ValueError("traffic_split must be between 0.0 and 1.0")

		self.ab_test_configs[test_name] = {
			"active": True,
			"traffic_split": traffic_split,
			"variant_a": dict(variant_a),
			"variant_b": dict(variant_b),
			"description": description,
			"started_at": datetime.now(timezone.utc),
		}

		logger.info(f"A/B test '{test_name}' started (split: {traffic_split:.0%})")

	def stop_ab_test(self, test_name: str) -> None:
		"""
		Stop an active A/B test.

		Args:
		    test_name: Test identifier
		"""
		if test_name in self.ab_test_configs:
			self.ab_test_configs[test_name]["active"] = False
			self.ab_test_configs[test_name]["stopped_at"] = datetime.now(timezone.utc)
			logger.info(f"A/B test '{test_name}' stopped")
		else:
			logger.warning(f"A/B test '{test_name}' not found")

	def get_ab_test_results(self, test_name: str, days: int = 7) -> Dict[str, Any]:
		"""
		Analyze results of an A/B test based on user feedback.

		Args:
		    test_name: Test identifier
		    days: Number of days to analyze

		Returns:
		    Dict with metrics for each variant
		"""
		try:
			from ..models.feedback import Feedback

			cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

			# Fetch feedback from the test period
			feedback = (
				self.db.query(Feedback)
				.filter(
					and_(
						Feedback.created_at >= cutoff_date,
						Feedback.type.in_(["job_recommendation", "recommendation_feedback"]),
					)
				)
				.all()
			)

			# Categorize feedback by variant
			metrics = {"variant_a": defaultdict(int), "variant_b": defaultdict(int), "control": defaultdict(int)}

			for fb in feedback:
				variant = self.get_user_algorithm_variant(fb.user_id, test_name)
				metrics[variant]["total"] += 1

				if hasattr(fb, "is_helpful") and fb.is_helpful:
					metrics[variant]["helpful"] += 1
				if hasattr(fb, "rating") and fb.rating:
					metrics[variant]["total_rating"] = metrics[variant].get("total_rating", 0) + fb.rating

			# Calculate satisfaction rates
			results = {}
			for variant, counts in metrics.items():
				total = counts["total"]
				results[variant] = {
					"metrics": {
						"total": total,
						"helpful": counts["helpful"],
						"satisfaction_rate": (counts["helpful"] / total) if total > 0 else 0.0,
						"avg_rating": (counts.get("total_rating", 0) / total) if total > 0 else 0.0,
					}
				}

			logger.info(f"A/B test results for '{test_name}': {results}")
			return results

		except Exception as e:
			logger.error(f"Failed to get A/B test results for '{test_name}': {e!s}")
			return {}

	def calculate_skill_match_score(self, user_skills: Set[str], job_skills: Set[str]) -> float:
		"""
		Calculate skill matching score with partial credit.

		Args:
		    user_skills: Set of user skills
		    job_skills: Set of required job skills

		Returns:
		    float: Score from 0-100
		"""
		if not job_skills:
			return 50.0  # Neutral score if no skills specified

		# Exact matches
		exact_matches = user_skills & job_skills
		match_ratio = len(exact_matches) / len(job_skills)

		# Bonus for having extra relevant skills
		skill_coverage = len(exact_matches) / len(user_skills) if user_skills else 0

		score = (match_ratio * 80) + (skill_coverage * 20)
		return min(100.0, score)

	def calculate_location_match_score(self, user_locations: Set[str], job_location: str) -> float:
		"""
		Calculate location matching score.

		Args:
		    user_locations: Set of preferred user locations
		    job_location: Job location

		Returns:
		    float: Score from 0-100
		"""
		if not user_locations:
			return 50.0  # Neutral if no preference

		job_loc_lower = job_location.lower()
		user_locs_lower = {loc.lower() for loc in user_locations}

		# Check for remote work
		if "remote" in job_loc_lower or "remote" in user_locs_lower:
			return 100.0

		# Check for exact match
		if job_loc_lower in user_locs_lower:
			return 100.0

		# Check for partial match (e.g., "San Francisco" in "San Francisco, CA")
		for user_loc in user_locs_lower:
			if user_loc in job_loc_lower or job_loc_lower in user_loc:
				return 80.0

		return 0.0

	def calculate_experience_match_score(self, user_exp_level: str, job_exp_level: str | None) -> float:
		"""
		Calculate experience level matching score.

		Args:
		    user_exp_level: User's experience level
		    job_exp_level: Required job experience level

		Returns:
		    float: Score from 0-100
		"""
		if not job_exp_level:
			return 50.0

		exp_hierarchy = {"entry": 0, "junior": 1, "mid": 2, "senior": 3, "lead": 4, "staff": 5, "principal": 6}

		user_level = exp_hierarchy.get(user_exp_level.lower(), 2)
		job_level = exp_hierarchy.get(job_exp_level.lower(), 2)

		# Perfect match
		if user_level == job_level:
			return 100.0

		# One level difference
		diff = abs(user_level - job_level)
		if diff == 1:
			return 75.0
		elif diff == 2:
			return 50.0
		else:
			return 25.0

	def calculate_salary_match_score(self, user_expectation: str | None, job_salary_range: str | None) -> float:
		"""
		Calculate salary matching score.

		Args:
		    user_expectation: User's salary expectation (e.g., "100000-120000")
		    job_salary_range: Job's salary range

		Returns:
		    float: Score from 0-100
		"""
		if not user_expectation or not job_salary_range:
			return 50.0

		try:
			# Parse salary ranges
			user_min, user_max = map(int, user_expectation.split("-"))
			job_min, job_max = map(int, job_salary_range.split("-"))

			# Check overlap
			overlap_min = max(user_min, job_min)
			overlap_max = min(user_max, job_max)

			if overlap_min <= overlap_max:
				# Calculate overlap percentage
				overlap_amount = overlap_max - overlap_min
				user_range = user_max - user_min
				overlap_ratio = overlap_amount / user_range if user_range > 0 else 1.0
				return min(100.0, overlap_ratio * 100)

			# No overlap - check if job offers more
			if job_min >= user_max:
				return 100.0  # Job pays more than expected

			# Job pays less than expected
			gap = user_min - job_max
			penalty = min(gap / user_min, 1.0) * 100
			return max(0.0, 100.0 - penalty)

		except (ValueError, AttributeError):
			return 50.0

	def calculate_recency_score(self, job_date: datetime) -> float:
		"""
		Calculate recency score with exponential decay.

		Args:
		    job_date: When the job was posted

		Returns:
		    float: Score from 0-100
		"""
		now = datetime.now(timezone.utc)
		age_days = (now - job_date).days

		# Exponential decay with half-life
		half_life = RecommendationConfig.FRESHNESS_HALF_LIFE_DAYS
		decay_factor = 0.5 ** (age_days / half_life)

		return min(100.0, decay_factor * 100)

	def calculate_match_score_adaptive(self, user: Any, job: Any, weights: Dict[str, int]) -> float:
		"""
		Calculate comprehensive match score using adaptive weights.

		Args:
		    user: User object with preferences
		    job: Job object with requirements
		    weights: Weight configuration for scoring factors

		Returns:
		    float: Overall match score from 0-100
		"""
		# Extract user attributes
		user_skills = set(getattr(user, "skills", []) or [])
		user_locations = set(getattr(user, "preferred_locations", []) or [])
		user_exp = getattr(user, "experience_level", "mid") or "mid"
		user_salary = getattr(user, "salary_expectation", None)

		# Extract job attributes
		job_skills = set(getattr(job, "tech_stack", []) or getattr(job, "requirements", {}).get("skills_required", []) or [])
		job_location = getattr(job, "location", "") or ""
		job_exp = getattr(job, "experience_level", None)
		job_salary = getattr(job, "salary_range", None)
		job_date = getattr(job, "date_added", None) or getattr(job, "created_at", datetime.now(timezone.utc))

		# Calculate component scores
		skill_score = self.calculate_skill_match_score(user_skills, job_skills)
		location_score = self.calculate_location_match_score(user_locations, job_location)
		experience_score = self.calculate_experience_match_score(user_exp, job_exp)
		salary_score = self.calculate_salary_match_score(user_salary, job_salary)
		recency_score = self.calculate_recency_score(job_date)

		# Weighted combination
		total_score = (
			skill_score * weights.get("skill_matching", 0) / 100
			+ location_score * weights.get("location_matching", 0) / 100
			+ experience_score * weights.get("experience_matching", 0) / 100
			+ salary_score * weights.get("salary_matching", 0) / 100
			+ recency_score * weights.get("recency", 0) / 100
		)

		return round(total_score, 2)

	def _apply_diversity_boost(self, recommendations: List[Dict[str, Any]]) -> None:
		"""
		Apply diversity boost to prevent same-company domination.

		Args:
		    recommendations: List of recommendation dicts (modified in-place)
		"""
		company_counts: Dict[str, int] = defaultdict(int)

		for rec in recommendations:
			company = getattr(rec["job"], "company", "Unknown")
			company_counts[company] += 1

			# Penalize if too many from same company
			if company_counts[company] > RecommendationConfig.MAX_SAME_COMPANY:
				penalty = (company_counts[company] - RecommendationConfig.MAX_SAME_COMPANY) * 5
				rec["score"] = max(0, rec["score"] - penalty)

	def get_recommendations_adaptive(
		self, user: Any, limit: int = 10, include_explanation: bool = False, use_cache: bool = True
	) -> List[Dict[str, Any]]:
		"""
		Get personalized job recommendations with adaptive algorithm.

		Args:
		    user: User object
		    limit: Maximum number of recommendations
		    include_explanation: Whether to include scoring breakdown
		    use_cache: Whether to use cached results

		Returns:
		    List of recommendation dicts with job and score
		"""
		user_id = getattr(user, "id", 0)
		cache_key = f"recs_{user_id}_{limit}"

		# Check cache
		if use_cache and cache_key in self._cache:
			cached_recs, cache_time = self._cache[cache_key]
			if datetime.now(timezone.utc) - cache_time < self._cache_ttl:
				logger.debug(f"Returning cached recommendations for user {user_id}")
				return cached_recs[:limit]

		try:
			from ..models.job import Job

			# Get algorithm weights for user
			weights = self.get_algorithm_weights(user_id)

			# Query for not-applied jobs
			jobs_query = self.db.query(Job).filter(
				and_(
					Job.status == "not_applied",
					Job.is_active == True,
				)
			)

			jobs = jobs_query.all()

			# Score each job
			scored_jobs = []
			for job in jobs:
				score = self.calculate_match_score_adaptive(user, job, weights)

				if score >= RecommendationConfig.MIN_MATCH_SCORE:
					rec_dict: Dict[str, Any] = {"job": job, "score": score}

					if include_explanation:
						rec_dict["explanation"] = self._generate_explanation(user, job, weights)

					scored_jobs.append(rec_dict)

			# Sort by score
			scored_jobs.sort(key=lambda x: x["score"], reverse=True)

			# Apply diversity boost
			self._apply_diversity_boost(scored_jobs)

			# Re-sort after diversity adjustment
			scored_jobs.sort(key=lambda x: x["score"], reverse=True)

			# Cache results
			result = scored_jobs[:limit]
			self._cache[cache_key] = (result, datetime.now(timezone.utc))

			logger.info(f"Generated {len(result)} recommendations for user {user_id} (from {len(jobs)} jobs)")
			return result

		except Exception as e:
			logger.error(f"Failed to generate recommendations for user {user_id}: {e!s}")
			return []

	def _generate_explanation(self, user: Any, job: Any, weights: Dict[str, int]) -> Dict[str, Any]:
		"""
		Generate explanation for recommendation score.

		Args:
		    user: User object
		    job: Job object
		    weights: Weight configuration

		Returns:
		    Dict with scoring breakdown and matching details
		"""
		user_skills = set(getattr(user, "skills", []) or [])
		job_skills = set(getattr(job, "tech_stack", []) or [])

		matching_skills = list(user_skills & job_skills)
		missing_skills = list(job_skills - user_skills)

		return {
			"matching_skills": matching_skills,
			"missing_skills": missing_skills,
			"location_match": getattr(job, "location", "") in getattr(user, "preferred_locations", []),
			"experience_match": getattr(job, "experience_level") == getattr(user, "experience_level"),
			"score_components": {
				"skills": self.calculate_skill_match_score(user_skills, job_skills),
				"location": self.calculate_location_match_score(set(getattr(user, "preferred_locations", [])), getattr(job, "location", "")),
				"experience": self.calculate_experience_match_score(getattr(user, "experience_level", "mid"), getattr(job, "experience_level", None)),
			},
		}

	def clear_cache(self, user_id: int | None = None) -> None:
		"""
		Clear recommendation cache.

		Args:
		    user_id: Optional user ID to clear specific user cache
		"""
		if user_id:
			keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"recs_{user_id}_")]
			for key in keys_to_remove:
				del self._cache[key]
			logger.info(f"Cleared cache for user {user_id}")
		else:
			self._cache.clear()
			logger.info("Cleared all recommendation cache")

	async def health_check(self) -> Dict[str, Any]:
		"""
		Perform health check on recommendation engine.

		Returns:
		    Dict with health status and metrics
		"""
		try:
			from ..models.job import Job

			# Check database connectivity
			job_count = self.db.query(func.count(Job.id)).scalar()

			return {
				"status": "healthy",
				"total_jobs": job_count,
				"active_ab_tests": len([t for t, c in self.ab_test_configs.items() if c.get("active")]),
				"cache_size": len(self._cache),
				"cache_ttl_minutes": self._cache_ttl.total_seconds() / 60,
			}

		except Exception as e:
			logger.error(f"Health check failed: {e!s}")
			return {"status": "unhealthy", "error": str(e)}
