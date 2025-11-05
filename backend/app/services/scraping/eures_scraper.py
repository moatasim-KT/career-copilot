"""
EURES Scraper - Official European Job Mobility Portal
https://eures.europa.eu/
"""

import logging
import urllib.parse
from datetime import datetime
from typing import List, Optional

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class EuresScraper(BaseScraper):
	"""Scraper for EURES - Official EU job portal for cross-border workers"""

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.base_url = "https://eures.europa.eu"
		self.search_url = f"{self.base_url}/search-engine/search/api/v1/jobs"
		self.name = "EURES"

	async def search_jobs(
		self,
		keywords: str = "",
		location: str = "",
		max_results: int = 25,
		eu_countries: Optional[List[str]] = None,
	) -> List[JobCreate]:
		"""
		Search for jobs on EURES

		Args:
			keywords: Job search keywords (e.g., "Data Science", "AI", "Machine Learning")
			location: Location/country filter
			max_results: Maximum number of jobs to return
			eu_countries: List of EU country codes (e.g., ["DE", "FR", "NL"])

		Returns:
			List of JobCreate objects
		"""
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		logger.info(f"Searching EURES for '{keywords}' in {location or 'EU'}")

		jobs = []
		page = 0
		page_size = 25

		# Default to major EU countries if not specified
		if not eu_countries:
			eu_countries = ["DE", "FR", "NL", "ES", "IT", "SE", "AT", "BE", "DK", "FI", "IE", "PL"]

		try:
			while len(jobs) < max_results:
				# Build query parameters for EURES API
				params = {
					"query": keywords or "",
					"page": page,
					"pageSize": min(page_size, max_results - len(jobs)),
					"language": "en",
					"selectedSectors": "",  # Can be refined for tech sector
				}

				# Add country filter
				if eu_countries:
					params["location"] = ",".join(eu_countries)

				# Make API request
				response = await self._make_request(self.search_url, params=params)

				if not response:
					logger.warning(f"Failed to fetch page {page} from EURES")
					break

				try:
					data = response.json()

					# EURES API structure may vary, check for jobs in different possible keys
					job_listings = data.get("data", {}).get("jobs", []) or data.get("jobs", []) or data.get("results", [])

					if not job_listings:
						logger.info(f"No more jobs found on page {page}")
						break

					logger.info(f"Found {len(job_listings)} jobs on page {page}")

					# Parse each job listing
					for job_data in job_listings:
						if len(jobs) >= max_results:
							break

						job = self._parse_job(job_data)
						if job:
							jobs.append(job)

					page += 1

				except Exception as e:
					logger.error(f"Error parsing EURES response: {e}", exc_info=True)
					break

		except Exception as e:
			logger.error(f"Error searching EURES: {e}", exc_info=True)

		logger.info(f"EURES search completed: {len(jobs)} jobs found")
		return jobs[:max_results]

	def _parse_job(self, job_data: dict) -> Optional[JobCreate]:
		"""Parse a single job listing from EURES API"""
		try:
			# Extract basic information
			title = job_data.get("title", "").strip()

			# Company/employer
			employer = job_data.get("employer", {})
			if isinstance(employer, dict):
				company = employer.get("name", "") or employer.get("companyName", "")
			else:
				company = str(employer) if employer else ""

			if not company:
				company = job_data.get("companyName", "") or job_data.get("company", "")

			if not title or not company:
				logger.debug(f"Skipping job - missing title or company: {job_data}")
				return None

			# Location
			location_data = job_data.get("location", {})
			if isinstance(location_data, dict):
				city = location_data.get("city", "")
				country = location_data.get("country", "") or location_data.get("countryCode", "")
				location = f"{city}, {country}".strip(", ")
			else:
				location = str(location_data) if location_data else ""

			if not location:
				location = job_data.get("workLocation", "") or "Europe"

			# Description
			description = job_data.get("description", "") or job_data.get("jobDescription", "")

			# Add requirements if available
			requirements = job_data.get("requirements", "")
			if requirements:
				description = f"{description}\n\nRequirements:\n{requirements}"

			# URL - EURES job reference
			job_id = job_data.get("id", "") or job_data.get("jobId", "") or job_data.get("referenceNumber", "")
			if job_id:
				url = f"{self.base_url}/portal/jv-se/job-details/{job_id}"
			else:
				url = self.base_url

			# Job type
			job_type_raw = job_data.get("jobType", "") or job_data.get("contractType", "")
			job_type = self._normalize_job_type(job_type_raw)

			# Remote option
			remote_option = "on-site"
			if job_data.get("remote") or "remote" in description.lower():
				remote_option = "remote"
			elif "hybrid" in description.lower():
				remote_option = "hybrid"

			# Salary information
			salary_data = job_data.get("salary", {})
			salary_min = None
			salary_max = None
			salary_currency = "EUR"

			if isinstance(salary_data, dict):
				salary_min = salary_data.get("min") or salary_data.get("minimum")
				salary_max = salary_data.get("max") or salary_data.get("maximum")
				salary_currency = salary_data.get("currency", "EUR")

			# Posted date
			posted_date_str = job_data.get("publicationDate", "") or job_data.get("postedDate", "")
			posted_date = self._parse_date(posted_date_str) if posted_date_str else datetime.now()

			# Build job object
			job = JobCreate(
				title=title,
				company=company.strip(),
				location=location,
				description=description or f"{title} position at {company}",
				url=url,
				source="EURES",
				job_type=job_type,
				remote_option=remote_option,
				posted_date=posted_date,
				salary_min=salary_min,
				salary_max=salary_max,
				salary_currency=salary_currency,
				requires_visa_sponsorship=False,  # EURES jobs are EU-wide, may or may not sponsor
			)

			return job

		except Exception as e:
			logger.error(f"Error parsing EURES job: {e}", exc_info=True)
			return None

	def _normalize_job_type(self, job_type_raw: str) -> str:
		"""Normalize job type to standard format"""
		if not job_type_raw:
			return "Full-time"

		job_type_lower = job_type_raw.lower()

		if "full" in job_type_lower or "permanent" in job_type_lower:
			return "Full-time"
		elif "part" in job_type_lower:
			return "Part-time"
		elif "contract" in job_type_lower or "temporary" in job_type_lower:
			return "Contract"
		elif "intern" in job_type_lower:
			return "Internship"
		else:
			return "Full-time"

	def _parse_date(self, date_str: str) -> datetime:
		"""Parse various date formats"""
		try:
			# Try ISO format first
			if "T" in date_str:
				return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

			# Try other common formats
			from dateutil import parser

			return parser.parse(date_str)
		except Exception:
			return datetime.now()

	def _parse_job_listing(self, job_data: dict) -> Optional[dict]:
		"""Required by base class - parse job listing to dict"""
		job = self._parse_job(job_data)
		if job:
			return job.model_dump()
		return None

	def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
		"""Required by base class - build search URL"""
		params = {
			"query": keywords or "",
			"page": page,
			"pageSize": 25,
			"language": "en",
		}
		param_str = "&".join([f"{k}={v}" for k, v in params.items()])
		return f"{self.search_url}?{param_str}"

	def close(self):
		"""Close the scraper session"""
		if self.session:
			import asyncio

			try:
				loop = asyncio.get_event_loop()
				if loop.is_running():
					self._close_tasks = getattr(self, "_close_tasks", [])
					self._close_tasks.append(loop.create_task(self.session.aclose()))
				else:
					loop.run_until_complete(self.session.aclose())
			except Exception:
				pass
