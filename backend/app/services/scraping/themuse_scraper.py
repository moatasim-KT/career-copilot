import logging
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.schemas.job import JobCreate

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)
settings = get_settings()


class TheMuseScraper(BaseScraper):
	"""Scraper for The Muse API"""

	def __init__(self, rate_limiter=None):
		super().__init__(rate_limiter)
		self.base_url = settings.themuse_base_url or "https://www.themuse.com/api/public"
		self.api_key = settings.themuse_api_key  # Optional - can be None for free tier
		# Treat placeholder/comment values as not set
		if self.api_key and self.api_key.strip().startswith("#"):
			self.api_key = None
		self.name = "themuse"

	def _build_search_url(self, keywords: str, location: str, page: int = 0) -> str:
		"""Build search URL for The Muse API"""
		params = {
			"page": page,
		}
		
		# Add API key if available
		if self.api_key:
			params["api_key"] = self.api_key
		
		# The Muse uses category and level, not direct keywords
		# We'll use keywords in the general search for now
		if location:
			params["location"] = location
		
		# Build URL
		query_string = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
		return f"{self.base_url}/jobs?{query_string}"

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
		"""Search for jobs on The Muse"""
		jobs: List[JobCreate] = []
		page = 0
		results_per_page = 20  # The Muse default page size
		
		while len(jobs) < max_results:
			url = self._build_search_url(keywords, location, page)
			response = await self._make_request(url)

			if response and response.status_code == 200:
				data = response.json()
				results = data.get("results", [])
				
				if not results:
					logger.info(f"No more jobs found on The Muse for keywords: {keywords}, location: {location}")
					break
				
				for job_data in results:
					# Filter by keywords since The Muse doesn't support keyword search directly
					category_names = [c.get("name", "") for c in job_data.get("categories", []) if isinstance(c, dict)]
					if keywords.lower() in job_data.get("name", "").lower() or \
					   keywords.lower() in " ".join(category_names).lower():
						parsed_job = self._parse_job_listing(job_data)
						if parsed_job:
							job_create_obj = self._create_job_object(parsed_job)
							if job_create_obj:
								jobs.append(job_create_obj)
								if len(jobs) >= max_results:
									break
				
				page += 1
			else:
				logger.error(f"Failed to fetch jobs from The Muse. Response: {response.text if response else 'No response'}")
				break

		logger.info(f"The Muse scraper found {len(jobs)} jobs")
		return jobs

	def _parse_job_listing(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		"""Parse a single job listing from The Muse API response"""
		try:
			# Extract company info
			company_data = job_data.get("company", {})
			
			# Extract locations
			locations = job_data.get("locations", [])
			location_str = locations[0].get("name", "") if locations else ""
			
			# Check if remote
			is_remote = any(loc.get("name", "").lower() == "flexible / remote" for loc in locations)
			
			# Extract categories (can be used as tech stack)
			categories = job_data.get("categories", [])
			tech_stack = [cat.get("name", "") for cat in categories if cat.get("name")]
			
			# Extract levels
			levels = job_data.get("levels", [])
			level_str = levels[0].get("name", "") if levels else ""
			
			return {
				"title": job_data.get("name"),
				"company": company_data.get("name", ""),
				"location": location_str,
				"description": job_data.get("contents", ""),
				"url": job_data.get("refs", {}).get("landing_page", ""),
				"salary": "",  # The Muse doesn't provide salary info
				"job_type": level_str,
				"remote": is_remote,
				"tech_stack": tech_stack,
				"responsibilities": job_data.get("contents", ""),
				"source": self.name,
				"currency": "USD",
				"requirements": "",
			}
		except Exception as e:
			logger.error(f"Error parsing The Muse job listing: {e}")
			return None

	def _create_job_object(self, parsed_data: Dict[str, Any]) -> Optional[JobCreate]:
		"""Convert parsed data to JobCreate schema"""
		if not self._validate_job_data(parsed_data):
			return None

		try:
			return JobCreate(
				title=parsed_data["title"],
				company=parsed_data["company"],
				location=parsed_data.get("location", ""),
				description=parsed_data.get("description", ""),
				application_url=parsed_data.get("url", ""),
				job_type=parsed_data.get("job_type", ""),
				remote_option=("remote" if parsed_data.get("remote", False) else None),
				tech_stack=parsed_data.get("tech_stack", []),
				requirements=parsed_data.get("requirements", ""),
				responsibilities=parsed_data.get("responsibilities", ""),
				source="scraped",
				currency=parsed_data.get("currency", None),
			)
		except Exception as e:
			logger.error(f"Error creating JobCreate object: {e}")
			return None
