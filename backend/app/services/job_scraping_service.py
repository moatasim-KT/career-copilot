"""
class None  # JobAPIService: pass
from .job_api_service import None  # JobAPIService

class None  # JobAPIService: pass


Consolidated Job Scraping Service

This service consolidates multiple job scraping and ingestion modules:
- job_scraper_service.py: Job scraping from multiple sources
- job_scraper.py: Core scraping functionality
- job_ingestion_service.py: Job ingestion and processing
- job_ingestion.py: Celery tasks for job ingestion
- job_api_service.py: External API integration

Provides unified interface for job scraping, data ingestion, and normalization.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import feedparser
from app.celery import celery_app
from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate
from app.services.notification_service import NotificationService
from app.services.quota_manager import QuotaManager
from app.services.rss_feed_service import RSSFeedService
from app.services.scraping import ScraperManager, ScrapingConfig
from app.services.skill_matching_service import SkillMatchingService
from celery import current_task
from sqlalchemy.orm import Session

logger = get_logger(__name__)
settings = get_settings()


class JobScrapingService:
	"""
	Unified job scraping service that handles:
	- Multi-source job scraping
	- Data ingestion and normalization
	- API integration
	- Celery task coordination
	"""

	def __init__(self, db: Session = None):
		self.db = db
		self.settings = settings
		self.notification_service = NotificationService()
		self.skill_matcher = SkillMatchingService()
		self.quota_manager = QuotaManager()
		self.scraper_manager = None

		# API configurations - use getattr to handle optional attributes gracefully
		self.apis = {
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
			"weworkremotely": {
				"enabled": True,  # RSS feed doesn't require authentication
				"base_url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
			},
			"stackoverflow": {
				"enabled": True,  # RSS feed doesn't require authentication
				"base_url": "https://stackoverflow.com/jobs/feed",
			},
			"usajobs": {
				"enabled": True,  # Free government API
				"base_url": "https://data.usajobs.gov/api/search",
			},
			"remoteok": {
				"enabled": True,  # Public API
				"base_url": "https://remoteok.io/api",
			},
		}

		# Rate limiting and quota management
		self.api_quotas = {}
		self.last_request_times = {}

	def _get_scraper_manager(self) -> ScraperManager:
		"""Get or create scraper manager"""
		if not self.scraper_manager:
			config = ScrapingConfig(
				max_results_per_site=settings.SCRAPING_MAX_RESULTS_PER_SITE,
				max_concurrent_scrapers=settings.SCRAPING_MAX_CONCURRENT,
				enable_indeed=settings.SCRAPING_ENABLE_INDEED,
				enable_linkedin=settings.SCRAPING_ENABLE_LINKEDIN,
				rate_limit_min_delay=settings.SCRAPING_RATE_LIMIT_MIN,
				rate_limit_max_delay=settings.SCRAPING_RATE_LIMIT_MAX,
				deduplication_enabled=True,
			)
			self.scraper_manager = ScraperManager(config)
		return self.scraper_manager

	# Main Scraping Interface

	async def scrape_jobs(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Scrape jobs from all configured sources.

		Args:
		    user_preferences: Dictionary containing user preferences
		        - skills: List of skills
		        - locations: List of preferred locations
		        - experience_level: Experience level
		        - job_types: List of preferred job types
		        - remote_option: Remote work preference

		Returns:
		    List of job dictionaries
		"""
		tasks = []

		# Create tasks for each enabled API
		if self.apis["adzuna"]["enabled"]:
			tasks.append(self._scrape_adzuna(user_preferences))
		if self.apis["github"]["enabled"]:
			tasks.append(self._scrape_github_issues(user_preferences))
		if self.apis["usajobs"]["enabled"]:
			tasks.append(self._scrape_usajobs(user_preferences))
		if self.apis["remoteok"]["enabled"]:
			tasks.append(self._scrape_remoteok(user_preferences))

		# RSS feeds
		tasks.append(self._scrape_weworkremotely(user_preferences))
		tasks.append(self._scrape_stackoverflow(user_preferences))

		# Run all scraping tasks concurrently
		results = await asyncio.gather(*tasks, return_exceptions=True)

		# Combine and normalize results
		all_jobs = []
		for result in results:
			if isinstance(result, Exception):
				logger.error(f"Error in job scraping: {result!s}")
				continue
			all_jobs.extend(result)

		return all_jobs

	# Individual Source Scrapers

	async def _scrape_adzuna(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape jobs from Adzuna API."""
		try:
			async with aiohttp.ClientSession() as session:
				params = {
					"app_id": self.apis["adzuna"]["app_id"],
					"app_key": self.apis["adzuna"]["app_key"],
					"what": " ".join(preferences["skills"]),
					"where": preferences["locations"][0],  # Primary location
					"max_days_old": 30,
					"results_per_page": 50,
				}

				url = f"{self.apis['adzuna']['base_url']}/gb/search/1"
				async with session.get(url, params=params) as response:
					if response.status == 200:
						data = await response.json()
						return [self._normalize_adzuna_job(job) for job in data.get("results", [])]
					else:
						logger.error(f"Adzuna API error: {response.status}")
						return []

		except Exception as e:
			logger.error(f"Error scraping from Adzuna: {e!s}")
			return []

	async def _scrape_github_issues(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape job postings from GitHub issues."""
		try:
			async with aiohttp.ClientSession() as session:
				headers = {"Authorization": f"token {self.apis['github']['token']}", "Accept": "application/vnd.github.v3+json"}

				skills_query = " OR ".join(preferences["skills"])
				query = f"label:job type:issue state:open ({skills_query})"

				params = {"q": query, "sort": "created", "order": "desc", "per_page": 50}

				url = self.apis["github"]["base_url"]
				async with session.get(url, headers=headers, params=params) as response:
					if response.status == 200:
						data = await response.json()
						return [self._normalize_github_issue(issue) for issue in data.get("items", [])]
					else:
						logger.error(f"GitHub API error: {response.status}")
						return []

		except Exception as e:
			logger.error(f"Error scraping from GitHub: {e!s}")
			return []

	async def _scrape_usajobs(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape jobs from USAJobs API."""
		try:
			async with aiohttp.ClientSession() as session:
				params = {
					"Keyword": " ".join(preferences["skills"]),
					"LocationName": preferences["locations"][0],
					"ResultsPerPage": 50,
					"SortField": "OpenDate",
					"SortDirection": "Desc",
				}

				headers = {"Host": "data.usajobs.gov", "User-Agent": "career-copilot@example.com"}

				url = self.apis["usajobs"]["base_url"]
				async with session.get(url, params=params, headers=headers) as response:
					if response.status == 200:
						data = await response.json()
						if "SearchResult" in data and "SearchResultItems" in data["SearchResult"]:
							return [self._normalize_usajobs_job(item) for item in data["SearchResult"]["SearchResultItems"]]
					else:
						logger.error(f"USAJobs API error: {response.status}")
					return []

		except Exception as e:
			logger.error(f"Error scraping from USAJobs: {e!s}")
			return []

	async def _scrape_remoteok(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape remote jobs from RemoteOK API."""
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["remoteok"]["base_url"]
				async with session.get(url) as response:
					if response.status == 200:
						data = await response.json()
						if isinstance(data, list) and len(data) > 1:
							# Filter jobs by keywords
							keyword_list = [skill.lower() for skill in preferences["skills"]]
							filtered_jobs = []

							for job_data in data[1:]:  # First item is metadata
								if self._matches_keywords_remoteok(job_data, keyword_list):
									normalized_job = self._normalize_remoteok_job(job_data)
									if normalized_job:
										filtered_jobs.append(normalized_job)

							return filtered_jobs[:50]  # Limit results
					else:
						logger.error(f"RemoteOK API error: {response.status}")
					return []

		except Exception as e:
			logger.error(f"Error scraping from RemoteOK: {e!s}")
			return []

	async def _scrape_weworkremotely(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape jobs from WeWorkRemotely RSS feed."""
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["weworkremotely"]["base_url"]
				async with session.get(url) as response:
					if response.status == 200:
						content = await response.text()
						feed = feedparser.parse(content)
						return [self._normalize_wwr_job(entry) for entry in feed.entries]
					else:
						logger.error(f"WWR feed error: {response.status}")
						return []

		except Exception as e:
			logger.error(f"Error scraping from WeWorkRemotely: {e!s}")
			return []

	async def _scrape_stackoverflow(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Scrape jobs from Stack Overflow RSS feed."""
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["stackoverflow"]["base_url"]
				async with session.get(url) as response:
					if response.status == 200:
						content = await response.text()
						feed = feedparser.parse(content)
						return [self._normalize_stackoverflow_job(entry) for entry in feed.entries]
					else:
						logger.error(f"Stack Overflow feed error: {response.status}")
						return []

		except Exception as e:
			logger.error(f"Error scraping from Stack Overflow: {e!s}")
			return []

	# Data Normalization Methods

	def _normalize_adzuna_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize Adzuna job data to common format."""
		return {
			"title": job.get("title"),
			"company": job.get("company", {}).get("display_name"),
			"location": job.get("location", {}).get("display_name"),
			"description": job.get("description"),
			"url": job.get("redirect_url"),
			"salary_min": job.get("salary_min"),
			"salary_max": job.get("salary_max"),
			"source": "adzuna",
			"remote": "remote" in job.get("description", "").lower(),
			"posted_at": job.get("created"),
			"original_data": job,
		}

	def _normalize_github_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize GitHub issue job posting to common format."""
		return {
			"title": issue.get("title"),
			"company": self._extract_company_from_issue(issue),
			"location": self._extract_location_from_issue(issue),
			"description": issue.get("body"),
			"url": issue.get("html_url"),
			"salary_min": None,
			"salary_max": None,
			"source": "github",
			"remote": "remote" in issue.get("body", "").lower(),
			"posted_at": issue.get("created_at"),
			"original_data": issue,
		}

	def _normalize_usajobs_job(self, item: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize USAJobs job data to common format."""
		job_data = item.get("MatchedObjectDescriptor", {})

		return {
			"title": job_data.get("PositionTitle", ""),
			"company": job_data.get("OrganizationName", "U.S. Government"),
			"location": self._extract_usajobs_location(job_data),
			"description": job_data.get("QualificationSummary", ""),
			"url": job_data.get("PositionURI", ""),
			"salary_min": self._extract_usajobs_salary(job_data).get("min"),
			"salary_max": self._extract_usajobs_salary(job_data).get("max"),
			"source": "usajobs",
			"remote": False,  # Government jobs are typically on-site
			"posted_at": job_data.get("PublicationStartDate"),
			"original_data": item,
		}

	def _normalize_remoteok_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize RemoteOK job data to common format."""
		return {
			"title": job_data.get("position", ""),
			"company": job_data.get("company", ""),
			"location": "Remote",
			"description": job_data.get("description", ""),
			"url": job_data.get("url", ""),
			"salary_min": job_data.get("salary_min"),
			"salary_max": job_data.get("salary_max"),
			"source": "remoteok",
			"remote": True,
			"posted_at": job_data.get("date"),
			"original_data": job_data,
		}

	def _normalize_wwr_job(self, entry: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize WeWorkRemotely job to common format."""
		return {
			"title": entry.get("title"),
			"company": self._extract_company_from_wwr(entry),
			"location": "Remote",
			"description": entry.get("description"),
			"url": entry.get("link"),
			"salary_min": None,
			"salary_max": None,
			"source": "weworkremotely",
			"remote": True,
			"posted_at": entry.get("published"),
			"original_data": entry,
		}

	def _normalize_stackoverflow_job(self, entry: Dict[str, Any]) -> Dict[str, Any]:
		"""Normalize Stack Overflow job to common format."""
		return {
			"title": entry.get("title"),
			"company": self._extract_company_from_so(entry),
			"location": self._extract_location_from_so(entry),
			"description": entry.get("description"),
			"url": entry.get("link"),
			"salary_min": None,
			"salary_max": None,
			"source": "stackoverflow",
			"remote": "remote" in entry.get("description", "").lower(),
			"posted_at": entry.get("published"),
			"original_data": entry,
		}

	# Helper Methods for Data Extraction

	def _extract_company_from_issue(self, issue: Dict[str, Any]) -> str:
		"""Extract company name from GitHub issue."""
		title = issue.get("title", "").lower()
		body = issue.get("body", "").lower()

		patterns = ["at", "with", "for", "@"]

		for pattern in patterns:
			if pattern in title:
				parts = title.split(pattern)
				if len(parts) > 1:
					return parts[1].strip().title()

		return issue.get("repository", {}).get("owner", {}).get("login", "Unknown")

	def _extract_location_from_issue(self, issue: Dict[str, Any]) -> str:
		"""Extract location from GitHub issue."""
		body = issue.get("body", "").lower()

		patterns = ["location:", "based in:", "position location:"]

		for pattern in patterns:
			if pattern in body:
				idx = body.find(pattern)
				end_idx = body.find("\n", idx)
				if end_idx == -1:
					end_idx = len(body)
				return body[idx + len(pattern) : end_idx].strip().title()
		return "Remote/Unspecified"

	def _extract_usajobs_location(self, job_data: Dict[str, Any]) -> str:
		"""Extract location from USAJobs data."""
		locations = job_data.get("PositionLocation", [])
		if locations and isinstance(locations, list):
			location = locations[0]
			city = location.get("CityName", "")
			state = location.get("StateCode", "")
			return f"{city}, {state}".strip(", ")
		return ""

	def _extract_usajobs_salary(self, job_data: Dict[str, Any]) -> Dict[str, Optional[int]]:
		"""Extract salary from USAJobs data."""
		salary_info = {"min": None, "max": None}

		remuneration = job_data.get("PositionRemuneration", [])
		if remuneration and isinstance(remuneration, list):
			salary_data = remuneration[0]
			min_range = salary_data.get("MinimumRange")
			max_range = salary_data.get("MaximumRange")

			try:
				if min_range:
					salary_info["min"] = int(float(min_range))
				if max_range:
					salary_info["max"] = int(float(max_range))
			except (ValueError, TypeError):
				pass

		return salary_info

	def _extract_company_from_wwr(self, entry: Dict[str, Any]) -> str:
		"""Extract company name from WeWorkRemotely entry."""
		title = entry.get("title", "")
		if ":" in title:
			return title.split(":")[0].strip()
		return "Unknown"

	def _extract_company_from_so(self, entry: Dict[str, Any]) -> str:
		"""Extract company name from Stack Overflow entry."""
		title = entry.get("title", "")
		if "at" in title:
			return title.split("at")[1].strip()
		return "Unknown"

	def _extract_location_from_so(self, entry: Dict[str, Any]) -> str:
		"""Extract location from Stack Overflow entry."""
		title = entry.get("title", "")
		if "(" in title and ")" in title:
			return title[title.find("(") + 1 : title.find(")")].strip()
		return "Remote/Unspecified"

	def _matches_keywords_remoteok(self, job_data: Dict[str, Any], keywords: List[str]) -> bool:
		"""Check if RemoteOK job matches keywords."""
		if not keywords:
			return True

		searchable_text = f"{job_data.get('position', '')} {job_data.get('company', '')} {job_data.get('description', '')}".lower()

		return any(keyword in searchable_text for keyword in keywords)

	# Job Processing and Ingestion

	async def ingest_jobs_for_user(self, user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
		"""Ingest jobs for a specific user based on their preferences"""
		try:
			# Get user and preferences
			user = self.db.query(User).filter(User.id == user_id).first()
			if not user:
				raise ValueError(f"User {user_id} not found")

			logger.info(f"Starting multi-source job ingestion for user {user_id}")

			# Extract search parameters from user profile
			search_params = self._extract_search_params(user)

			# Track ingestion results
			ingestion_results = {
				"user_id": user_id,
				"started_at": datetime.now(timezone.utc),
				"search_params": search_params,
				"sources_used": [],
				"jobs_by_source": {},
				"jobs_found": 0,
				"jobs_saved": 0,
				"duplicates_filtered": 0,
				"errors": [],
			}

			# Get all jobs from multiple sources
			all_jobs = []

			# Source 1: RSS Feeds
			rss_jobs = await self._ingest_from_rss_feeds(search_params, max_jobs // 4)
			if rss_jobs:
				all_jobs.extend(rss_jobs)
				ingestion_results["sources_used"].append("rss_feeds")
				ingestion_results["jobs_by_source"]["rss_feeds"] = len(rss_jobs)

			# Source 2: Job APIs
			api_jobs = await self._ingest_from_apis(search_params, max_jobs // 4)
			if api_jobs:
				all_jobs.extend(api_jobs)
				ingestion_results["sources_used"].append("job_apis")
				ingestion_results["jobs_by_source"]["job_apis"] = len(api_jobs)

			# Source 3: Web Scraping (fallback)
			if len(all_jobs) < max_jobs // 2:
				scraper_jobs = await self._ingest_from_scrapers(search_params, max_jobs // 2)
				if scraper_jobs:
					all_jobs.extend(scraper_jobs)
					ingestion_results["sources_used"].append("web_scraping")
					ingestion_results["jobs_by_source"]["web_scraping"] = len(scraper_jobs)

			ingestion_results["jobs_found"] = len(all_jobs)

			# Filter out jobs that already exist for this user
			new_jobs = await self._filter_existing_jobs(user_id, all_jobs)
			ingestion_results["duplicates_filtered"] = len(all_jobs) - len(new_jobs)

			# Save new jobs to database
			saved_jobs = []
			for job_data in new_jobs:
				try:
					# Convert to JobCreate and save
					job_create = self._convert_to_job_create(job_data, user_id)
					job = Job(**job_create.model_dump(), user_id=user_id)
					self.db.add(job)
					self.db.flush()

					# Calculate match score
					if hasattr(self.skill_matcher, "calculate_match_score"):
						match_score = await self.skill_matcher.calculate_match_score(job, user_id)
						job.match_score = match_score

					saved_jobs.append(job)

				except Exception as e:
					error_msg = f"Error saving job '{job_data.get('title', 'Unknown')}': {e!s}"
					logger.error(error_msg)
					ingestion_results["errors"].append(error_msg)

			self.db.commit()
			ingestion_results["jobs_saved"] = len(saved_jobs)
			ingestion_results["completed_at"] = datetime.now(timezone.utc)

			logger.info(
				f"Multi-source job ingestion completed for user {user_id}: "
				f"{ingestion_results['jobs_saved']} new jobs saved from "
				f"{len(ingestion_results['sources_used'])} sources"
			)

			return ingestion_results

		except Exception as e:
			logger.error(f"Job ingestion failed for user {user_id}: {e!s}")
			raise

	def _extract_search_params(self, user: User) -> Dict[str, List[str]]:
		"""Extract search parameters from user profile"""
		profile = user.profile or {}

		# Default keywords based on user skills or generic terms
		keywords = []

		# Use user skills as keywords
		user_skills = profile.get("skills", [])
		if user_skills:
			keywords.extend(user_skills[:3])  # Use top 3 skills

		# Add job titles from preferences
		preferred_titles = profile.get("preferences", {}).get("job_titles", [])
		keywords.extend(preferred_titles)

		# Default keywords if none specified
		if not keywords:
			keywords = ["software engineer", "developer", "programmer"]

		# Locations
		locations = []

		# Use preferred locations
		preferred_locations = profile.get("locations", [])
		locations.extend(preferred_locations)

		# Add remote as an option
		if not any("remote" in loc.lower() for loc in locations):
			locations.append("remote")

		# Default location if none specified
		if not locations:
			locations = ["remote", "united states"]

		return {
			"keywords": keywords[:5],  # Limit to 5 keywords
			"locations": locations[:3],  # Limit to 3 locations
		}

	async def _filter_existing_jobs(self, user_id: int, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Filter out jobs that already exist for the user"""
		if not jobs:
			return []

		# Get existing jobs for user from last 30 days
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
		existing_jobs = self.db.query(Job).filter(Job.user_id == user_id, Job.created_at >= cutoff_date).all()

		# Create set of existing job keys
		existing_keys = set()
		for job in existing_jobs:
			key = self._create_job_key(job.title, job.company, job.location)
			existing_keys.add(key)

		# Filter new jobs
		new_jobs = []
		for job in jobs:
			key = self._create_job_key(job.get("title", ""), job.get("company", ""), job.get("location", ""))
			if key not in existing_keys:
				new_jobs.append(job)

		logger.info(f"Filtered {len(jobs) - len(new_jobs)} existing jobs")
		return new_jobs

	def _create_job_key(self, title: str, company: str, location: str = None) -> str:
		"""Create a normalized key for job comparison"""
		# Normalize text
		title = " ".join(title.lower().strip().split()) if title else ""
		company = " ".join(company.lower().strip().split()) if company else ""
		location = " ".join(location.lower().strip().split()) if location else ""

		return f"{title}|{company}|{location}"

	def _convert_to_job_create(self, job_data: Dict[str, Any], user_id: int) -> JobCreate:
		"""Convert scraped job data to JobCreate schema"""
		return JobCreate(
			title=job_data.get("title", "Unknown Position"),
			company=job_data.get("company", "Unknown Company"),
			location=job_data.get("location", "Unknown Location"),
			description=job_data.get("description", ""),
			salary_range=self._format_salary_range(job_data.get("salary_min"), job_data.get("salary_max")),
			source=job_data.get("source", "unknown"),
			application_url=job_data.get("url", ""),
			remote_option=job_data.get("remote", False),
			posted_at=job_data.get("posted_at"),
		)

	def _format_salary_range(self, salary_min: Optional[int], salary_max: Optional[int]) -> Optional[str]:
		"""Format salary range from min/max values"""
		if salary_min and salary_max:
			return f"${salary_min:,} - ${salary_max:,}"
		elif salary_min:
			return f"${salary_min:,}+"
		elif salary_max:
			return f"Up to ${salary_max:,}"
		return None

	# Placeholder methods for RSS and API integration
	async def _ingest_from_rss_feeds(self, search_params: Dict[str, List[str]], max_jobs: int) -> List[JobCreate]:
		"""Ingest jobs from RSS feeds"""
		# Placeholder - would integrate with RSSFeedService
		return []

	async def _ingest_from_apis(self, search_params: Dict[str, List[str]], max_jobs: int) -> List[JobCreate]:
		"""Ingest jobs from external APIs"""
		# Use the scraping methods we already implemented
		user_preferences = {"skills": search_params.get("keywords", []), "locations": search_params.get("locations", [])}

		scraped_jobs = await self.scrape_jobs(user_preferences)
		return scraped_jobs[:max_jobs]

	async def _ingest_from_scrapers(self, search_params: Dict[str, List[str]], max_jobs: int) -> List[JobCreate]:
		"""Ingest jobs from web scrapers"""
		# Placeholder - would integrate with ScraperManager
		return []

	# Celery Tasks

	@celery_app.task(bind=True, name="app.services.job_scraping_service.ingest_jobs")
	def ingest_jobs_task(self, user_ids: List[int] = None, max_jobs_per_user: int = 50) -> Dict[str, Any]:
		"""Celery task to ingest jobs for users"""
		task_id = current_task.request.id
		logger.info(f"Starting job ingestion task {task_id}")

		results = {"task_id": task_id, "users_processed": 0, "total_jobs_found": 0, "total_jobs_saved": 0, "errors": [], "user_results": []}

		try:
			# Get database session
			db: Session = next(get_db())

			try:
				# Get users to process
				if user_ids:
					users = db.query(User).filter(User.id.in_(user_ids)).all()
				else:
					# Get all active users
					cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
					users = db.query(User).filter(User.last_active >= cutoff_date).all()

				logger.info(f"Processing job ingestion for {len(users)} users")

				# Process each user
				scraping_service = JobScrapingService(db)

				for i, user in enumerate(users):
					try:
						# Update task progress
						current_task.update_state(
							state="PROGRESS", meta={"current": i + 1, "total": len(users), "status": f"Processing user {user.id}"}
						)

						logger.info(f"Processing job ingestion for user {user.id}")

						# Perform job ingestion for user
						import asyncio

						loop = asyncio.new_event_loop()
						asyncio.set_event_loop(loop)
						try:
							user_result = loop.run_until_complete(scraping_service.ingest_jobs_for_user(user.id, max_jobs_per_user))
						finally:
							loop.close()

						# Update results
						results["users_processed"] += 1
						results["total_jobs_found"] += user_result["jobs_found"]
						results["total_jobs_saved"] += user_result["jobs_saved"]
						results["user_results"].append(
							{
								"user_id": user.id,
								"jobs_found": user_result["jobs_found"],
								"jobs_saved": user_result["jobs_saved"],
								"duplicates_filtered": user_result["duplicates_filtered"],
								"errors": user_result["errors"],
							}
						)

						# Add user errors to overall errors
						if user_result["errors"]:
							results["errors"].extend([f"User {user.id}: {error}" for error in user_result["errors"]])

						logger.info(f"Completed job ingestion for user {user.id}: {user_result['jobs_saved']} jobs saved")

					except Exception as e:
						error_msg = f"Error processing user {user.id}: {e!s}"
						logger.error(error_msg)
						results["errors"].append(error_msg)

				logger.info(f"Job ingestion task completed: {results['users_processed']} users processed, {results['total_jobs_saved']} jobs saved")

				return results

			finally:
				db.close()

		except Exception as e:
			error_msg = f"Job ingestion task failed: {e!s}"
			logger.error(error_msg)
			results["errors"].append(error_msg)
			return results

	async def get_ingestion_stats(self, user_id: int) -> Dict[str, Any]:
		"""Get ingestion statistics for a user"""
		try:
			user = self.db.query(User).filter(User.id == user_id).first()

			if not user:
				return {"error": "User not found"}

			profile = user.profile or {}

			# Get job counts by source
			job_counts = self.db.query(Job.source, self.db.func.count(Job.id)).filter(Job.user_id == user_id).group_by(Job.source).all()

			# Get recent jobs (last 7 days)
			recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
			recent_jobs_count = self.db.query(Job).filter(Job.user_id == user_id, Job.created_at >= recent_cutoff).count()

			return {
				"user_id": user_id,
				"last_ingestion": profile.get("last_job_ingestion"),
				"total_jobs": sum(count for _, count in job_counts),
				"jobs_by_source": dict(job_counts),
				"recent_jobs_count": recent_jobs_count,
				"available_scrapers": self._get_scraper_manager().get_available_scrapers(),
				"quota_status": self.quota_manager.get_quota_summary(),
				"health_status": self.quota_manager.get_health_status(),
			}

		except Exception as e:
			logger.error(f"Error getting ingestion stats for user {user_id}: {e!s}")
			return {"error": str(e)}

	async def test_all_sources(self) -> Dict[str, Any]:
		"""Test all job ingestion sources"""

		test_results = {"rss_feeds": {}, "job_apis": {}, "web_scrapers": {}, "quota_status": self.quota_manager.get_quota_summary()}

		# Test RSS feeds

		try:
			async with RSSFeedService() as rss_service:
				feed_urls = rss_service.get_default_feed_urls()[:3]  # Test first 3 feeds

				jobs = await rss_service.monitor_feeds(feed_urls, ["software engineer"], max_concurrent=2)

				test_results["rss_feeds"] = {"status": "success", "feeds_tested": len(feed_urls), "jobs_found": len(jobs)}

		except Exception as e:
			test_results["rss_feeds"] = {"status": "error", "error": str(e)}

		# Test job APIs
		# Commented out - JobAPIService() implementation needed
		# try:
		# 	async with JobAPIService() as api_service:
		# 		api_tests = await api_service.test_apis()
		# 		test_results["job_apis"] = api_tests
		# except Exception as e:
		# 	test_results["job_apis"] = {"status": "error", "error": str(e)}

		# Test web scrapers

		try:
			scraper_manager = self._get_scraper_manager()

			scraper_tests = await scraper_manager.test_scrapers()

			test_results["web_scrapers"] = scraper_tests

		except Exception as e:
			test_results["web_scrapers"] = {"status": "error", "error": str(e)}

		return test_results


# Factory function for dependency injection


def get_job_scraping_service(db: Session) -> JobScrapingService:
	"""Get JobScrapingService instance"""
	return JobScrapingService(db)
