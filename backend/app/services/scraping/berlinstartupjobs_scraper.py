"""
Berlin Startup Jobs Scraper - Berlin tech startup jobs with visa sponsorship
https://berlinstartupjobs.com/
"""

import logging
from typing import List, Optional
from datetime import datetime

from app.schemas.job import JobCreate
from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class BerlinStartupJobsScraper(BaseScraper):
	"""Scraper for Berlin Startup Jobs with visa sponsorship and AI filters"""

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.base_url = "https://berlinstartupjobs.com"
		self.name = "BerlinStartupJobs"

	async def search_jobs(
		self,
		keywords: str = "AI",
		location: str = "Berlin",
		max_results: int = 25,
		visa_sponsorship: bool = True,
	) -> List[JobCreate]:
		"""
		Search for jobs on Berlin Startup Jobs
		
		Args:
			keywords: Job search keywords (e.g., "AI", "Data Science", "Machine Learning")
			location: Location filter (default: Berlin)
			max_results: Maximum number of jobs to return
			visa_sponsorship: Filter for visa sponsorship jobs only
			
		Returns:
			List of JobCreate objects
		"""
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		logger.info(f"Searching Berlin Startup Jobs for '{keywords}' (visa_sponsorship={visa_sponsorship})")

		jobs = []
		
		try:
			# Build search URL with filters
			# Berlin Startup Jobs uses URL parameters for filtering
			search_terms = []
			
			if keywords:
				search_terms.append(f"skill/{keywords.lower()}")
			
			if visa_sponsorship:
				search_terms.append("visa-sponsorship/yes")
			
			# Construct URL
			if search_terms:
				search_url = f"{self.base_url}/{'/'.join(search_terms)}/"
			else:
				search_url = f"{self.base_url}/jobs/"
			
			logger.info(f"Fetching jobs from: {search_url}")
			
			# Fetch the page
			response = await self._make_request(search_url)
			
			if not response:
				logger.warning("Failed to fetch Berlin Startup Jobs")
				return []
			
			# Parse HTML
			soup = self._parse_html(response.text)
			
			# Find job listings - adjust selectors based on actual HTML structure
			job_cards = soup.find_all("div", class_=lambda x: x and ("job" in x.lower() or "listing" in x.lower()))
			
			if not job_cards:
				# Try alternative selectors
				job_cards = soup.find_all("article") or soup.find_all("li", class_="job")
			
			logger.info(f"Found {len(job_cards)} job cards")
			
			# Parse each job card
			for card in job_cards[:max_results]:
				job = self._parse_job_card(card)
				if job:
					jobs.append(job)
			
		except Exception as e:
			logger.error(f"Error searching Berlin Startup Jobs: {e}", exc_info=True)
		
		logger.info(f"Berlin Startup Jobs search completed: {len(jobs)} jobs found")
		return jobs[:max_results]

	def _parse_job_card(self, card) -> Optional[JobCreate]:
		"""Parse a single job card from HTML"""
		try:
			# Extract title
			title_elem = card.find("h2") or card.find("h3") or card.find("a", class_=lambda x: x and "title" in x.lower())
			title = self._clean_text(title_elem.get_text()) if title_elem else ""
			
			# Extract company
			company_elem = card.find(class_=lambda x: x and "company" in x.lower())
			company = self._clean_text(company_elem.get_text()) if company_elem else ""
			
			# If company not found, try alternative
			if not company:
				company_elem = card.find("a", href=lambda x: x and "/company/" in x) if card.find("a") else None
				company = self._clean_text(company_elem.get_text()) if company_elem else "Berlin Startup"
			
			if not title:
				return None
			
			# Extract URL
			url_elem = card.find("a", href=True)
			url = url_elem["href"] if url_elem else ""
			if url and not url.startswith("http"):
				url = f"{self.base_url}{url}"
			
			# Extract description
			desc_elem = card.find(class_=lambda x: x and ("description" in x.lower() or "excerpt" in x.lower()))
			description = self._clean_text(desc_elem.get_text()) if desc_elem else ""
			
			# Extract location
			location_elem = card.find(class_=lambda x: x and "location" in x.lower())
			location = self._clean_text(location_elem.get_text()) if location_elem else "Berlin, Germany"
			
			# Check for remote
			remote_option = "hybrid"
			text_content = card.get_text().lower()
			if "remote" in text_content:
				remote_option = "remote"
			elif "office" in text_content or "on-site" in text_content:
				remote_option = "on-site"
			
			# Extract job type
			job_type = "Full-time"
			if "part-time" in text_content:
				job_type = "Part-time"
			elif "contract" in text_content:
				job_type = "Contract"
			
			# Build job object
			job = JobCreate(
				title=title,
				company=company,
				location=location,
				description=description or f"{title} position at {company}",
				url=url or self.base_url,
				source="BerlinStartupJobs",
				job_type=job_type,
				remote_option=remote_option,
				posted_date=datetime.now(),
				salary_min=None,
				salary_max=None,
				salary_currency="EUR",
				requires_visa_sponsorship=True,
			)
			
			return job
			
		except Exception as e:
			logger.error(f"Error parsing Berlin Startup Jobs card: {e}", exc_info=True)
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
