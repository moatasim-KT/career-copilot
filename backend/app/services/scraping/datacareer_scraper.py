"""DataCareer.eu scraper for continental data science roles."""

from __future__ import annotations

import logging
from typing import ClassVar, List, Optional

import feedparser

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class DataCareerScraper(BaseScraper):
	"""Consumes DataCareer.eu RSS feed, filtering to onsite EU DS/ML roles."""

	FEED_URL: ClassVar[str] = "https://www.datacareer.eu/jobs?format=rss"
	EU_LOCATIONS: ClassVar[List[str]] = [
		"Switzerland",
		"Zurich",
		"Geneva",
		"Germany",
		"Austria",
		"Netherlands",
		"Belgium",
		"France",
		"Spain",
		"Portugal",
		"Italy",
		"Sweden",
		"Denmark",
		"Finland",
		"Norway",
		"Ireland",
	]
	KEYWORDS: ClassVar[List[str]] = [
		"data scientist",
		"data engineer",
		"analytics",
		"ml",
		"machine learning",
		"ai",
	]

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.name = "DataCareer"

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 40) -> List[JobCreate]:
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		response = await self._make_request(self.FEED_URL)
		if not response:
			return []

		feed = feedparser.parse(response.text)
		jobs: List[JobCreate] = []
		keyword_terms = self._normalize_terms(keywords)

		for entry in feed.entries:
			if len(jobs) >= max_results:
				break

			title = entry.get("title", "").strip()
			summary = entry.get("summary", "")
			if "remote" in summary.lower() or "remote" in title.lower():
				continue

			text_blob = f"{title} {summary}".lower()
			if keyword_terms and not any(term in text_blob for term in keyword_terms):
				continue

			if not keyword_terms and not any(term in text_blob for term in self.KEYWORDS):
				continue

			location_guess = self._infer_location(summary)
			if location and location.lower() not in location_guess.lower():
				continue

			job_data = {
				"title": title or "DataCareer Listing",
				"company": entry.get("author", "DataCareer Partner"),
				"location": location_guess,
				"description": summary,
				"requirements": summary,
				"job_type": "Full-time",
				"remote_option": "on-site",
				"application_url": entry.get("link", self.FEED_URL),
				"source": "scraped",
			}

			job = self._create_job_object(job_data)
			if job:
				jobs.append(job)

		logger.info("DataCareer scraper produced %d EU onsite roles", len(jobs))
		return jobs

	def _normalize_terms(self, keywords: str) -> List[str]:
		return [term.strip().lower() for term in keywords.split(",") if term.strip()]

	def _infer_location(self, summary: str) -> str:
		summary_lower = summary.lower()
		for loc in self.EU_LOCATIONS:
			if loc.lower() in summary_lower:
				return loc
		return "European Union"

	def _parse_job_listing(self, job_element) -> Optional[dict]:
		return job_element if isinstance(job_element, dict) else None

	def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
		return self.FEED_URL
