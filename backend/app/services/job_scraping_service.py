"""
Consolidated Job Scraping Service

Provides a unified interface for job scraping, data ingestion, and normalization
across several sources (APIs and RSS feeds). Includes a Celery task entry point
for batch ingestion per user.

Features:
- Multi-source job aggregation (APIs, RSS, web scrapers)
- Advanced deduplication with fuzzy matching
- Automatic fingerprint generation
- Efficient database queries with composite indexes
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
from app.services.job_deduplication_service import JobDeduplicationService
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
	"""Unified job scraping service that aggregates multiple sources."""

	def __init__(self, db: Session | None = None):
		self.db = db
		self.settings = settings
		self.deduplication_service = JobDeduplicationService(db) if db else None
		self.notification_service = NotificationService()
		self.skill_matcher = SkillMatchingService()
		self.quota_manager = QuotaManager()
		self.scraper_manager: Optional[ScraperManager] = None

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

		# Rate limiting and quota management placeholders
		self.api_quotas: Dict[str, Any] = {}
		self.last_request_times: Dict[str, datetime] = {}

	def _get_scraper_manager(self) -> ScraperManager:
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
				enable_firecrawl=getattr(settings, "SCRAPING_ENABLE_FIRECRAWL", True),
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

	# Main scraping interface
	async def scrape_jobs(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""
		Manual job scraping method - now uses ScraperManager first (same as scheduled ingestion).
		PRIORITY 1: ScraperManager with working scrapers (Adzuna, Arbeitnow, The Muse, RapidAPI)
		PRIORITY 2: Legacy individual scrapers only if needed
		"""
		all_jobs: List[Dict[str, Any]] = []

		# PRIORITY 1: Use ScraperManager with working scrapers
		try:
			# Initialize ScraperManager if not already done
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

		# PRIORITY 2: Only use legacy scrapers if ScraperManager didn't find enough
		if len(all_jobs) < 50:
			logger.info("Using legacy scrapers as fallback...")
			tasks: List[asyncio.Future] = []
			if self.apis["adzuna"]["enabled"]:
				tasks.append(self._scrape_adzuna(user_preferences))
			if self.apis["remoteok"]["enabled"]:
				tasks.append(self._scrape_remoteok(user_preferences))

			# Deprecated scrapers commented out
			# if self.apis["github"]["enabled"]:
			# 	tasks.append(self._scrape_github_issues(user_preferences))
			# if self.apis["usajobs"]["enabled"]:
			# 	tasks.append(self._scrape_usajobs(user_preferences))
			# tasks.append(self._scrape_weworkremotely(user_preferences))
			# tasks.append(self._scrape_stackoverflow(user_preferences))

			if tasks:
				results = await asyncio.gather(*tasks, return_exceptions=True)
				for result in results:
					if isinstance(result, Exception):
						logger.error("Error in job scraping: %r", result)
						continue
					all_jobs.extend(result)

		logger.info(f"Total jobs scraped: {len(all_jobs)}")
		return all_jobs

	# Individual source scrapers
	async def _scrape_adzuna(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
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

	async def _scrape_github_issues(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		try:
			async with aiohttp.ClientSession() as session:
				headers = {"Authorization": f"token {self.apis['github']['token']}", "Accept": "application/vnd.github.v3+json"}
				skills_query = " OR ".join(preferences.get("skills", []))
				query = f"label:job type:issue state:open ({skills_query})"
				params = {"q": query, "sort": "created", "order": "desc", "per_page": 50}
				url = self.apis["github"]["base_url"]
				async with session.get(url, headers=headers, params=params) as resp:
					if resp.status == 200:
						data = await resp.json()
						return [self._normalize_github_issue(it) for it in data.get("items", [])]
					logger.error("GitHub API error: %s", resp.status)
		except Exception as e:
			logger.error("Error scraping from GitHub: %r", e)
		return []

	async def _scrape_usajobs(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		try:
			async with aiohttp.ClientSession() as session:
				params = {
					"Keyword": " ".join(preferences.get("skills", [])),
					"LocationName": (preferences.get("locations") or [""])[0],
					"ResultsPerPage": 50,
					"SortField": "OpenDate",
					"SortDirection": "Desc",
				}
				headers = {"Host": "data.usajobs.gov", "User-Agent": "career-copilot@example.com"}
				url = self.apis["usajobs"]["base_url"]
				async with session.get(url, params=params, headers=headers) as resp:
					if resp.status == 200:
						data = await resp.json()
						items = data.get("SearchResult", {}).get("SearchResultItems", [])
						return [self._normalize_usajobs_job(item) for item in items]
					logger.error("USAJobs API error: %s", resp.status)
		except Exception as e:
			logger.error("Error scraping from USAJobs: %r", e)
		return []

	async def _scrape_remoteok(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["remoteok"]["base_url"]
				async with session.get(url) as resp:
					if resp.status == 200:
						data = await resp.json()
						if isinstance(data, list) and len(data) > 1:
							keywords = [s.lower() for s in preferences.get("skills", [])]
							out: List[Dict[str, Any]] = []
							for job in data[1:]:  # skip metadata
								if self._matches_keywords_remoteok(job, keywords):
									norm = self._normalize_remoteok_job(job)
									if norm:
										out.append(norm)
							return out[:50]
					logger.error("RemoteOK API error: %s", resp.status)
		except Exception as e:
			logger.error("Error scraping from RemoteOK: %r", e)
		return []

	async def _scrape_weworkremotely(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["weworkremotely"]["base_url"]
				async with session.get(url) as resp:
					if resp.status == 200:
						content = await resp.text()
						feed = feedparser.parse(content)
						return [self._normalize_wwr_job(entry) for entry in feed.entries]
					logger.error("WWR feed error: %s", resp.status)
		except Exception as e:
			logger.error("Error scraping from WeWorkRemotely: %r", e)
		return []

	async def _scrape_stackoverflow(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
		try:
			async with aiohttp.ClientSession() as session:
				url = self.apis["stackoverflow"]["base_url"]
				async with session.get(url) as resp:
					if resp.status == 200:
						content = await resp.text()
						feed = feedparser.parse(content)
						return [self._normalize_stackoverflow_job(entry) for entry in feed.entries]
					logger.error("Stack Overflow feed error: %s", resp.status)
		except Exception as e:
			logger.error("Error scraping from Stack Overflow: %r", e)
		return []

	# Normalization helpers
	def _normalize_adzuna_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
		return {
			"title": job.get("title"),
			"company": job.get("company", {}).get("display_name"),
			"location": job.get("location", {}).get("display_name"),
			"description": job.get("description"),
			"url": job.get("redirect_url"),
			"salary_min": job.get("salary_min"),
			"salary_max": job.get("salary_max"),
			"source": "adzuna",
			"remote": "remote" in (job.get("description", "").lower()),
			"posted_at": job.get("created"),
			"original_data": job,
		}

	def _normalize_github_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
		return {
			"title": issue.get("title"),
			"company": self._extract_company_from_issue(issue),
			"location": self._extract_location_from_issue(issue),
			"description": issue.get("body"),
			"url": issue.get("html_url"),
			"salary_min": None,
			"salary_max": None,
			"source": "github",
			"remote": "remote" in (issue.get("body", "").lower()),
			"posted_at": issue.get("created_at"),
			"original_data": issue,
		}

	def _normalize_usajobs_job(self, item: Dict[str, Any]) -> Dict[str, Any]:
		job_data = item.get("MatchedObjectDescriptor", {})
		sal = self._extract_usajobs_salary(job_data)
		return {
			"title": job_data.get("PositionTitle", ""),
			"company": job_data.get("OrganizationName", "U.S. Government"),
			"location": self._extract_usajobs_location(job_data),
			"description": job_data.get("QualificationSummary", ""),
			"url": job_data.get("PositionURI", ""),
			"salary_min": sal.get("min"),
			"salary_max": sal.get("max"),
			"source": "usajobs",
			"remote": False,
			"posted_at": job_data.get("PublicationStartDate"),
			"original_data": item,
		}

	def _normalize_remoteok_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
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
		return {
			"title": entry.get("title"),
			"company": self._extract_company_from_so(entry),
			"location": self._extract_location_from_so(entry),
			"description": entry.get("description"),
			"url": entry.get("link"),
			"salary_min": None,
			"salary_max": None,
			"source": "stackoverflow",
			"remote": "remote" in (entry.get("description", "").lower()),
			"posted_at": entry.get("published"),
			"original_data": entry,
		}

	# Extraction helpers
	def _extract_company_from_issue(self, issue: Dict[str, Any]) -> str:
		title = (issue.get("title", "") or "").lower()
		for pattern in ["at", "with", "for", "@"]:
			if pattern in title:
				parts = title.split(pattern)
				if len(parts) > 1:
					return parts[1].strip().title()
		return issue.get("repository", {}).get("owner", {}).get("login", "Unknown")

	def _extract_location_from_issue(self, issue: Dict[str, Any]) -> str:
		body = (issue.get("body", "") or "").lower()
		for pattern in ["location:", "based in:", "position location:"]:
			if pattern in body:
				idx = body.find(pattern)
				end_idx = body.find("\n", idx)
				if end_idx == -1:
					end_idx = len(body)
				return body[idx + len(pattern) : end_idx].strip().title()
		return "Remote/Unspecified"

	def _extract_usajobs_location(self, job_data: Dict[str, Any]) -> str:
		locations = job_data.get("PositionLocation", [])
		if locations and isinstance(locations, list):
			location = locations[0]
			city = location.get("CityName", "")
			state = location.get("StateCode", "")
			return f"{city}, {state}".strip(", ")
		return ""

	def _extract_usajobs_salary(self, job_data: Dict[str, Any]) -> Dict[str, Optional[int]]:
		salary_info: Dict[str, Optional[int]] = {"min": None, "max": None}
		remuneration = job_data.get("PositionRemuneration", [])
		if remuneration and isinstance(remuneration, list):
			salary_data = remuneration[0]
			try:
				if salary_data.get("MinimumRange"):
					salary_info["min"] = int(float(salary_data["MinimumRange"]))
				if salary_data.get("MaximumRange"):
					salary_info["max"] = int(float(salary_data["MaximumRange"]))
			except (ValueError, TypeError):
				pass
		return salary_info

	def _extract_company_from_wwr(self, entry: Dict[str, Any]) -> str:
		title = entry.get("title", "")
		return title.split(":")[0].strip() if ":" in title else "Unknown"

	def _extract_company_from_so(self, entry: Dict[str, Any]) -> str:
		title = entry.get("title", "")
		return title.split("at")[1].strip() if "at" in title else "Unknown"

	def _extract_location_from_so(self, entry: Dict[str, Any]) -> str:
		title = entry.get("title", "")
		if "(" in title and ")" in title:
			return title[title.find("(") + 1 : title.find(")")].strip()
		return "Remote/Unspecified"

	def _matches_keywords_remoteok(self, job_data: Dict[str, Any], keywords: List[str]) -> bool:
		if not keywords:
			return True
		txt = f"{job_data.get('position', '')} {job_data.get('company', '')} {job_data.get('description', '')}".lower()
		return any(k in txt for k in keywords)

	# Ingestion pipeline
	async def ingest_jobs_for_user(self, user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
		user = self.db.query(User).filter(User.id == user_id).first()
		if not user:
			raise ValueError(f"User {user_id} not found")

		logger.info("Starting multi-source job ingestion for user %s", user_id)

		search_params = self._extract_search_params(user)
		ingestion_results: Dict[str, Any] = {
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

		all_jobs: List[Dict[str, Any]] = []

		# PRIORITY 1: Use ScraperManager with working scrapers (Adzuna, Arbeitnow, The Muse, RapidAPI, etc.)
		scraper_jobs = await self._ingest_from_scrapers(search_params, max_jobs)
		if scraper_jobs:
			all_jobs.extend(scraper_jobs)
			ingestion_results["sources_used"].append("scraper_manager")
			ingestion_results["jobs_by_source"]["scraper_manager"] = len(scraper_jobs)
			logger.info(f"✅ ScraperManager found {len(scraper_jobs)} jobs")

		# PRIORITY 2: Try RSS feeds only if needed (many are deprecated/broken)
		if len(all_jobs) < max_jobs // 2:
			rss_jobs = await self._ingest_from_rss_feeds(search_params, max_jobs // 4)
			if rss_jobs:
				all_jobs.extend(rss_jobs)
				ingestion_results["sources_used"].append("rss_feeds")
				ingestion_results["jobs_by_source"]["rss_feeds"] = len(rss_jobs)

		# PRIORITY 3: Legacy API scrapers (mostly deprecated, skip for now)
		# api_jobs = await self._ingest_from_apis(search_params, max_jobs // 4)
		# if api_jobs:
		# 	all_jobs.extend(api_jobs)
		# 	ingestion_results["sources_used"].append("job_apis")
		# 	ingestion_results["jobs_by_source"]["job_apis"] = len(api_jobs)

		ingestion_results["jobs_found"] = len(all_jobs)

		new_jobs = await self._filter_existing_jobs(user_id, all_jobs)
		ingestion_results["duplicates_filtered"] = len(all_jobs) - len(new_jobs)

		saved_jobs: List[Job] = []
		for data in new_jobs:
			try:
				job_create = self._convert_to_job_create(data, user_id)
				job = Job(**job_create.model_dump(), user_id=user_id)

				# Generate and store fingerprint for future deduplication
				if self.deduplication_service:
					job.job_fingerprint = self.deduplication_service.create_job_fingerprint(job.title, job.company, job.location)

				self.db.add(job)
				self.db.flush()

				if hasattr(self.skill_matcher, "calculate_match_score"):
					job.match_score = await self.skill_matcher.calculate_match_score(job, user_id)

				saved_jobs.append(job)
			except Exception as e:
				# Handle both dict and Pydantic model for error reporting
				if hasattr(data, "model_dump"):
					data_dict = data.model_dump()
				elif hasattr(data, "dict"):
					data_dict = data.dict()
				elif isinstance(data, dict):
					data_dict = data
				else:
					data_dict = {"title": "Unknown"}

				msg = f"Error saving job '{data_dict.get('title', 'Unknown')}': {e!r}"
				logger.error(msg)
				ingestion_results["errors"].append(msg)

		self.db.commit()
		ingestion_results["jobs_saved"] = len(saved_jobs)
		ingestion_results["completed_at"] = datetime.now(timezone.utc)

		logger.info(
			"Multi-source job ingestion completed for user %s: %d new jobs saved from %d sources",
			user_id,
			ingestion_results["jobs_saved"],
			len(ingestion_results["sources_used"]),
		)
		return ingestion_results

	def _extract_search_params(self, user: User) -> Dict[str, List[str]]:
		"""Extract search parameters from user object"""
		keywords: List[str] = []

		# Try to get skills from user.skills attribute (direct field)
		if hasattr(user, "skills") and user.skills:
			if isinstance(user.skills, list):
				keywords.extend(user.skills[:3])
			elif isinstance(user.skills, str):
				keywords.extend([s.strip() for s in user.skills.split(",")][:3])

		# Fallback to profile if it exists
		if hasattr(user, "profile") and user.profile:
			profile = user.profile
			user_skills = profile.get("skills", [])
			if user_skills:
				keywords.extend(user_skills[:3])
			preferred_titles = profile.get("preferences", {}).get("job_titles", [])
			keywords.extend(preferred_titles)

		if not keywords:
			keywords = ["software engineer", "developer", "programmer"]

		locations: List[str] = []

		# Try to get locations from user.preferred_locations (direct field)
		if hasattr(user, "preferred_locations") and user.preferred_locations:
			if isinstance(user.preferred_locations, list):
				locations.extend(user.preferred_locations)
			elif isinstance(user.preferred_locations, str):
				locations.extend([l.strip() for l in user.preferred_locations.split(",")])

		# Fallback to profile if it exists
		if hasattr(user, "profile") and user.profile:
			locations.extend(user.profile.get("locations", []))

		# Respect user's remote preference (default is in-person jobs)
		prefer_remote = getattr(user, "prefer_remote_jobs", False)

		if prefer_remote:
			# User wants remote jobs - add "remote" if not already present
			if not any("remote" in loc.lower() for loc in locations):
				locations.append("remote")
		else:
			# User prefers in-person jobs - remove "remote" if present
			locations = [loc for loc in locations if "remote" not in loc.lower()]

		if not locations:
			# Default to remote if no locations specified (backward compatibility)
			locations = ["remote", "united states"]
		return {"keywords": keywords[:5], "locations": locations[:3]}

	async def _filter_existing_jobs(self, user_id: int, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""
		Filter out jobs that already exist for the user using advanced deduplication

		Uses JobDeduplicationService for:
		- URL-based matching
		- Fingerprint-based matching
		- Fuzzy title/company matching
		"""
		if not jobs or not self.deduplication_service:
			return jobs

		# Use deduplication service with fuzzy matching
		unique_jobs, stats = self.deduplication_service.deduplicate_against_db(
			jobs=jobs,
			user_id=user_id,
			days_lookback=30,
			strict_mode=False,  # Enable fuzzy matching
		)

		logger.info(
			f"Deduplication complete: {stats['unique_output']}/{stats['total_input']} unique jobs ({stats['duplicates_removed']} duplicates filtered)"
		)

		return unique_jobs

	def _create_job_key(self, title: str, company: str, location: Optional[str] = None) -> str:
		"""
		DEPRECATED: Use JobDeduplicationService.create_job_fingerprint instead

		Kept for backward compatibility
		"""
		if self.deduplication_service:
			return self.deduplication_service.create_job_fingerprint(title, company, location)

		# Fallback to old logic
		t = " ".join((title or "").lower().strip().split())
		c = " ".join((company or "").lower().strip().split())
		l = " ".join((location or "").lower().strip().split())
		return f"{t}|{c}|{l}"

	def _convert_to_job_create(self, job_data: Dict[str, Any], user_id: int) -> JobCreate:
		# Handle both dict and Pydantic model
		if hasattr(job_data, "model_dump"):
			job_dict = job_data.model_dump()
		elif hasattr(job_data, "dict"):
			job_dict = job_data.dict()
		elif isinstance(job_data, dict):
			job_dict = job_data
		else:
			raise ValueError(f"Unexpected job_data type: {type(job_data)}")

		return JobCreate(
			title=job_dict.get("title", "Unknown Position"),
			company=job_dict.get("company", "Unknown Company"),
			location=job_dict.get("location", "Unknown Location"),
			description=job_dict.get("description", ""),
			salary_range=self._format_salary_range(job_dict.get("salary_min"), job_dict.get("salary_max")),
			source=job_dict.get("source", "unknown"),
			application_url=job_dict.get("url", ""),
			remote_option=job_dict.get("remote", False),
			posted_at=job_dict.get("posted_at"),
		)

	def _format_salary_range(self, salary_min: Optional[int], salary_max: Optional[int]) -> Optional[str]:
		if salary_min and salary_max:
			return f"${salary_min:,} - ${salary_max:,}"
		if salary_min:
			return f"${salary_min:,}+"
		if salary_max:
			return f"Up to ${salary_max:,}"
		return None

	async def _ingest_from_rss_feeds(self, search_params: Dict[str, List[str]], max_jobs: int) -> List[Dict[str, Any]]:
		try:
			async with RSSFeedService() as rss_service:
				feed_urls = rss_service.get_default_feed_urls()
				jobs = await rss_service.monitor_feeds(feed_urls, search_params.get("keywords"), max_concurrent=5)
				return jobs[:max_jobs]
		except Exception as e:
			logger.error("Error ingesting from RSS feeds: %r", e)
			return []

	async def _ingest_from_apis(self, search_params: Dict[str, List[str]], max_jobs: int) -> List[Dict[str, Any]]:
		user_preferences = {
			"skills": search_params.get("keywords", []),
			"locations": search_params.get("locations", []),
		}
		scraped_jobs = await self.scrape_jobs(user_preferences)
		return scraped_jobs[:max_jobs]

	async def _ingest_from_scrapers(self, search_params: Dict[str, List[str]], max_jobs: int) -> List[Dict[str, Any]]:
		try:
			scraper_manager = self._get_scraper_manager()
			jobs = await scraper_manager.search_all_sites(
				keywords=" ".join(search_params.get("keywords", [])),
				location=" ".join(search_params.get("locations", [])),
				max_total_results=max_jobs,
			)
			return jobs
		except Exception as e:
			logger.error("Error ingesting from scrapers: %r", e)
			return []


@celery_app.task(bind=True, name="app.services.job_scraping_service.ingest_jobs")
def ingest_jobs_task(self, user_ids: Optional[List[int]] = None, max_jobs_per_user: int = 50) -> Dict[str, Any]:
	task_id = current_task.request.id
	logger.info("Starting job ingestion task %s", task_id)
	results: Dict[str, Any] = {
		"task_id": task_id,
		"users_processed": 0,
		"total_jobs_found": 0,
		"total_jobs_saved": 0,
		"errors": [],
		"user_results": [],
	}
	try:
		db: Session = next(get_db())
		try:
			if user_ids:
				users = db.query(User).filter(User.id.in_(user_ids)).all()
			else:
				cutoff = datetime.now(timezone.utc) - timedelta(days=30)
				users = db.query(User).filter(User.last_active >= cutoff).all()

			logger.info("Processing job ingestion for %d users", len(users))
			scraping_service = JobScrapingService(db)

			for i, user in enumerate(users):
				try:
					current_task.update_state(state="PROGRESS", meta={"current": i + 1, "total": len(users), "status": f"Processing user {user.id}"})
					logger.info("Processing job ingestion for user %s", user.id)
					loop = asyncio.new_event_loop()
					asyncio.set_event_loop(loop)
					try:
						user_result = loop.run_until_complete(scraping_service.ingest_jobs_for_user(user.id, max_jobs_per_user))
					finally:
						loop.close()

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
					if user_result["errors"]:
						results["errors"].extend([f"User {user.id}: {err}" for err in user_result["errors"]])
					logger.info("Completed job ingestion for user %s: %d jobs saved", user.id, user_result["jobs_saved"])
				except Exception as e:
					msg = f"Error processing user {user.id}: {e!r}"
					logger.error(msg)
					results["errors"].append(msg)

			logger.info(
				"Job ingestion task completed: %d users processed, %d jobs saved",
				results["users_processed"],
				results["total_jobs_saved"],
			)
			return results
		finally:
			db.close()
	except Exception as e:
		msg = f"Job ingestion task failed: {e!r}"
		logger.error(msg)
		results["errors"].append(msg)
		return results


def get_job_scraping_service(db: Session) -> JobScrapingService:
	return JobScrapingService(db)
