"""EuroTechJobs scraper focused on EU Data Science & ML listings."""

from __future__ import annotations

import logging
from typing import ClassVar, List, Optional

import feedparser

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class EuroTechJobsScraper(BaseScraper):
	"""Consumes EuroTechJobs RSS feeds for DS/ML-focused onsite roles across the EU."""

	FEED_URL: ClassVar[str] = "https://www.eurotechjobs.com/jobs/machine-learning.rss"
	KEYWORDS: ClassVar[List[str]] = [
		"data scientist",
		"data science",
		"machine learning",
		"ml engineer",
		"ai engineer",
		"ai scientist",
		"computer vision",
	]
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
		"Norway",
		"Ireland",
		"Belgium",
		"Austria",
		"Poland",
		"Czech Republic",
		"Switzerland",
		"Luxembourg",
	]

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.name = "EuroTechJobs"

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
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
			link = entry.get("link", self.FEED_URL)

			if "remote" in title.lower() or "remote" in summary.lower():
				continue

			if keyword_terms and not any(term in title.lower() for term in keyword_terms):
				continue

			if not keyword_terms and not any(term in title.lower() for term in self.KEYWORDS):
				continue

			location_guess = self._infer_location(summary)
			if location and location.lower() not in location_guess.lower():
				continue

			job_data = {
				"title": title or "EuroTechJobs Listing",
				"company": self._extract_company(entry),
				"location": location_guess,
				"description": summary,
				"requirements": summary,
				"job_type": "Full-time",
				"remote_option": "on-site",
				"application_url": link,
				"source": "scraped",
			}

			job = self._create_job_object(job_data)
			if job:
				jobs.append(job)

		logger.info("EuroTechJobs scraper produced %d jobs", len(jobs))
		return jobs

	def _normalize_terms(self, keywords: str) -> List[str]:
		return [term.strip().lower() for term in keywords.split(",") if term.strip()]

	def _infer_location(self, summary: str) -> str:
		summary_lower = summary.lower()
		for country in self.EU_COUNTRIES:
			if country.lower() in summary_lower:
				return country
		return "European Union"

	def _extract_company(self, entry: feedparser.FeedParserDict) -> str:
		title = entry.get("title", "")
		if " at " in title:
			return title.split(" at ")[-1].strip()
		return entry.get("author", "EuroTechJobs Partner")

	def _parse_job_listing(self, job_element) -> Optional[dict]:
		return job_element if isinstance(job_element, dict) else None

	def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
		return self.FEED_URL
