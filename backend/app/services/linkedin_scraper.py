"""Production-grade LinkedIn Scraper.

Features:
- Session management with cookie persistence
- Rate limiting and request throttling
- Anti-detection measures
- Proxy support
- Job scraping with pagination
- Comprehensive error handling and retry logic
- Logging and monitoring
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional
from urllib.parse import urlencode, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkedInScraper:
	"""
	Production-grade LinkedIn job scraper.

	Handles rate limiting, session management, anti-detection,
	and comprehensive job data extraction.
	"""

	# User agents for rotation
	USER_AGENTS: ClassVar[List[str]] = [
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
	]

	def __init__(
		self,
		cookies_file: str | None = None,
		proxy: str | None = None,
		rate_limit_requests: int = 10,
		rate_limit_window: int = 60,
		min_delay: float = 2.0,
		max_delay: float = 5.0,
	) -> None:
		"""
		Initialize LinkedIn scraper.

		Args:
		    cookies_file: Path to cookies JSON file
		    proxy: Proxy URL (e.g., "http://proxy:8080")
		    rate_limit_requests: Max requests per window
		    rate_limit_window: Rate limit window in seconds
		    min_delay: Minimum delay between requests (seconds)
		    max_delay: Maximum delay between requests (seconds)
		"""
		self.cookies_file = Path(cookies_file) if cookies_file else None
		self.proxy = proxy
		self.rate_limit_requests = rate_limit_requests
		self.rate_limit_window = rate_limit_window
		self.min_delay = min_delay
		self.max_delay = max_delay

		# Rate limiting tracking
		self.request_timestamps: List[float] = []

		# Session management
		self.cookies: Dict[str, str] = {}
		if self.cookies_file and self.cookies_file.exists():
			self._load_cookies()

		# Statistics
		self.stats = {
			"requests_made": 0,
			"jobs_scraped": 0,
			"errors": 0,
			"rate_limit_hits": 0,
		}

		logger.info("LinkedInScraper initialized with rate limit %d/%ds", rate_limit_requests, rate_limit_window)

	def _load_cookies(self) -> None:
		"""Load cookies from file."""
		try:
			if self.cookies_file and self.cookies_file.exists():
				with self.cookies_file.open() as f:
					self.cookies = json.load(f)
				logger.info("Loaded %d cookies from %s", len(self.cookies), self.cookies_file)
		except Exception as e:
			logger.error(f"Failed to load cookies: {e!s}")

	def _save_cookies(self, response_cookies: httpx.Cookies) -> None:
		"""Save cookies to file."""
		try:
			if self.cookies_file:
				# Update cookies dict
				for name, value in response_cookies.items():
					self.cookies[name] = value

				# Save to file
				self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
				with self.cookies_file.open("w") as f:
					json.dump(self.cookies, f, indent=2)
				logger.debug("Saved cookies to %s", self.cookies_file)
		except Exception as e:
			logger.error(f"Failed to save cookies: {e!s}")

	def _get_random_user_agent(self) -> str:
		"""Get random user agent for anti-detection."""
		return random.choice(self.USER_AGENTS)

	def _get_headers(self) -> Dict[str, str]:
		"""Get request headers with random user agent."""
		return {
			"User-Agent": self._get_random_user_agent(),
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"Accept-Language": "en-US,en;q=0.5",
			"Accept-Encoding": "gzip, deflate, br",
			"DNT": "1",
			"Connection": "keep-alive",
			"Upgrade-Insecure-Requests": "1",
			"Sec-Fetch-Dest": "document",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "none",
			"Cache-Control": "max-age=0",
		}

	async def _check_rate_limit(self) -> None:
		"""Check and enforce rate limiting."""
		current_time = time.time()

		# Remove old timestamps outside window
		cutoff = current_time - self.rate_limit_window
		self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff]

		# Check if we've hit the limit
		if len(self.request_timestamps) >= self.rate_limit_requests:
			# Calculate wait time
			oldest = self.request_timestamps[0]
			wait_time = self.rate_limit_window - (current_time - oldest)

			if wait_time > 0:
				self.stats["rate_limit_hits"] += 1
				logger.warning(f"Rate limit hit, waiting {wait_time:.1f}s")
				await asyncio.sleep(wait_time)

		# Add current timestamp
		self.request_timestamps.append(current_time)

	async def _random_delay(self) -> None:
		"""Add random delay between requests for anti-detection."""
		delay = random.uniform(self.min_delay, self.max_delay)
		await asyncio.sleep(delay)

	async def _make_request(
		self,
		url: str,
		params: Dict[str, Any] | None = None,
		retries: int = 3,
	) -> httpx.Response | None:
		"""
		Make HTTP request with retry logic.

		Args:
		    url: URL to request
		    params: Query parameters
		    retries: Number of retries on failure

		Returns:
		    Response or None on failure
		"""
		# Enforce rate limiting
		await self._check_rate_limit()

		# Random delay for anti-detection
		await self._random_delay()

		headers = self._get_headers()

		for attempt in range(retries):
			try:
				async with httpx.AsyncClient(
					cookies=self.cookies,
					proxies=self.proxy,
					timeout=30.0,
					follow_redirects=True,
				) as client:
					response = await client.get(url, headers=headers, params=params)

					# Save cookies from response
					if response.cookies:
						self._save_cookies(response.cookies)

					self.stats["requests_made"] += 1

					# Check for rate limiting response
					if response.status_code == 429:
						wait_time = int(response.headers.get("Retry-After", 60))
						logger.warning(f"LinkedIn rate limit (429), waiting {wait_time}s")
						await asyncio.sleep(wait_time)
						continue

					response.raise_for_status()
					return response

			except httpx.HTTPStatusError as e:
				logger.error(f"HTTP error on attempt {attempt + 1}: {e!s}")
				self.stats["errors"] += 1

				if attempt < retries - 1:
					# Exponential backoff
					wait = 2**attempt
					await asyncio.sleep(wait)
				else:
					return None

			except Exception as e:
				logger.error(f"Request error on attempt {attempt + 1}: {e!s}")
				self.stats["errors"] += 1

				if attempt < retries - 1:
					await asyncio.sleep(2**attempt)
				else:
					return None

		return None

	async def search_jobs(
		self,
		keywords: str | None = None,
		location: str | None = None,
		experience_level: str | None = None,
		job_type: str | None = None,
		max_pages: int = 5,
	) -> List[Dict[str, Any]]:
		"""
		Search LinkedIn jobs.

		Args:
		    keywords: Job keywords (e.g., "Python Developer")
		    location: Location (e.g., "San Francisco, CA")
		    experience_level: Experience level filter
		    job_type: Job type (full-time, contract, etc.)
		    max_pages: Maximum pages to scrape

		Returns:
		    List of job dictionaries
		"""
		jobs = []

		# Build search URL
		base_url = "https://www.linkedin.com/jobs/search/"

		for page in range(max_pages):
			try:
				# Build query parameters
				params: Dict[str, Any] = {"start": page * 25}

				if keywords:
					params["keywords"] = keywords
				if location:
					params["location"] = location
				if experience_level:
					params["f_E"] = experience_level
				if job_type:
					params["f_JT"] = job_type

				logger.info(f"Searching jobs page {page + 1}/{max_pages}")

				# Make request
				response = await self._make_request(base_url, params=params)

				if not response:
					logger.error(f"Failed to get page {page + 1}")
					break

				# Parse jobs
				page_jobs = self._parse_job_listings(response.text)
				jobs.extend(page_jobs)

				logger.info(f"Found {len(page_jobs)} jobs on page {page + 1}")

				# Stop if no more jobs
				if not page_jobs:
					break

			except Exception as e:
				logger.error(f"Error scraping page {page + 1}: {e!s}")
				break

		self.stats["jobs_scraped"] += len(jobs)
		logger.info(f"Total jobs scraped: {len(jobs)}")

		return jobs

	def _parse_job_listings(self, html: str) -> List[Dict[str, Any]]:
		"""
		Parse job listings from HTML.

		Args:
		    html: HTML content

		Returns:
		    List of job dictionaries
		"""
		jobs = []

		try:
			soup = BeautifulSoup(html, "html.parser")

			# Find job cards
			job_cards = soup.find_all("div", class_="base-card")

			for card in job_cards:
				try:
					job_data = self._extract_job_data(card)
					if job_data:
						jobs.append(job_data)
				except Exception as e:
					logger.error(f"Error parsing job card: {e!s}")
					continue

		except Exception as e:
			logger.error(f"Error parsing job listings: {e!s}")

		return jobs

	def _extract_job_data(self, card: Any) -> Dict[str, Any] | None:
		"""
		Extract job data from job card.

		Args:
		    card: BeautifulSoup job card element

		Returns:
		    Job dictionary or None
		"""
		try:
			# Extract job title
			title_elem = card.find("h3", class_="base-search-card__title")
			title = title_elem.get_text(strip=True) if title_elem else None

			# Extract company
			company_elem = card.find("h4", class_="base-search-card__subtitle")
			company = company_elem.get_text(strip=True) if company_elem else None

			# Extract location
			location_elem = card.find("span", class_="job-search-card__location")
			location = location_elem.get_text(strip=True) if location_elem else None

			# Extract job link
			link_elem = card.find("a", class_="base-card__full-link")
			job_url = link_elem.get("href") if link_elem else None

			# Extract job ID from URL
			job_id = None
			if job_url:
				parsed = urlparse(job_url)
				path_parts = parsed.path.split("/")
				if "view" in path_parts:
					idx = path_parts.index("view")
					if idx + 1 < len(path_parts):
						job_id = path_parts[idx + 1].split("?")[0]

			# Extract posted date
			posted_elem = card.find("time", class_="job-search-card__listdate")
			posted_date = posted_elem.get("datetime") if posted_elem else None

			if not title or not company:
				return None

			return {
				"job_id": job_id,
				"title": title,
				"company": company,
				"location": location,
				"url": job_url,
				"posted_date": posted_date,
				"scraped_at": datetime.now(timezone.utc).isoformat(),
			}

		except Exception as e:
			logger.error(f"Error extracting job data: {e!s}")
			return None

	async def get_job_details(self, job_url: str) -> Dict[str, Any] | None:
		"""
		Get detailed job information.

		Args:
		    job_url: Job URL

		Returns:
		    Detailed job dictionary or None
		"""
		try:
			response = await self._make_request(job_url)

			if not response:
				return None

			soup = BeautifulSoup(response.text, "html.parser")

			# Extract description
			desc_elem = soup.find("div", class_="show-more-less-html__markup")
			description = desc_elem.get_text(strip=True) if desc_elem else None

			# Extract criteria
			criteria = {}
			criteria_items = soup.find_all("li", class_="description__job-criteria-item")
			for item in criteria_items:
				header = item.find("h3")
				value = item.find("span")
				if header and value:
					key = header.get_text(strip=True).lower().replace(" ", "_")
					criteria[key] = value.get_text(strip=True)

			return {
				"url": job_url,
				"description": description,
				"criteria": criteria,
				"scraped_at": datetime.now(timezone.utc).isoformat(),
			}

		except Exception as e:
			logger.error(f"Error getting job details: {e!s}")
			return None

	def get_stats(self) -> Dict[str, Any]:
		"""Get scraper statistics."""
		return dict(self.stats)

	async def health_check(self) -> Dict[str, Any]:
		"""
		Perform health check.

		Returns:
		    Health status
		"""
		try:
			# Try to access LinkedIn homepage
			response = await self._make_request("https://www.linkedin.com")

			if response and response.status_code == 200:
				return {
					"status": "healthy",
					"stats": self.get_stats(),
				}

			return {"status": "degraded", "message": "Failed to reach LinkedIn"}

		except Exception as e:
			logger.error(f"Health check failed: {e!s}")
			return {"status": "unhealthy", "error": str(e)}
