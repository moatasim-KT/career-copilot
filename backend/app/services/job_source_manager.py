"""
Job Source Manager Service
Manages job sources, their configurations, and user preferences
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.user import User
from ..models.user_job_preferences import UserJobPreferences

logger = get_logger(__name__)


class JobSourceManager:
	"""Manages job sources and their configurations"""

	# Define all available job sources with metadata
	JOB_SOURCES: ClassVar[Dict[str, Dict[str, Any]]] = {
		"linkedin": {
			"source": "linkedin",
			"display_name": "LinkedIn Jobs",
			"description": "Professional networking platform with extensive job listings across all industries",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 9.5,
			"average_jobs_per_day": 1000,
			"categories": ["Technology", "Business", "Healthcare", "Finance", "Marketing"],
			"supported_locations": ["Global"],
			"refresh_rate_hours": 1,
		},
		"indeed": {
			"source": "indeed",
			"display_name": "Indeed",
			"description": "One of the largest job search engines with millions of listings worldwide",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 9.0,
			"average_jobs_per_day": 2000,
			"categories": ["All Industries"],
			"supported_locations": ["Global"],
			"refresh_rate_hours": 2,
		},
		"glassdoor": {
			"source": "glassdoor",
			"display_name": "Glassdoor",
			"description": "Job listings with company reviews, salaries, and interview insights",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 8.5,
			"average_jobs_per_day": 500,
			"categories": ["Technology", "Business", "Engineering"],
			"supported_locations": ["US", "Canada", "UK", "Europe"],
			"refresh_rate_hours": 3,
		},
		"dice": {
			"source": "dice",
			"display_name": "Dice",
			"description": "Specialized tech job board for IT professionals and engineers",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 8.0,
			"average_jobs_per_day": 300,
			"categories": ["Technology", "Engineering", "Data Science"],
			"supported_locations": ["US", "Canada"],
			"refresh_rate_hours": 4,
		},
		"github_jobs": {
			"source": "github_jobs",
			"display_name": "GitHub Jobs",
			"description": "Developer-focused job board integrated with GitHub",
			"is_active": True,
			"requires_api_key": True,
			"quality_score": 9.0,
			"average_jobs_per_day": 200,
			"categories": ["Software Development", "DevOps", "Data Engineering"],
			"supported_locations": ["Global"],
			"refresh_rate_hours": 6,
		},
		"stackoverflow": {
			"source": "stackoverflow",
			"display_name": "Stack Overflow Jobs",
			"description": "Developer jobs from the world's largest programming community",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 8.7,
			"average_jobs_per_day": 150,
			"categories": ["Software Development", "Engineering"],
			"supported_locations": ["Global"],
			"refresh_rate_hours": 6,
		},
		"wellfound": {
			"source": "wellfound",
			"display_name": "Wellfound (AngelList)",
			"description": "Startup and tech company job board with equity information",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 8.5,
			"average_jobs_per_day": 250,
			"categories": ["Startups", "Technology", "Product"],
			"supported_locations": ["US", "Global"],
			"refresh_rate_hours": 12,
		},
		"remotive": {
			"source": "remotive",
			"display_name": "Remotive",
			"description": "Remote job board for tech and non-tech positions",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 8.0,
			"average_jobs_per_day": 100,
			"categories": ["Remote Work", "Technology", "Marketing", "Design"],
			"supported_locations": ["Global - Remote"],
			"refresh_rate_hours": 24,
		},
		"weworkremotely": {
			"source": "weworkremotely",
			"display_name": "We Work Remotely",
			"description": "Largest remote work community with quality remote job listings",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 8.3,
			"average_jobs_per_day": 80,
			"categories": ["Remote Work", "Programming", "Design", "Marketing"],
			"supported_locations": ["Global - Remote"],
			"refresh_rate_hours": 24,
		},
		"ycombinator": {
			"source": "ycombinator",
			"display_name": "Y Combinator Jobs",
			"description": "Jobs at Y Combinator startups and portfolio companies",
			"is_active": True,
			"requires_api_key": False,
			"quality_score": 9.2,
			"average_jobs_per_day": 50,
			"categories": ["Startups", "Engineering", "Product"],
			"supported_locations": ["US", "Global"],
			"refresh_rate_hours": 24,
		},
	}

	def __init__(self, db: AsyncSession):
		self.db = db

	def get_available_sources_info(self) -> List[Dict[str, Any]]:
		"""Get information about all available job sources"""
		sources_info = []
		for source_key, source_data in self.JOB_SOURCES.items():
			sources_info.append(
				{
					**source_data,
					"last_updated": datetime.utcnow().isoformat(),
					"status": "active" if source_data["is_active"] else "inactive",
				}
			)
		return sources_info

	def get_source_info(self, source: str) -> Optional[Dict[str, Any]]:
		"""Get information about a specific job source"""
		if source in self.JOB_SOURCES:
			source_data = self.JOB_SOURCES[source].copy()
			source_data["last_updated"] = datetime.utcnow().isoformat()
			source_data["status"] = "active" if source_data["is_active"] else "inactive"
			return source_data
		return None

	async def get_user_preferences(self, user_id: int) -> Optional[UserJobPreferences]:
		"""Get user's job source preferences"""
		try:
			result = await self.db.execute(select(UserJobPreferences).where(UserJobPreferences.user_id == user_id))
			return result.scalar_one_or_none()
		except Exception as e:
			logger.error(f"Error fetching user preferences: {e}")
			return None

	async def update_user_preferences(
		self,
		user_id: int,
		enabled_sources: List[str],
		preferred_locations: Optional[List[str]] = None,
		preferred_categories: Optional[List[str]] = None,
	) -> UserJobPreferences:
		"""Update user's job source preferences"""
		try:
			# Validate sources
			invalid_sources = [s for s in enabled_sources if s not in self.JOB_SOURCES]
			if invalid_sources:
				raise ValueError(f"Invalid job sources: {invalid_sources}")

			# Get existing preferences
			prefs = await self.get_user_preferences(user_id)

			if prefs:
				# Update existing
				await self.db.execute(
					update(UserJobPreferences)
					.where(UserJobPreferences.user_id == user_id)
					.values(
						enabled_sources=enabled_sources,
						preferred_locations=preferred_locations or prefs.preferred_locations,
						preferred_categories=preferred_categories or prefs.preferred_categories,
						updated_at=datetime.utcnow(),
					)
				)
			else:
				# Create new
				prefs = UserJobPreferences(
					user_id=user_id,
					enabled_sources=enabled_sources,
					preferred_locations=preferred_locations or [],
					preferred_categories=preferred_categories or [],
				)
				self.db.add(prefs)

			await self.db.commit()

			# Refresh to get updated object
			result = await self.db.execute(select(UserJobPreferences).where(UserJobPreferences.user_id == user_id))
			return result.scalar_one()

		except Exception as e:
			await self.db.rollback()
			logger.error(f"Error updating user preferences: {e}")
			raise

	async def enable_source(self, user_id: int, source: str) -> UserJobPreferences:
		"""Enable a specific job source for a user"""
		if source not in self.JOB_SOURCES:
			raise ValueError(f"Invalid job source: {source}")

		prefs = await self.get_user_preferences(user_id)

		if prefs:
			enabled = list(set([*prefs.enabled_sources, source]))
		else:
			enabled = [source]

		return await self.update_user_preferences(user_id, enabled)

	async def disable_source(self, user_id: int, source: str) -> UserJobPreferences:
		"""Disable a specific job source for a user"""
		prefs = await self.get_user_preferences(user_id)

		if prefs and source in prefs.enabled_sources:
			enabled = [s for s in prefs.enabled_sources if s != source]
			return await self.update_user_preferences(user_id, enabled)

		return prefs

	def get_source_quality_metrics(self, source: str) -> Dict[str, Any]:
		"""Get quality metrics for a job source"""
		if source not in self.JOB_SOURCES:
			raise ValueError(f"Invalid job source: {source}")

		source_data = self.JOB_SOURCES[source]
		return {
			"source": source,
			"quality_score": source_data["quality_score"],
			"average_jobs_per_day": source_data["average_jobs_per_day"],
			"refresh_rate_hours": source_data["refresh_rate_hours"],
			"reliability": "high" if source_data["quality_score"] >= 8.5 else "medium",
		}

	def get_recommended_sources(self, user_preferences: Optional[Dict[str, Any]] = None) -> List[str]:
		"""Get recommended job sources based on user preferences"""
		# If user preferences provided, filter sources
		if user_preferences:
			preferred_categories = user_preferences.get("categories", [])
			preferred_locations = user_preferences.get("locations", [])
			remote_only = user_preferences.get("remote_only", False)

			recommended = []
			for source_key, source_data in self.JOB_SOURCES.items():
				if not source_data["is_active"]:
					continue

				score = source_data["quality_score"]

				# Boost score if matches preferences
				if preferred_categories:
					if any(cat in source_data["categories"] for cat in preferred_categories):
						score += 1.0

				if remote_only and "Remote" in " ".join(source_data["categories"]):
					score += 2.0

				recommended.append((source_key, score))

			# Sort by score and return top sources
			recommended.sort(key=lambda x: x[1], reverse=True)
			return [source for source, _ in recommended[:5]]

		# Default: return top quality sources
		sources_by_quality = sorted(
			[(k, v["quality_score"]) for k, v in self.JOB_SOURCES.items() if v["is_active"]], key=lambda x: x[1], reverse=True
		)
		return [source for source, _ in sources_by_quality[:5]]

	async def get_source_statistics(self) -> Dict[str, Any]:
		"""Get overall statistics about job sources"""
		active_sources = sum(1 for s in self.JOB_SOURCES.values() if s["is_active"])
		total_estimated_jobs = sum(s["average_jobs_per_day"] for s in self.JOB_SOURCES.values() if s["is_active"])
		avg_quality = sum(s["quality_score"] for s in self.JOB_SOURCES.values() if s["is_active"]) / active_sources

		return {
			"total_sources": len(self.JOB_SOURCES),
			"active_sources": active_sources,
			"estimated_daily_jobs": total_estimated_jobs,
			"average_quality_score": round(avg_quality, 2),
			"sources_requiring_api_key": sum(1 for s in self.JOB_SOURCES.values() if s["requires_api_key"]),
			"global_coverage": sum(1 for s in self.JOB_SOURCES.values() if "Global" in s["supported_locations"]),
		}
