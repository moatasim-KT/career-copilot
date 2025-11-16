"""
Consolidated Job Management Service

This service consolidates job_service.py, job_scraping_service.py, job_recommendation_service.py,
job_ingestion_service.py, and job_deduplication_service.py into a single comprehensive
job management system that handles CRUD operations, job processing, scraping coordination,
recommendations, deduplication, and user notifications.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import feedparser
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.celery import celery_app
from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.email_service import EmailService
from app.services.job_deduplication_service import JobDeduplicationService
from app.services.notification_service import NotificationService
from app.services.quota_manager import QuotaManager
from app.services.rss_feed_service import RSSFeedService
from app.services.scraping import ScraperManager, ScrapingConfig
from app.services.skill_matching_service import SkillMatchingService
from app.utils.datetime import utc_now
from celery import current_task

logger = get_logger(__name__)
settings = get_settings()


class JobManagementSystem:
	"""Unified job management system that handles all job-related operations.

	This class consolidates functionality from:
	- JobService: Core CRUD operations
	- JobScrapingService: Multi-source job scraping and aggregation
	- JobRecommendationService: Personalized job recommendations and matching
	- JobIngestionService: User-specific job ingestion coordination
	- JobDeduplicationService: Advanced deduplication with fuzzy matching
	"""

	def __init__(self, db: Session):
		"""Initializes the JobManagementSystem.

		Args:
		    db: The SQLAlchemy database session.
		"""
		self.db = db
		self.settings = settings

		# Core services
		self.notification = EmailService()
		self.deduplication_service = JobDeduplicationService(db)
		self.notification_service = NotificationService()
		self.skill_matcher = SkillMatchingService()
		self.quota_manager = QuotaManager()
		self.scraper_manager: Optional[ScraperManager] = None

		# API configurations for scraping
		self.apis: Dict[str, Dict[str, Any]] = {
			"adzuna": {
				"enabled": bool(getattr(settings, "adzuna_app_id", None) and getattr(settings, "adzuna_app_key", None)),
				"base_url": "https://api.adzuna.com/v1/api/jobs",
				"app_id": getattr(settings, "adzuna_app_id", None),
				"app_key": getattr(settings, "adzuna_app_key", None),
			},
			"github": {
				"enabled": bool(getattr(settings, "github_api_token", None)),
				"base_url": "https://api.github.com/search/issues",
				"token": getattr(settings, "github_api_token", None),
			},
			"weworkremotely": {"enabled": True, "base_url": "https://weworkremotely.com/categories/remote-programming-jobs.rss"},
			"stackoverflow": {"enabled": True, "base_url": "https://stackoverflow.com/jobs/feed"},
			"usajobs": {"enabled": True, "base_url": "https://data.usajobs.gov/api/search"},
			"remoteok": {"enabled": True, "base_url": "https://remoteok.io/api"},
		}

		# Rate limiting and quota management
		self.api_quotas: Dict[str, Any] = {}
		self.last_request_times: Dict[str, datetime] = {}

	# Scraping Infrastructure (from JobScrapingService)

	def _get_scraper_manager(self) -> ScraperManager:
		"""Initialize and return the ScraperManager for job scraping."""
		if not self.scraper_manager:
			config = ScrapingConfig(
				max_results_per_site=settings.SCRAPING_MAX_RESULTS_PER_SITE,
				max_concurrent_scrapers=settings.SCRAPING_MAX_CONCURRENT,
				enable_indeed=settings.SCRAPING_ENABLE_INDEED,
				enable_linkedin=settings.SCRAPING_ENABLE_LINKEDIN,
				enable_arbeitnow=getattr(settings, "SCRAPING_ENABLE_ARBEITNOW", True),
				enable_berlinstartupjobs=getattr(settings, "SCRAPING_ENABLE_BERLINSTARTUPJOBS", True),
				enable_relocateme=getattr(settings, "SCRAPING_ENABLE_RELOCATEME", True),
				enable_eures=getattr(settings, "SCRAPING_ENABLE_EURES", True),
				enable_landingjobs=getattr(settings, "SCRAPING_ENABLE_LANDINGJOBS", True),
				enable_eutechjobs=getattr(settings, "SCRAPING_ENABLE_EUTECHJOBS", True),
				enable_eurotechjobs=getattr(settings, "SCRAPING_ENABLE_EUROTECHJOBS", True),
				enable_aijobsnet=getattr(settings, "SCRAPING_ENABLE_AIJOBSNET", True),
				enable_datacareer=getattr(settings, "SCRAPING_ENABLE_DATACAREER", True),
				enable_firecrawl=getattr(settings, "SCRAPING_ENABLE_FIRECRAWL", True),
				enable_eu_company_playwright=getattr(settings, "SCRAPING_ENABLE_EU_PLAYWRIGHT", False),
				rate_limit_min_delay=settings.SCRAPING_RATE_LIMIT_MIN,
				rate_limit_max_delay=settings.SCRAPING_RATE_LIMIT_MAX,
				deduplication_enabled=True,
			)
			self.scraper_manager = ScraperManager(config)
			logger.info(
				"✅ Scraper manager initialized with %d scrapers including EU visa-sponsorship sources and Firecrawl",
				len(self.scraper_manager.get_available_scrapers()),
			)
		return self.scraper_manager

	async def scrape_jobs(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Manual job scraping method - uses ScraperManager first, then legacy scrapers as fallback.

		Args:
		    user_preferences: User preferences for job search (skills, locations, remote, etc.)

		Returns:
		    List of scraped job dictionaries
		"""
		all_jobs: List[Dict[str, Any]] = []

		# PRIORITY 1: Use ScraperManager with working scrapers
		try:
			self._get_scraper_manager()
			search_params = {
				"keywords": user_preferences.get("skills", []),
				"locations": user_preferences.get("locations", []),
				"remote": user_preferences.get("remote", True),
			}
			max_jobs = user_preferences.get("max_jobs", 100)

			logger.info("🔍 Using ScraperManager to fetch jobs from working sources...")
			scraper_jobs = await self._ingest_from_scrapers(search_params, max_jobs)
			if scraper_jobs:
				# Convert Pydantic models to dicts
				for job in scraper_jobs:
					if hasattr(job, "model_dump"):  # Pydantic v2
						all_jobs.append(job.model_dump())
					elif hasattr(job, "dict"):  # Pydantic v1
						all_jobs.append(job.dict())
					elif isinstance(job, dict):
						all_jobs.append(job)
				logger.info(f"✅ ScraperManager found {len(scraper_jobs)} jobs")
		except Exception as e:
			logger.error(f"Error using ScraperManager: {e!r}")

		# PRIORITY 2: Use legacy scrapers if ScraperManager didn't find enough
		if len(all_jobs) < 50:
			logger.info("Using legacy scrapers as fallback...")
			tasks: List[asyncio.Future] = []
			if self.apis["adzuna"]["enabled"]:
				tasks.append(self._scrape_adzuna(user_preferences))
			if self.apis["remoteok"]["enabled"]:
				tasks.append(self._scrape_remoteok(user_preferences))

			if tasks:
				results = await asyncio.gather(*tasks, return_exceptions=True)
				for result in results:
					if isinstance(result, Exception):
						logger.error("Error in job scraping: %r", result)
						continue
					all_jobs.extend(result)

		logger.info(f"Total jobs scraped: {len(all_jobs)}")
		return all_jobs

	async def _ingest_from_scrapers(self, search_params: Dict[str, Any], max_jobs: int) -> List[Any]:
		"""Ingest jobs using the ScraperManager."""
		scraper_manager = self._get_scraper_manager()
		return await scraper_manager.scrape_all_sources(search_params, max_jobs)

	# Individual source scrapers
	async def _scrape_adzuna(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape jobs from Adzuna API."""
		try:
			async with aiohttp.ClientSession() as session:
				params = {
					"app_id": self.apis["adzuna"]["app_id"],
					"app_key": self.apis["adzuna"]["app_key"],
					"what": " ".join(preferences.get("skills", [])),
					"where": (preferences.get("locations") or [""])[0],
					"max_days_old": 30,
					"results_per_page": 50,
				}
				url = f"{self.apis['adzuna']['base_url']}/gb/search/1"
				async with session.get(url, params=params) as resp:
					if resp.status == 200:
						data = await resp.json()
						return [self._normalize_adzuna_job(j) for j in data.get("results", [])]
					logger.error("Adzuna API error: %s", resp.status)
		except Exception as e:
			logger.error("Error scraping from Adzuna: %r", e)
		return []

	async def _scrape_remoteok(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape jobs from RemoteOK API."""
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["remoteok"]["base_url"]
				async with session.get(url) as resp:
					if resp.status == 200:
						jobs = await resp.json()
						return [self._normalize_remoteok_job(job) for job in jobs if job.get("position")]
		except Exception as e:
			logger.error("Error scraping from RemoteOK: %r", e)
		return []

	# Job normalization methods
	def _normalize_adzuna_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize Adzuna job data to standard format."""
		return {
			"title": job.get("title", ""),
			"company": job.get("company", {}).get("display_name", ""),
			"location": job.get("location", {}).get("display_name", ""),
			"description": job.get("description", ""),
			"url": job.get("redirect_url", ""),
			"source": "adzuna",
			"posted_date": job.get("created"),
			"salary_min": job.get("salary_min"),
			"salary_max": job.get("salary_max"),
		}

	def _normalize_remoteok_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize RemoteOK job data to standard format."""
		return {
			"title": job_data.get("position", ""),
			"company": job_data.get("company", ""),
			"location": job_data.get("location", ""),
			"description": job_data.get("description", ""),
			"url": job_data.get("url", ""),
			"source": "remoteok",
			"posted_date": job_data.get("date"),
			"salary_min": None,
			"salary_max": None,
		}

	# Job Ingestion Methods (from JobIngestionService)

	def ingest_jobs_for_user(self, user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
		"""Scrape and store jobs for a single user.

		Args:
			user_id: The ID of the user to ingest jobs for
			max_jobs: Maximum number of jobs to save

		Returns:
			Summary dictionary with jobs_found, jobs_saved, duplicates_filtered, errors, processing_time
		"""
		start = utc_now()
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

			# Build preferences from user record
			skills = user.skills or []
			locations = user.preferred_locations or []
			experience = getattr(user, "experience_level", None)

			prefs = {
				"skills": skills,
				"locations": locations or ["Remote"],
				"experience_level": experience,
				"job_types": getattr(user, "preferred_job_types", []) or [],
				"remote_option": getattr(user, "remote_option", None) or "remote",
				"max_jobs": max_jobs,
			}

			# Scrape jobs synchronously
			jobs = self._scrape_sync(prefs)
			result["jobs_found"] = len(jobs)

			saved = 0
			for job_data in jobs[:max_jobs]:
				try:
					# Basic deduplication check
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
			result["processing_time"] = (utc_now() - start).total_seconds()
			return result

		except Exception as e:
			logger.error(f"Job ingestion error for user {user_id}: {e}")
			result["errors"].append(str(e))
			result["processing_time"] = (utc_now() - start).total_seconds()
			return result

	def _scrape_sync(self, prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Helper to call async scrape_jobs synchronously without deprecated loop access."""
		import asyncio

		async def _run():
			return await self.scrape_jobs(prefs)

		try:
			loop = asyncio.get_running_loop()
		except RuntimeError:
			# No running loop in this thread; safely create a temporary one
			return asyncio.run(_run())
		else:
			# Re-use running loop (e.g., inside notebook) by enabling nested awaits
			import nest_asyncio

			nest_asyncio.apply(loop)
			return loop.run_until_complete(_run())

	# Deduplication Methods (from JobDeduplicationService)

	def normalize_company_name(self, company: str) -> str:
		"""Normalize company name for consistent deduplication."""
		return self.deduplication_service.normalize_company_name(company)

	def normalize_job_title(self, title: str) -> str:
		"""Normalize job title for consistent deduplication."""
		return self.deduplication_service.normalize_job_title(title)

	def normalize_location(self, location: str) -> str:
		"""Normalize location for consistent deduplication."""
		return self.deduplication_service.normalize_location(location)

	def create_job_fingerprint(self, title: str, company: str, location: Optional[str] = None) -> str:
		"""Create a fingerprint for job deduplication."""
		return self.deduplication_service.create_job_fingerprint(title, company, location)

	def calculate_similarity(self, str1: str, str2: str) -> float:
		"""Calculate similarity between two strings."""
		return self.deduplication_service.calculate_similarity(str1, str2)

	def are_jobs_duplicate(self, job1: Dict[str, Any], job2: Dict[str, Any], threshold: float = 0.85) -> bool:
		"""Check if two jobs are duplicates."""
		return self.deduplication_service.are_jobs_duplicate(job1, job2, threshold)

	def filter_duplicate_jobs(self, jobs: List[Dict[str, Any]], threshold: float = 0.85) -> List[Dict[str, Any]]:
		"""Filter duplicate jobs from a list."""
		return self.deduplication_service.filter_duplicate_jobs(jobs, threshold)

	def deduplicate_against_db(self, jobs: List[Dict[str, Any]], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
		"""Deduplicate jobs against existing database entries."""
		return self.deduplication_service.deduplicate_against_db(jobs, user_id)

	def bulk_deduplicate_database_jobs(self, user_id: Optional[int] = None, batch_size: int = 100) -> Dict[str, Any]:
		"""Bulk deduplicate jobs in the database."""
		return self.deduplication_service.bulk_deduplicate_database_jobs(user_id, batch_size)

	# Recommendation Methods (from JobRecommendationService)

	async def get_personalized_recommendations(
		self, user_id: int, limit: int = 10, min_score: float = 0.0, include_applied: bool = False
	) -> List[Dict[str, Any]]:
		"""Get personalized job recommendations for a user."""
		from app.services.job_recommendation_service import JobRecommendationService

		recommendation_service = JobRecommendationService(self.db)
		return await recommendation_service.get_personalized_recommendations(
			db=self.db, user_id=user_id, limit=limit, min_score=min_score, include_applied=include_applied
		)

	async def generate_recommendations(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
		"""Generate job recommendations for a user."""
		from app.services.job_recommendation_service import JobRecommendationService

		recommendation_service = JobRecommendationService(self.db)
		return await recommendation_service.generate_recommendations(user_id=user_id, limit=limit)

	async def check_job_matches_for_user(self, user: User, new_jobs: List[Job]) -> List[Dict[str, Any]]:
		"""Check new jobs against a user's profile and return matches above threshold."""
		from app.services.job_recommendation_service import JobRecommendationService

		recommendation_service = JobRecommendationService(self.db)
		return await recommendation_service.check_job_matches_for_user(user, new_jobs)

	def process_feedback(self, user_id: int, feedback_data, match_score: Optional[int] = None):
		"""Process user feedback on job recommendations."""
		from app.services.job_recommendation_service import JobRecommendationService

		recommendation_service = JobRecommendationService(self.db)
		return recommendation_service.process_feedback(user_id, feedback_data, match_score)

	def create_job(self, user_id: int, job_data: JobCreate) -> Job:
		"""Creates a new job entry in the database.

		Args:
			user_id: The ID of the user creating the job.
			job_data: The data for the new job.

		Returns:
			The newly created Job object.
		"""
		job = Job(**job_data.model_dump(), user_id=user_id)
		self.db.add(job)
		self.db.flush()  # Use flush to get ID before commit if needed elsewhere
		self.db.refresh(job)
		return job

	def update_job(self, job_id: int, job_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Job]:
		"""Updates an existing job in the database.

		Args:
			job_id: The ID of the job to update.
			job_data: A dictionary containing the fields to update.
			user_id: Optional; The ID of the user who owns the job (for authorization).

		Returns:
			The updated Job object, or None if the job was not found.
		"""
		query = self.db.query(Job).filter(Job.id == job_id)
		if user_id:
			query = query.filter(Job.user_id == user_id)

		job = query.first()
		if not job:
			return None

		for field, value in job_data.items():
			if hasattr(job, field):
				setattr(job, field, value)

		job.updated_at = utc_now()
		self.db.commit()
		self.db.refresh(job)
		return job

	def delete_job(self, job_id: int, user_id: Optional[int] = None) -> bool:
		"""Deletes a job from the database.

		Args:
			job_id: The ID of the job to delete.
			user_id: Optional; The ID of the user who owns the job (for authorization).

		Returns:
			True if the job was successfully deleted, False otherwise.
		"""
		query = self.db.query(Job).filter(Job.id == job_id)
		if user_id:
			query = query.filter(Job.user_id == user_id)

		job = query.first()
		if not job:
			return False

		self.db.delete(job)
		self.db.commit()
		return True

	def get_job(self, job_id: int, user_id: Optional[int] = None) -> Optional[Job]:
		"""Retrieves a job by ID.

		Args:
			job_id: The ID of the job to retrieve.
			user_id: Optional; The ID of the user who owns the job (for authorization).

		Returns:
			The Job object, or None if not found.
		"""
		query = self.db.query(Job).filter(Job.id == job_id)
		if user_id:
			query = query.filter(Job.user_id == user_id)
		return query.first()

	def get_job_by_unique_fields(self, user_id: int, title: str, company: str, location: Optional[str] = None) -> Optional[Job]:
		"""Retrieves a job by unique identifying fields.

		Args:
			user_id: The ID of the user.
			title: The job title.
			company: The company name.
			location: Optional location.

		Returns:
			The Job object, or None if not found.
		"""
		query = self.db.query(Job).filter(Job.user_id == user_id, Job.title == title, Job.company == company)
		if location:
			query = query.filter(Job.location == location)
		return query.first()

	def get_latest_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Job]:
		"""Retrieves the latest jobs for a user.

		Args:
			user_id: The ID of the user.
			limit: The maximum number of jobs to return.

		Returns:
			A list of Job objects.
		"""
		return self.db.query(Job).filter(Job.user_id == user_id).order_by(desc(Job.created_at)).limit(limit).all()

	def get_jobs_for_user(self, user_id: int, limit: int = 50, offset: int = 0, filters: Optional[Dict[str, Any]] = None) -> List[Job]:
		"""Retrieves jobs for a user with optional filtering.

		Args:
			user_id: The ID of the user.
			limit: The maximum number of jobs to return.
			offset: The number of jobs to skip.
			filters: Optional dictionary of filters to apply.

		Returns:
			A list of Job objects.
		"""
		query = self.db.query(Job).filter(Job.user_id == user_id)

		if filters:
			if "source" in filters:
				query = query.filter(Job.source == filters["source"])
			if "job_type" in filters:
				query = query.filter(Job.job_type == filters["job_type"])
			if "remote_option" in filters:
				query = query.filter(Job.remote_option == filters["remote_option"])
			if "company" in filters:
				query = query.filter(Job.company.ilike(f"%{filters['company']}%"))
			if "location" in filters:
				query = query.filter(Job.location.ilike(f"%{filters['location']}%"))

		return query.order_by(desc(Job.created_at)).offset(offset).limit(limit).all()

	def search_jobs(self, user_id: int, query: str, limit: int = 50, offset: int = 0) -> List[Job]:
		"""Searches for jobs by text query for a specific user.

		Args:
			user_id: The ID of the user.
			query: The search query string.
			limit: The maximum number of jobs to return.
			offset: The number of jobs to skip.

		Returns:
			A list of Job objects matching the search query.
		"""
		return (
			self.db.query(Job)
			.filter(Job.user_id == user_id, Job.title.ilike(f"%{query}%") | Job.company.ilike(f"%{query}%") | Job.description.ilike(f"%{query}%"))
			.order_by(desc(Job.created_at))
			.offset(offset)
			.limit(limit)
			.all()
		)

	def create_jobs_batch(self, user_id: int, jobs_data: List[JobCreate]) -> List[Job]:
		"""Creates multiple job entries in a single batch.

		Args:
			user_id: The ID of the user creating the jobs.
			jobs_data: A list of JobCreate objects for the new jobs.

		Returns:
			A list of the newly created Job objects.
		"""
		created_jobs = []

		for job_data in jobs_data:
			try:
				job = self.create_job(user_id, job_data)
				created_jobs.append(job)
			except Exception as e:
				logger.error(f"Error creating job in batch: {e}")
				continue

		self.db.commit()
		return created_jobs

	def update_jobs_batch(self, job_updates: List[Dict[str, Any]], user_id: Optional[int] = None) -> List[Job]:
		"""Updates multiple existing jobs in a single batch.

		Args:
			job_updates: A list of dictionaries, each containing job ID and fields to update.
			user_id: Optional; The ID of the user who owns the jobs (for authorization).

		Returns:
			A list of the updated Job objects.
		"""
		updated_jobs = []

		for update_data in job_updates:
			job_id = update_data.pop("id", None)
			if not job_id:
				continue

			job = self.update_job(job_id, update_data, user_id)
			if job:
				updated_jobs.append(job)

		return updated_jobs

	def delete_jobs_batch(self, job_ids: List[int], user_id: Optional[int] = None) -> int:
		"""Deletes multiple jobs in a single batch.

		Args:
			job_ids: A list of IDs of the jobs to delete.
			user_id: Optional; The ID of the user who owns the jobs (for authorization).

		Returns:
			The number of jobs successfully deleted.
		"""
		deleted_count = 0

		for job_id in job_ids:
			if self.delete_job(job_id, user_id):
				deleted_count += 1

		return deleted_count

	def get_job_statistics(self, user_id: int) -> Dict[str, Any]:
		"""Retrieves job statistics for a specific user.

		Args:
			user_id: The ID of the user.

		Returns:
			A dictionary containing job statistics.
		"""
		total_jobs = self.db.query(Job).filter(Job.user_id == user_id).count()

		# Jobs by source
		jobs_by_source = self.db.query(Job.source, self.db.func.count(Job.id)).filter(Job.user_id == user_id).group_by(Job.source).all()

		# Jobs by type
		jobs_by_type = self.db.query(Job.job_type, self.db.func.count(Job.id)).filter(Job.user_id == user_id).group_by(Job.job_type).all()

		# Recent jobs (last 30 days)
		from datetime import timedelta

		recent_cutoff = utc_now() - timedelta(days=30)
		recent_jobs = self.db.query(Job).filter(Job.user_id == user_id, Job.created_at >= recent_cutoff).count()

		return {"total_jobs": total_jobs, "recent_jobs": recent_jobs, "jobs_by_source": dict(jobs_by_source), "jobs_by_type": dict(jobs_by_type)}

	def validate_job_data(self, job_data: JobCreate) -> Dict[str, Any]:
		"""Validates job data before creation.

		Args:
			job_data: The JobCreate object containing job data.

		Returns:
			A dictionary indicating validity, errors, and warnings.
		"""
		errors = []
		warnings = []

		if not job_data.title or len(job_data.title.strip()) < 2:
			errors.append("Job title is required and must be at least 2 characters")
		if not job_data.company or len(job_data.company.strip()) < 2:
			errors.append("Company name is required and must be at least 2 characters")

		# Validate salary range if both min and max are provided
		if job_data.salary_min and job_data.salary_max:
			if job_data.salary_min > job_data.salary_max:
				warnings.append("Salary minimum should not be greater than salary maximum")

		return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

	def _is_valid_salary_format(self, salary_range: str) -> bool:
		"""Checks if a salary range string follows an expected format.

		Args:
			salary_range: The salary range string to validate.

		Returns:
			True if the format is valid, False otherwise.
		"""
		if not salary_range:
			return False

		import re

		patterns = [
			r"\$[\d,]+\s*-\s*\$[\d,]+",  # $50,000 - $70,000
			r"\d+k\s*-\s*\d+k",  # 50k-70k
			r"\$\d+K\s*-\s*\$\d+K",  # $50K-$70K
			r"\d+\s*-\s*\d+",  # 50000-70000
		]

		return any(re.search(pattern, salary_range, re.IGNORECASE) for pattern in patterns)


# Factory function for dependency injection
def get_job_management_system(db: Session) -> JobManagementSystem:
	"""Get JobManagementSystem instance"""
	return JobManagementSystem(db)


# Backward compatibility aliases
JobService = JobManagementSystem
UnifiedJobService = JobManagementSystem
