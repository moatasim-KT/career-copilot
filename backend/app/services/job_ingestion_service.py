"""Job ingestion service wrapper.

Provides a minimal JobIngestionService used by Celery tasks and scheduling
code. It leverages JobScrapingService to find jobs based on a user's
preferences and persists them to the database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..models.job import Job
from ..models.user import User
from .job_scraper_service import JobScraperService

logger = get_logger(__name__)


class JobIngestionService:
	def __init__(self, db: Session, settings: Any):
		self.db = db
		self.settings = settings
		self.scraper = JobScraperService(db)

	def ingest_jobs_for_user(self, user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
		"""Scrape and store jobs for a single user.

		Returns a summary dictionary with keys: jobs_found, jobs_saved,
		duplicates_filtered, errors, processing_time.
		"""
		start = datetime.now(timezone.utc)
		result: Dict[str, Any] = {
			"jobs_found": 0,
			"jobs_saved": 0,
			"duplicates_filtered": 0,
			"errors": [],
			"processing_time": 0,
		}

		try:
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				raise ValueError(f"User {user_id} not found")

			# Build simple preferences from user record
			skills = user.skills or []
			locations = user.preferred_locations or []
			experience = getattr(user, "experience_level", None)

			prefs = {
				"skills": skills,
				"locations": locations or ["Remote"],
				"experience_level": experience,
				"job_types": getattr(user, "preferred_job_types", []) or [],
				"remote_option": getattr(user, "remote_option", None) or "remote",
			}

			# Scrape jobs (async API wrapped via helper)
			jobs = self._scrape_sync(prefs)
			result["jobs_found"] = len(jobs)

			saved = 0
			for job_data in jobs[: max_jobs or 50]:
				try:
					# Basic deduplication by source_url+title
					existing = (
						self.db.query(Job)
						.filter(
							Job.user_id == user_id,
							Job.title == job_data.get("title"),
							Job.source_url == job_data.get("source_url"),
						)
						.first()
					)
					if existing:
						result["duplicates_filtered"] += 1
						continue

					job = Job(
						user_id=user_id,
						company=(job_data.get("company") or job_data.get("company_name") or "Unknown"),
						title=job_data.get("title") or "Untitled",
						location=job_data.get("location") or "",
						description=job_data.get("description") or "",
						salary_range=job_data.get("salary_range"),
						salary_min=job_data.get("salary_min"),
						salary_max=job_data.get("salary_max"),
						job_type=job_data.get("job_type"),
						remote_option=(job_data.get("remote_option") or "remote"),
						tech_stack=job_data.get("tech_stack"),
						responsibilities=job_data.get("responsibilities"),
						documents_required=job_data.get("documents_required"),
						application_url=job_data.get("application_url"),
						source_url=job_data.get("source_url"),
						source=job_data.get("source") or "scraped",
					)
					self.db.add(job)
					saved += 1
				except Exception as inner:
					logger.warning(f"Failed to save job for user {user_id}: {inner}")
					result["errors"].append(str(inner))

			self.db.commit()
			result["jobs_saved"] = saved
			result["processing_time"] = (datetime.now(timezone.utc) - start).total_seconds()
			return result

		except Exception as e:
			logger.error(f"Job ingestion error for user {user_id}: {e}")
			result["errors"].append(str(e))
			result["processing_time"] = (datetime.now(timezone.utc) - start).total_seconds()
			return result

	def _scrape_sync(self, prefs: Dict[str, Any]):
		"""Helper to call async scrape_jobs synchronously for simplicity."""
		import asyncio

		async def _run():
			return await self.scraper.scrape_jobs(prefs)

		return asyncio.get_event_loop().run_until_complete(_run())
