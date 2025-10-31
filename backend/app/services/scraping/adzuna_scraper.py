import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from app.core.config import get_settings
from app.schemas.job import JobCreate

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)
settings = get_settings()


class AdzunaScraper(BaseScraper):
	"""Scraper for Adzuna API"""
	
	# Mapping of country names to Adzuna country codes
	COUNTRY_CODES = {
		"germany": "de",
		"deutschland": "de",
		"france": "fr",
		"netherlands": "nl",
		"nederland": "nl",
		"united kingdom": "gb",
		"uk": "gb",
		"great britain": "gb",
		"spain": "es",
		"españa": "es",
		"italy": "it",
		"italia": "it",
		"poland": "pl",
		"polska": "pl",
		"belgium": "be",
		"belgië": "be",
		"belgique": "be",
		"austria": "at",
		"österreich": "at",
		"switzerland": "ch",
		"schweiz": "ch",
		"suisse": "ch",
		"sweden": "se",
		"sverige": "se",
		"ireland": "ie",
		"portugal": "pt",
		"united states": "us",
		"usa": "us",
		"canada": "ca",
		"australia": "au",
		"india": "in",
		"singapore": "sg",
		"brazil": "br",
		"brasil": "br",
	}

	def __init__(self, rate_limiter=None):
		super().__init__(rate_limiter)
		self.base_url = "https://api.adzuna.com/v1/api"
		self.app_id = settings.adzuna_app_id
		self.app_key = settings.adzuna_app_key
		self.default_country = settings.adzuna_country
		self.name = "adzuna"

		if not self.app_id or not self.app_key:
			logger.error("Adzuna API keys (ADZUNA_APP_ID, ADZUNA_APP_KEY) are not set.")
			raise ValueError("Adzuna API keys are required.")
	
	def _detect_country(self, location: str) -> str:
		"""Detect country code from location string."""
		location_lower = location.lower()
		
		# Check for country names in the location string
		for country_name, country_code in self.COUNTRY_CODES.items():
			if country_name in location_lower:
				return country_code
		
		# Default to configured country
		return self.default_country

	def _build_search_url(self, keywords: str, location: str, page: int = 1) -> str:
		"""Build the search URL with query parameters."""
		# Detect country from location
		country = self._detect_country(location)
		
		# Base URL structure: https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
		url = f"{self.base_url}/jobs/{country}/search/{page}"
		
		# Build query parameters
		params = {
			"app_id": self.app_id,
			"app_key": self.app_key,
			"what": keywords,
			"where": location,
			"results_per_page": 25
		}
		
		query_string = urlencode(params)
		return f"{url}?{query_string}"

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
		"""Search for jobs on Adzuna"""
		jobs: List[JobCreate] = []
		page = 1
		total_pages = 1

		while len(jobs) < max_results and page <= total_pages:
			url = self._build_search_url(keywords, location, page)
			# Adzuna requires Accept header for JSON response
			headers = {"Accept": "application/json"}
			response = await self._make_request(url, headers=headers)

			if response and response.status_code == 200:
				try:
					data = response.json()  # httpx.Response.json() is not async
				except Exception as e:
					logger.error(f"Failed to parse JSON from Adzuna response: {e}")
					logger.error(f"Response text: {response.text[:500]}")
					break
					
				total_results = data.get("count", 0)
				if total_results > 0:
					# Adzuna API returns max 50 results per page
					total_pages = (total_results + 49) // 50
					for job_data in data.get("results", []):
						parsed_job = self._parse_job_listing(job_data)
						if parsed_job:
							job_create_obj = self._create_job_object(parsed_job)
							if job_create_obj:
								jobs.append(job_create_obj)
								if len(jobs) >= max_results:
									break
				else:
					logger.info(f"No jobs found on Adzuna for keywords: {keywords}, location: {location}")
					break
			else:
				logger.error(f"Failed to fetch jobs from Adzuna. Response: {response.text if response else 'No response'}")
				break
			page += 1

		return jobs

	def _parse_job_listing(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		"""Parse a single job listing from Adzuna API response"""
		try:
			salary_min = job_data.get("salary_min")
			salary_max = job_data.get("salary_max")
			salary_string = ""
			if salary_min is not None and salary_max is not None:
				salary_string = f"${salary_min:,.0f}-${salary_max:,.0f}"
			elif salary_min is not None:
				salary_string = f"${salary_min:,.0f}+"
			return {
				"title": job_data.get("title"),
				"company": job_data.get("company", {}).get("display_name", ""),
				"location": job_data.get("location", {}).get("display_name", ""),
				"description": job_data.get("description"),
				"url": job_data.get("redirect_url"),
				# Pass salary as a string for compatibility; extract later if needed
				"salary": salary_string,
				"job_type": job_data.get("contract_type", "").replace("_", "-"),
				"remote": "remote" in job_data.get("category", {}).get("label", "").lower() or "remote" in job_data.get("description", "").lower(),
				"tech_stack": [],  # Adzuna doesn't provide tech stack directly, can be extracted from description later
				"responsibilities": job_data.get("description"),  # Adzuna description often contains responsibilities
				"source": "scraped",
				"currency": "USD",
				"requirements": "",  # Adzuna doesn't have a direct requirements field, default to empty string
			}
		except Exception as e:
			logger.error(f"Error parsing Adzuna job listing: {e}")
			return None

	def _create_job_object(self, parsed_data: Dict[str, Any]) -> Optional[JobCreate]:
		"""Convert parsed data to JobCreate schema with compatibility mapping"""
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
