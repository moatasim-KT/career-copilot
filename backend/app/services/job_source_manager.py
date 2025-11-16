"""
Job Source Manager Service
Manages job sources, their configurations, and user preferences
"""

from typing import Any, ClassVar, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models.user import User
from ..models.user_job_preferences import UserJobPreferences
from ..utils.datetime import utc_now

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
					"last_updated": utc_now().isoformat(),
					"status": "active" if source_data["is_active"] else "inactive",
				}
			)
		return sources_info

	def get_source_info(self, source: str) -> Optional[Dict[str, Any]]:
		"""Get information about a specific job source"""
		if source in self.JOB_SOURCES:
			source_data = self.JOB_SOURCES[source].copy()
			source_data["last_updated"] = utc_now().isoformat()
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
						updated_at=utc_now(),
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

	async def create_or_update_user_preferences(self, user_id: int, preferences_data: Dict[str, Any]) -> UserJobPreferences:
		"""Create or update user job source preferences from a dict payload."""
		from sqlalchemy import select, update

		try:
			# Normalize incoming fields to model column names
			values = {
				"preferred_sources": preferences_data.get("preferred_sources", None),
				"disabled_sources": preferences_data.get("disabled_sources", None),
				"source_priorities": preferences_data.get("source_priorities", None),
				"auto_scraping_enabled": preferences_data.get("auto_scraping_enabled", None),
				"max_jobs_per_source": preferences_data.get("max_jobs_per_source", None),
				"min_quality_threshold": preferences_data.get("min_quality_threshold", None),
				"notify_on_high_match": preferences_data.get("notify_on_high_match", None),
				"notify_on_new_sources": preferences_data.get("notify_on_new_sources", None),
			}

			# Remove None values so we only update provided fields
			values = {k: v for k, v in values.items() if v is not None}

			# Try to find existing prefs
			result = await self.db.execute(select(UserJobPreferences).where(UserJobPreferences.user_id == user_id))
			prefs = result.scalar_one_or_none()

			if prefs:
				# Update provided fields
				if values:
					await self.db.execute(update(UserJobPreferences).where(UserJobPreferences.user_id == user_id).values(**values))
			else:
				# Create new preferences row
				prefs = UserJobPreferences(
					user_id=user_id,
					preferred_sources=values.get("preferred_sources", []),
					disabled_sources=values.get("disabled_sources", []),
					source_priorities=values.get("source_priorities", {}),
					auto_scraping_enabled=values.get("auto_scraping_enabled", True),
					max_jobs_per_source=values.get("max_jobs_per_source", 10),
					min_quality_threshold=values.get("min_quality_threshold", 60.0),
					notify_on_high_match=values.get("notify_on_high_match", True),
					notify_on_new_sources=values.get("notify_on_new_sources", False),
				)
				self.db.add(prefs)

			await self.db.commit()

			# Refresh and return
			result = await self.db.execute(select(UserJobPreferences).where(UserJobPreferences.user_id == user_id))
			return result.scalar_one()

		except Exception as e:
			await self.db.rollback()
			logger.error(f"Error creating/updating user preferences: {e}")
			raise

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

	def _get_source_quality_score(self, source: str) -> float:
		"""Private helper returning a numeric quality score for a source.
		This keeps compatibility with other services that call _get_source_quality_score.
		"""
		try:
			return float(self.JOB_SOURCES.get(source, {}).get("quality_score", 50.0))
		except Exception:
			return 50.0

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

	# --- Analytics helpers -------------------------------------------------

	async def get_user_source_preferences(self, user_id: int) -> Dict[str, Any]:
		"""Return a lightweight, serializable view of a user's source preferences and derived insights."""
		prefs = await self.get_user_preferences(user_id)
		if not prefs:
			# Default structure when no prefs exist
			return {
				"insights": [],
				"recommended_sources": self.get_recommended_sources(),
				"source_performance": {},
			}

		# Build user insights and recommended sources
		user_pref_data = {
			"insights": [{"note": "Using custom source priorities"} if prefs.source_priorities else {"note": "No custom source priorities"}],
			"recommended_sources": self.get_recommended_sources(
				{
					"categories": [],
					"locations": [],
					"remote_only": False,
				}
			),
			"source_performance": {},
		}

		return user_pref_data

	async def get_source_analytics(self, timeframe_days: int = 30, user_id: Optional[int] = None) -> Dict[str, Any]:
		"""Return analytics for all job sources over the requested timeframe.
		A practical, lightweight implementation suitable for tests and endpoint responses.
		"""
		from sqlalchemy import func

		from ..models.job import Job

		cutoff = None
		try:
			from datetime import timedelta

			cutoff = utc_now() - timedelta(days=max(1, int(timeframe_days)))
		except Exception:
			cutoff = None

		analytics: Dict[str, Any] = {s: {"jobs_count": 0, "quality": self._get_source_quality_score(s)} for s in self.JOB_SOURCES}

		# Try to count recent jobs per source when DB is available
		try:
			result = await self.db.execute(select(Job.source, func.count(Job.id).label("count")).where(Job.created_at >= cutoff).group_by(Job.source))
			for row in result.all():
				source_key = row[0]
				if source_key in analytics:
					analytics[source_key]["jobs_count"] = int(row[1])
		except Exception:
			# If DB or schema not available, return best-effort values
			pass

		# Build summary and simple trends placeholder
		summary = {
			"timeframe_days": timeframe_days,
			"by_source": analytics,
			"trends": {},
		}

		return summary

	async def get_source_performance_summary(self, user_id: int, timeframe_days: int = 30) -> Dict[str, Any]:
		"""Return a user-personalized source performance summary used by endpoints.
		This composes analytics and user preference data into a compact response.
		"""
		analytics = await self.get_source_analytics(timeframe_days, user_id)
		user_prefs = await self.get_user_source_preferences(user_id)

		# Create a simple ranking by combining quality and job counts
		rankings = []
		for src, data in analytics.get("by_source", {}).items():
			rank_score = float(data.get("quality", 0)) * 0.7 + float(data.get("jobs_count", 0)) * 0.3
			rankings.append(
				{"source": src, "score": round(rank_score, 2), "jobs_count": data.get("jobs_count", 0), "quality": data.get("quality", 0)}
			)

		rankings.sort(key=lambda x: x["score"], reverse=True)

		return {
			"rankings": rankings,
			"analytics": analytics,
			"user_insights": user_prefs.get("insights", []),
			"recommended_sources": user_prefs.get("recommended_sources", []),
		}

	def calculate_source_quality_score(self, source: str, timeframe_days: int = 30, user_id: Optional[int] = None) -> float:
		"""Return a numeric quality score for the given source. This is a thin wrapper
		around the internal _get_source_quality_score to preserve the public API used by endpoints."""
		try:
			base = self._get_source_quality_score(source)
			# Small adjustment based on timeframe (older timeframes reduce confidence slightly)
			adjustment = max(0.0, 1.0 - (max(1, timeframe_days) / 365.0) * 0.1)
			return round(float(base) * adjustment, 2)
		except Exception:
			return float(self._get_source_quality_score(source))
