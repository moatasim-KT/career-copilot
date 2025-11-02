"""
Arbeitnow Scraper - Germany-focused job board with visa sponsorship filter
https://www.arbeitnow.com/
"""

import logging
from typing import List, Optional
from datetime import datetime

from app.schemas.job import JobCreate
from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class ArbeitnowScraper(BaseScraper):
	"""Scraper for Arbeitnow (Germany) with visa sponsorship support"""

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.base_url = "https://www.arbeitnow.com"
		self.api_url = "https://www.arbeitnow.com/api/job-board-api"
		self.name = "Arbeitnow"

	async def search_jobs(
		self,
		keywords: str = "",
		location: str = "Germany",
		max_results: int = 25,
		visa_sponsorship: bool = True,
	) -> List[JobCreate]:
		"""
		Search for jobs on Arbeitnow
		
		Args:
			keywords: Job search keywords (e.g., "AI", "Data Science", "Machine Learning")
			location: Location filter (default: Germany)
			max_results: Maximum number of jobs to return
			visa_sponsorship: Filter for visa sponsorship jobs only
			
		Returns:
			List of JobCreate objects
		"""
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		logger.info(f"Searching Arbeitnow for '{keywords}' in {location} (visa_sponsorship={visa_sponsorship})")

		jobs = []
		page = 1
		
		try:
			while len(jobs) < max_results:
				# Build query parameters
				params = {
					"search": keywords or "",
					"page": page,
				}
				
				# Add visa sponsorship filter if requested
				if visa_sponsorship:
					params["visa_sponsorship"] = "true"
				
				# Make API request
				response = await self._make_request(self.api_url, params=params)
				
				if not response:
					logger.warning(f"Failed to fetch page {page} from Arbeitnow")
					break
				
				# Parse JSON response
				try:
					data = response.json()
					job_listings = data.get("data", [])
					
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
					logger.error(f"Error parsing Arbeitnow response: {e}", exc_info=True)
					break
		
		except Exception as e:
			logger.error(f"Error searching Arbeitnow: {e}", exc_info=True)
		
		logger.info(f"Arbeitnow search completed: {len(jobs)} jobs found")
		return jobs[:max_results]

	def _parse_job(self, job_data: dict) -> Optional[JobCreate]:
		"""Parse a single job listing from Arbeitnow API"""
		try:
			# Extract job details
			title = job_data.get("title", "").strip()
			company = job_data.get("company_name", "").strip()
			
			if not title or not company:
				return None
			
			# Build job description
			description_parts = []
			
			if job_data.get("description"):
				description_parts.append(job_data["description"])
			
			# Add tags as skills
			tags = job_data.get("tags", [])
			if tags:
				description_parts.append(f"\n\nSkills: {', '.join(tags)}")
			
			description = "\n".join(description_parts).strip()
			
			# Get location
			location = job_data.get("location", "Germany")
			
			# Remote option
			remote_option = "remote" if job_data.get("remote", False) else "on-site"
			
			# URL
			slug = job_data.get("slug", "")
			url = f"{self.base_url}/jobs/{slug}" if slug else self.base_url
			
			# Build job object
			job = JobCreate(
				title=title,
				company=company,
				location=location,
				description=description,
				url=url,
				source="Arbeitnow",
				job_type=job_data.get("job_types", ["Full-time"])[0] if job_data.get("job_types") else "Full-time",
				remote_option=remote_option,
				posted_date=datetime.now(),  # Arbeitnow doesn't provide posted date in API
				salary_min=None,
				salary_max=None,
				salary_currency="EUR",
				requires_visa_sponsorship=True,  # All jobs from this search have visa sponsorship
			)
			
			return job
			
		except Exception as e:
			logger.error(f"Error parsing Arbeitnow job: {e}", exc_info=True)
			return None

	def close(self):
		"""Close the scraper session"""
		if self.session:
			import asyncio
			try:
				loop = asyncio.get_event_loop()
				if loop.is_running():
					loop.create_task(self.session.aclose())
				else:
					loop.run_until_complete(self.session.aclose())
			except Exception:
				pass
