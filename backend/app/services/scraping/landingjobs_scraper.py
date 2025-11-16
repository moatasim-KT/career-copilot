"""Landing.jobs scraper focused on EU relocation/visa-friendly roles."""

from __future__ import annotations

import logging
from typing import ClassVar, List, Optional

import feedparser

from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)


class LandingJobsScraper(BaseScraper):
	"""Scrapes Landing.jobs RSS feed for on-site EU roles with relocation support."""

	FEED_URL = "https://landing.jobs/feed"
	EU_LOCATIONS: ClassVar[List[str]] = [
		"Portugal",
		"Lisbon",
		"Porto",
		"Germany",
		"Berlin",
		"Munich",
		"Netherlands",
		"Amsterdam",
		"Spain",
		"Barcelona",
		"Madrid",
		"France",
		"Paris",
		"Italy",
		"Milan",
		"Sweden",
		"Stockholm",
		"Denmark",
		"Copenhagen",
		"Ireland",
		"Dublin",
		"Austria",
		"Vienna",
		"Belgium",
		"Brussels",
	]
	VISA_KEYWORDS: ClassVar[List[str]] = ["visa", "relocation", "sponsor", "blue card", "work permit"]
	REMOTE_KEYWORDS: ClassVar[List[str]] = ["remote", "anywhere", "hybrid", "global"]

	def __init__(self, rate_limiter: Optional[RateLimiter] = None):
		super().__init__(rate_limiter)
		self.name = "LandingJobs"

	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		logger.info("Fetching Landing.jobs feed for EU on-site opportunities")
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
			if any(word in summary.lower() or word in title.lower() for word in self.REMOTE_KEYWORDS):
				continue  # Skip remote-first postings

			if keyword_terms and not any(term in title.lower() for term in keyword_terms):
				continue

			location_guess = self._extract_location(summary)
			if location and location.lower() not in location_guess.lower():
				continue

			job_data = {
				"title": title or "Landing.jobs Opportunity",
				"company": self._extract_company_name(entry),
				"location": location_guess,
				"description": summary,
				"requirements": summary,
				"job_type": "Full-time",
				"remote_option": "on-site",
				"application_url": entry.get("link", self.FEED_URL),
				"source": "scraped",
			}

			# Flag visa-friendly postings
			if any(keyword in summary.lower() for keyword in self.VISA_KEYWORDS):
				job_data["notes"] = "Highlights relocation/visa support"

			job = self._create_job_object(job_data)
			if job:
				jobs.append(job)

		logger.info("Landing.jobs scraper produced %d jobs", len(jobs))
		return jobs

	def _extract_location(self, summary: str) -> str:
		summary_lower = summary.lower()
		for city in self.EU_LOCATIONS:
			if city.lower() in summary_lower:
				return city
		return "European Union"

	def _extract_company_name(self, entry: feedparser.FeedParserDict) -> str:
		tags = entry.get("tags", [])
		for tag in tags:
			label = tag.get("term", "").strip()
			if label and label not in {"jobs", "landing.jobs"}:
				return label
		return "Landing.jobs Company"

	def _parse_job_listing(self, job_element) -> Optional[dict]:
		return job_element if isinstance(job_element, dict) else None

	def _build_search_url(self, keywords: str, location: str = "", page: int = 0) -> str:
		return self.FEED_URL
