"""EU Tech Jobs scraper pulling relocation-friendly postings from RSS."""

from __future__ import annotations

import logging
from typing import ClassVar, List, Optional

import feedparser

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class EUTechJobsScraper(BaseScraper):
	"""Consumes the EU Tech Jobs RSS feed and normalizes listings for ingestion."""

	FEED_URL: ClassVar[str] = "https://eutechjobs.com/feed"
	EU_COUNTRIES: ClassVar[List[str]] = [
		"Germany",
		"Netherlands",
		"France",
		"Spain",
		"Portugal",
		"Italy",
		"Sweden",
		"Finland",
		"Denmark",
		"Ireland",
		"Belgium",
		"Austria",
		"Switzerland",
		"Poland",
		"Czech Republic",
		"Estonia",
	]
	VISA_DENOTATIONS: ClassVar[List[str]] = ["visa", "relocation", "sponsorship", "eu blue card"]

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.name = "EUTechJobs"

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		response = await self._make_request(self.FEED_URL)
		if not response:
			return []

		feed = feedparser.parse(response.text)
		jobs: List[JobCreate] = []
		keyword_terms = [term.strip().lower() for term in keywords.split(",") if term.strip()]

		for entry in feed.entries:
			if len(jobs) >= max_results:
				break

			title = entry.get("title", "").strip()
			summary = entry.get("summary", "")
			location_guess = self._guess_location(title, summary)

			if location and location.lower() not in location_guess.lower():
				continue

			if keyword_terms and not any(term in title.lower() for term in keyword_terms):
				continue

			if "remote" in title.lower() or "remote" in summary.lower():
				continue

			job_data = {
				"title": title or "EU Tech Job",
				"company": self._extract_company(entry),
				"location": location_guess,
				"description": summary,
				"requirements": summary,
				"job_type": "Full-time",
				"remote_option": "on-site",
				"application_url": entry.get("link", self.FEED_URL),
				"source": "scraped",
			}

			if any(marker in summary.lower() for marker in self.VISA_DENOTATIONS):
				job_data["notes"] = "Mentions relocation/visa assistance"

			job = self._create_job_object(job_data)
			if job:
				jobs.append(job)

		logger.info("EU Tech Jobs scraper produced %d postings", len(jobs))
		return jobs

	def _guess_location(self, title: str, summary: str) -> str:
		text = f"{title} {summary}".lower()
		for country in self.EU_COUNTRIES:
			if country.lower() in text:
				return country
		return "European Union"

	def _extract_company(self, entry: feedparser.FeedParserDict) -> str:
		title = entry.get("title", "")
		if " at " in title:
			return title.split(" at ")[-1].strip()
		return entry.get("author", "EU Tech Jobs Partner")

	def _parse_job_listing(self, job_element) -> Optional[dict]:
		return job_element if isinstance(job_element, dict) else None

	def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
		return self.FEED_URL
