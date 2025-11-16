"""Headless Playwright scraper for EU companies known to sponsor visas."""

from __future__ import annotations

import asyncio
import logging
from typing import ClassVar, Dict, List, Optional

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class EUCompanyPlaywrightScraper(BaseScraper):
	"""Uses Playwright to scan curated EU company career pages for tech roles."""

	TARGET_COMPANIES: ClassVar[List[Dict[str, str]]] = [
		{"name": "Spotify", "url": "https://www.lifeatspotify.com/jobs", "location": "Stockholm, Sweden"},
		{"name": "Adyen", "url": "https://careers.adyen.com/vacancies", "location": "Amsterdam, Netherlands"},
		{"name": "Wise", "url": "https://www.wise.jobs", "location": "London, United Kingdom"},
		{"name": "DeepMind", "url": "https://www.deepmind.com/careers", "location": "London, United Kingdom"},
		{"name": "N26", "url": "https://n26.com/en/careers", "location": "Berlin, Germany"},
		{"name": "Zalando", "url": "https://jobs.zalando.com/en/tech/", "location": "Berlin, Germany"},
		{"name": "Bolt", "url": "https://bolt.eu/en/careers/positions/", "location": "Tallinn, Estonia"},
		{"name": "Northvolt", "url": "https://careers.northvolt.com/jobs", "location": "Stockholm, Sweden"},
		{"name": "SAP", "url": "https://jobs.sap.com", "location": "Walldorf, Germany"},
		{"name": "Booking.com", "url": "https://careers.booking.com", "location": "Amsterdam, Netherlands"},
	]
	KEYWORD_FILTERS: ClassVar[List[str]] = [
		"engineer",
		"developer",
		"science",
		"machine learning",
		"data",
		"cloud",
		"ai",
	]
	MAX_LINKS_PER_COMPANY: ClassVar[int] = 5

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.name = "EUCompanyPlaywright"
		self._playwright = None
		self._browser = None

	async def __aenter__(self):
		await super().__aenter__()
		self._playwright = await async_playwright().start()
		self._browser = await self._playwright.chromium.launch(headless=True)
		return self

	async def __aexit__(self, exc_type, exc, tb):
		if self._browser:
			await self._browser.close()
		if self._playwright:
			await self._playwright.stop()
		await super().__aexit__(exc_type, exc, tb)

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 40) -> List[JobCreate]:
		if not self._browser:
			raise RuntimeError(
				"Playwright browser not initialized. Run inside async context manager and install browsers via 'playwright install chromium'."
			)

		jobs: List[JobCreate] = []
		keyword_terms = [term.strip().lower() for term in keywords.split(",") if term.strip()]

		for company in self.TARGET_COMPANIES:
			if len(jobs) >= max_results:
				break

			if location and location.lower() not in company["location"].lower():
				continue

			company_jobs = await self._scrape_company(company, keyword_terms, max_results - len(jobs))
			jobs.extend(company_jobs)

		logger.info("EU company Playwright scraper produced %d curated postings", len(jobs))
		return jobs

	async def _scrape_company(self, company: Dict[str, str], keyword_terms: List[str], remaining_budget: int) -> List[JobCreate]:
		context = await self._browser.new_context()
		page = await context.new_page()
		collected: List[JobCreate] = []

		try:
			await page.goto(company["url"], wait_until="networkidle", timeout=45000)
			await asyncio.sleep(1.5)  # allow lazy-loaded cards

			link_data = await page.evaluate(
				"""
				() => {
				  return Array.from(document.querySelectorAll('a[href]'))
				    .map(a => ({ text: a.innerText.trim(), href: a.href }))
				    .filter(item => item.text && item.href);
				}
				"""
			)

			relevant_links = self._filter_links(link_data, keyword_terms)

			for link in relevant_links[: self.MAX_LINKS_PER_COMPANY]:
				if len(collected) >= remaining_budget:
					break

				job_data = {
					"title": link["text"],
					"company": company["name"],
					"location": company["location"],
					"description": f"Opportunity discovered on {company['name']} careers page.",
					"requirements": "Visa-friendly EU employer",
					"job_type": "Full-time",
					"remote_option": "on-site",
					"application_url": link["href"],
					"source": "scraped",
				}

				job = self._create_job_object(job_data)
				if job:
					collected.append(job)

		except PlaywrightTimeoutError:
			logger.warning("Timed out loading %s", company["url"])
		except Exception as exc:  # pragma: no cover - defensive logging
			logger.error("Failed to scrape %s: %s", company["name"], exc)
		finally:
			await context.close()

		return collected

	def _filter_links(self, link_data: List[Dict[str, str]], keyword_terms: List[str]) -> List[Dict[str, str]]:
		relevant = []
		for link in link_data:
			text_lower = link["text"].lower()
			if "remote" in text_lower:
				continue

			if keyword_terms and not any(term in text_lower for term in keyword_terms):
				continue

			if not keyword_terms and not any(keyword in text_lower for keyword in self.KEYWORD_FILTERS):
				continue

			relevant.append(link)

		return relevant

	def _parse_job_listing(self, job_element) -> Optional[dict]:
		return job_element if isinstance(job_element, dict) else None

	def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
		return "playwright://eu-company-careers"
