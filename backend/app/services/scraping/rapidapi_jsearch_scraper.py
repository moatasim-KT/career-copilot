import logging
from typing import Any, ClassVar, Dict, List, Optional
from urllib.parse import quote, urlencode

from app.core.config import get_settings
from app.schemas.job import JobCreate

from .base_scraper import BaseScraper
from .job_roles import JobRoles

logger = logging.getLogger(__name__)
settings = get_settings()


class RapidAPIJSearchScraper(BaseScraper):
	"""
	Scraper for RapidAPI JSearch - aggregates Indeed, LinkedIn, Glassdoor, etc.

	Searches for tech roles across EU countries with visa sponsorship focus.
	Default search roles:
	- Data Science: Data Scientist, ML Engineer, Data Analyst, Data Engineer
	- Software Engineering: Backend, Frontend, Full-stack, Mobile
	- AI/ML: ML Engineer, AI Researcher, MLOps
	- DevOps: DevOps Engineer, Cloud Engineer, SRE
	- Product: Product Manager, Product Designer
	"""

	# Default roles to search for if none specified
	DEFAULT_ROLES: ClassVar[List[str]] = [
		"data_scientist",
		"ml_engineer",
		"data_analyst",
		"data_engineer",
		"backend_engineer",
		"fullstack_engineer",
		"devops_engineer",
	]

	def __init__(self, rate_limiter=None):
		super().__init__(rate_limiter)
		self.base_url = "https://jsearch.p.rapidapi.com/search"
		self.api_key = settings.rapidapi_jsearch_key
		self.name = "rapidapi_jsearch"

		if not self.api_key:
			logger.error("RapidAPI JSearch API key (RAPIDAPI_JSEARCH_KEY) is not set.")
			raise ValueError("RapidAPI JSearch API key is required.")

	def _build_search_url(self, keywords: str, location: str, page: int = 1) -> str:
		"""Build search URL for RapidAPI JSEarch - Optimized for EU job search"""

		# EU countries known for hiring international talent with visa sponsorship
		# Priority: Countries with best tech job markets and visa sponsorship programs
		eu_country_map = {
			# Western Europe - High tech hubs
			"germany": "de",
			"deutschland": "de",
			"berlin": "de",
			"munich": "de",
			"münchen": "de",
			"frankfurt": "de",
			"hamburg": "de",
			"netherlands": "nl",
			"amsterdam": "nl",
			"rotterdam": "nl",
			"utrecht": "nl",
			"united kingdom": "gb",
			"uk": "gb",
			"london": "gb",
			"manchester": "gb",
			"edinburgh": "gb",
			"france": "fr",
			"paris": "fr",
			"lyon": "fr",
			"switzerland": "ch",
			"zurich": "ch",
			"geneva": "ch",
			# Nordic countries - Strong tech ecosystems
			"sweden": "se",
			"stockholm": "se",
			"gothenburg": "se",
			"malmö": "se",
			"denmark": "dk",
			"copenhagen": "dk",
			"norway": "no",
			"oslo": "no",
			"finland": "fi",
			"helsinki": "fi",
			# Southern Europe - Growing tech scenes
			"spain": "es",
			"madrid": "es",
			"barcelona": "es",
			"portugal": "pt",
			"lisbon": "pt",
			"lisboa": "pt",
			"porto": "pt",
			"italy": "it",
			"milan": "it",
			"milano": "it",
			"rome": "it",
			"roma": "it",
			# Eastern Europe - Emerging tech hubs
			"ireland": "ie",
			"dublin": "ie",
			"poland": "pl",
			"warsaw": "pl",
			"warszawa": "pl",
			"krakow": "pl",
			"kraków": "pl",
			"czech republic": "cz",
			"czechia": "cz",
			"prague": "cz",
			"praha": "cz",
			"austria": "at",
			"vienna": "at",
			"wien": "at",
			"belgium": "be",
			"brussels": "be",
			"bruxelles": "be",
			"greece": "gr",
			"athens": "gr",
			"hungary": "hu",
			"budapest": "hu",
			"romania": "ro",
			"bucharest": "ro",
			"bucurești": "ro",
		}

		# Companies known for visa sponsorship in EU
		visa_sponsor_keywords = ["visa sponsorship", "relocation", "international", "expat", "work permit", "blue card", "skilled migrant"]

		# Detect country code from location
		country_code = None
		location_lower = location.lower() if location else ""

		for geo_name, code in eu_country_map.items():
			if geo_name in location_lower:
				country_code = code
				break

		# If EU location not detected, try generic "europe" or default to Germany (biggest tech market)
		if not country_code:
			if any(term in location_lower for term in ["europe", "eu", "european"]):
				country_code = "de"  # Default to Germany for EU searches
			else:
				country_code = "de"  # Changed default from "us" to "de" for EU focus

		# Optimize query format for better EU results
		# Format: "job title in city/country" works better than "job title jobs in location"
		if location:
			# Try city-specific search first (better results)
			query = f"{keywords} in {location}"
		else:
			query = f"{keywords} Europe"

		params = {
			"query": query,
			"page": str(page),
			"num_pages": "1",
			"country": country_code,
			"date_posted": "month",  # Changed from "all" to get fresher listings
			"employment_types": "FULLTIME",  # Focus on full-time positions
		}

		# Build query string with proper URL encoding
		query_string = urlencode(params)
		return f"{self.base_url}?{query_string}"

	def _get_headers(self) -> Dict[str, str]:
		"""Override headers to include RapidAPI key"""
		base_headers = super()._get_headers()
		base_headers.update(
			{
				"X-RapidAPI-Key": self.api_key,
				"X-RapidAPI-Host": "jsearch.p.rapidapi.com",
			}
		)
		return base_headers

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
		"""Search for jobs using RapidAPI JSEarch"""
		jobs: List[JobCreate] = []
		page = 1

		# JSEarch typically returns 10 jobs per page
		max_pages = min(5, (max_results + 9) // 10)

		while len(jobs) < max_results and page <= max_pages:
			url = self._build_search_url(keywords, location, page)
			response = await self._make_request(url)

			if response and response.status_code == 200:
				data = response.json()
				results = data.get("data", [])

				if not results:
					logger.info(f"No more jobs found on RapidAPI JSEarch for keywords: {keywords}, location: {location}")
					break

				for job_data in results:
					parsed_job = self._parse_job_listing(job_data)
					if parsed_job:
						job_create_obj = self._create_job_object(parsed_job)
						if job_create_obj:
							jobs.append(job_create_obj)
							if len(jobs) >= max_results:
								break

				page += 1
			else:
				logger.error(f"Failed to fetch jobs from RapidAPI JSEarch. Response: {response.text if response else 'No response'}")
				break

		logger.info(f"RapidAPI JSEarch scraper found {len(jobs)} jobs")
		return jobs

	def _parse_job_listing(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		"""Parse a single job listing from RapidAPI JSEarch response"""
		try:
			# Extract salary info
			salary_min = job_data.get("job_min_salary")
			salary_max = job_data.get("job_max_salary")
			salary_currency = job_data.get("job_salary_currency", "USD")

			salary_string = ""
			if salary_min and salary_max:
				salary_string = f"{salary_currency} {salary_min:,.0f}-{salary_max:,.0f}"
			elif salary_min:
				salary_string = f"{salary_currency} {salary_min:,.0f}+"

			# Determine if remote
			is_remote = job_data.get("job_is_remote", False)

			# Extract employment type
			employment_type = job_data.get("job_employment_type", "")

			# Extract required skills (if available)
			required_skills = job_data.get("job_required_skills", [])

			# Get highlights (benefits, qualifications, responsibilities)
			highlights = job_data.get("job_highlights", {})
			responsibilities = " ".join(highlights.get("Responsibilities", []))
			qualifications = " ".join(highlights.get("Qualifications", []))

			# Build location string safely
			location_parts = []
			if job_data.get("job_city"):
				location_parts.append(job_data.get("job_city"))
			if job_data.get("job_state"):
				location_parts.append(job_data.get("job_state"))
			if job_data.get("job_country"):
				location_parts.append(job_data.get("job_country"))

			location = ", ".join(location_parts) if location_parts else "Remote"

			return {
				"title": job_data.get("job_title"),
				"company": job_data.get("employer_name", ""),
				"location": location,
				"description": job_data.get("job_description", ""),
				"url": job_data.get("job_apply_link", ""),
				"salary": salary_string,
				"job_type": employment_type,
				"remote": is_remote,
				"tech_stack": required_skills,
				"responsibilities": responsibilities,
				"source": f"{self.name} ({job_data.get('job_publisher', 'Unknown')})",
				"currency": salary_currency,
				"requirements": qualifications,
			}
		except Exception as e:
			logger.error(f"Error parsing RapidAPI JSEarch job listing: {e}")
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
