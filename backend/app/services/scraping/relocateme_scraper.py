"""
Relocate.me Scraper - Tech jobs with relocation and visa support
https://relocate.me/
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class RelocateMeScraper(BaseScraper):
	"""Scraper for Relocate.me - specialized in tech jobs with relocation support"""

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.base_url = "https://relocate.me"
		self.api_url = "https://relocate.me/api/jobs"
		self.name = "RelocateMe"

	async def search_jobs(
		self,
		keywords: str = "",
		location: str = "Europe",
		max_results: int = 25,
		job_category: str = "data-science",
	) -> List[JobCreate]:
		"""
		Search for jobs on Relocate.me

		Args:
			keywords: Job search keywords
			location: Region filter (default: Europe)
			max_results: Maximum number of jobs to return
			job_category: Category filter (data-science, ai, machine-learning, software-engineering)

		Returns:
			List of JobCreate objects
		"""
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		logger.info(f"Searching Relocate.me for '{keywords}' in {location}")

		jobs = []
		page = 1

		try:
			while len(jobs) < max_results:
				# Build query parameters
				params = {
					"search": keywords or "",
					"location": location,
					"page": page,
					"per_page": min(25, max_results),
				}

				if job_category:
					params["category"] = job_category

				# Try API endpoint first
				response = await self._make_request(self.api_url, params=params)

				if response and response.status_code == 200:
					try:
						data = response.json()
						job_listings = data.get("jobs", []) or data.get("data", [])

						if not job_listings:
							break

						for job_data in job_listings:
							if len(jobs) >= max_results:
								break
							job = self._parse_api_job(job_data)
							if job:
								jobs.append(job)

						page += 1

					except Exception as e:
						logger.warning(f"API parsing failed, falling back to HTML scraping: {e}")
						# Fall back to HTML scraping
						html_jobs = await self._scrape_html(keywords, location, max_results)
						jobs.extend(html_jobs)
						break
				else:
					# Fallback to HTML scraping
					html_jobs = await self._scrape_html(keywords, location, max_results)
					jobs.extend(html_jobs)
					break

		except Exception as e:
			logger.error(f"Error searching Relocate.me: {e}", exc_info=True)

		logger.info(f"Relocate.me search completed: {len(jobs)} jobs found")
		return jobs[:max_results]

	async def _scrape_html(self, keywords: str, location: str, max_results: int) -> List[JobCreate]:
		"""Fallback HTML scraping method"""
		jobs = []

		try:
			# Build search URL
			search_url = f"{self.base_url}/search"
			params = {}

			if keywords:
				params["q"] = keywords
			if location:
				params["location"] = location

			response = await self._make_request(search_url, params=params)

			if not response:
				return []

			soup = self._parse_html(response.text)

			# Find job listings
			job_cards = soup.find_all("div", class_=lambda x: x and "job" in x.lower())

			if not job_cards:
				job_cards = soup.find_all("article") or soup.find_all("li", attrs={"data-job": True})

			logger.info(f"Found {len(job_cards)} job cards via HTML scraping")

			for card in job_cards[:max_results]:
				job = self._parse_html_job(card)
				if job:
					jobs.append(job)

		except Exception as e:
			logger.error(f"Error in HTML scraping: {e}", exc_info=True)

		return jobs

	def _parse_api_job(self, job_data: dict) -> Optional[JobCreate]:
		"""Parse job from API response"""
		try:
			title = job_data.get("title", "").strip()
			company = job_data.get("company", {}).get("name", "") if isinstance(job_data.get("company"), dict) else job_data.get("company", "")

			if not title or not company:
				return None

			# Extract location
			location_data = job_data.get("location", {})
			if isinstance(location_data, dict):
				city = location_data.get("city", "")
				country = location_data.get("country", "")
				location = f"{city}, {country}".strip(", ")
			else:
				location = str(location_data) if location_data else "Europe"

			# Description
			description = job_data.get("description", "") or job_data.get("summary", "")

			# URL
			job_id = job_data.get("id", "") or job_data.get("slug", "")
			url = f"{self.base_url}/jobs/{job_id}" if job_id else self.base_url

			# Salary
			salary_info = job_data.get("salary", {})
			salary_min = salary_info.get("min") if isinstance(salary_info, dict) else None
			salary_max = salary_info.get("max") if isinstance(salary_info, dict) else None
			salary_currency = salary_info.get("currency", "EUR") if isinstance(salary_info, dict) else "EUR"

			# Remote option
			remote = job_data.get("remote", False)
			remote_option = "remote" if remote else "hybrid"

			job = JobCreate(
				title=title,
				company=company.strip(),
				location=location,
				description=description,
				url=url,
				source="RelocateMe",
				job_type=job_data.get("type", "Full-time"),
				remote_option=remote_option,
				posted_date=datetime.now(),
				salary_min=salary_min,
				salary_max=salary_max,
				salary_currency=salary_currency,
				requires_visa_sponsorship=True,
			)

			return job

		except Exception as e:
			logger.error(f"Error parsing Relocate.me API job: {e}", exc_info=True)
			return None

	def _parse_html_job(self, card) -> Optional[JobCreate]:
		"""Parse job from HTML card"""
		try:
			# Extract title
			title_elem = card.find("h2") or card.find("h3") or card.find(class_=lambda x: x and "title" in x.lower())
			title = self._clean_text(title_elem.get_text()) if title_elem else ""

			# Extract company
			company_elem = card.find(class_=lambda x: x and "company" in x.lower())
			company = self._clean_text(company_elem.get_text()) if company_elem else ""

			if not title:
				return None

			# URL
			url_elem = card.find("a", href=True)
			url = url_elem["href"] if url_elem else ""
			if url and not url.startswith("http"):
				url = f"{self.base_url}{url}"

			# Location
			location_elem = card.find(class_=lambda x: x and "location" in x.lower())
			location = self._clean_text(location_elem.get_text()) if location_elem else "Europe"

			# Description
			desc_elem = card.find(class_=lambda x: x and "description" in x.lower())
			description = self._clean_text(desc_elem.get_text()) if desc_elem else ""

			job = JobCreate(
				title=title,
				company=company or "Unknown Company",
				location=location,
				description=description or f"{title} at {company}",
				url=url or self.base_url,
				source="RelocateMe",
				job_type="Full-time",
				remote_option="hybrid",
				posted_date=datetime.now(),
				salary_min=None,
				salary_max=None,
				salary_currency="EUR",
				requires_visa_sponsorship=True,
			)

			return job

		except Exception as e:
			logger.error(f"Error parsing Relocate.me HTML job: {e}", exc_info=True)
			return None

	def _parse_job_listing(self, job_data) -> Optional[dict]:
		"""Required by base class - parse job listing to dict"""
		if isinstance(job_data, dict):
			job = self._parse_api_job(job_data)
		else:
			job = self._parse_html_job(job_data)

		if job:
			return job.model_dump()
		return None

	def _build_search_url(self, keywords: str, location: str = "Europe", page: int = 1) -> str:
		"""Required by base class - build search URL"""
		params = {
			"search": keywords or "",
			"location": location,
			"page": page,
			"per_page": 25,
		}
		param_str = "&".join([f"{k}={v}" for k, v in params.items() if v])
		return f"{self.api_url}?{param_str}"

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
