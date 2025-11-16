"""
Base scraper class with common functionality for all job board scrapers
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from app.schemas.job import JobCreate

logger = logging.getLogger(__name__)


class RateLimiter:
	"""Rate limiter to ensure respectful scraping"""

	def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
		self.min_delay = min_delay
		self.max_delay = max_delay
		self.last_request_time = 0

	async def wait(self):
		"""Wait for appropriate delay between requests"""
		current_time = time.time()
		elapsed = current_time - self.last_request_time

		# Random delay between min and max
		delay = random.uniform(self.min_delay, self.max_delay)

		if elapsed < delay:
			wait_time = delay - elapsed
			logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
			await asyncio.sleep(wait_time)

		self.last_request_time = time.time()


class BaseScraper(ABC):
	"""Base class for all job board scrapers"""

	def __init__(
		self,
		rate_limiter: Optional[RateLimiter] = None,
		request_override: Optional[Callable[[str, Dict[str, Any]], Awaitable[Optional[httpx.Response]]]] = None,
	):
		self.rate_limiter = rate_limiter or RateLimiter()
		self.user_agent = UserAgent()
		self.session = None
		self.base_url = ""
		self.name = self.__class__.__name__
		self._request_override = request_override

	def set_request_override(self, override: Optional[Callable[[str, Dict[str, Any]], Awaitable[Optional[httpx.Response]]]]) -> None:
		"""Override HTTP requests (used by testing harness)."""
		self._request_override = override

	async def __aenter__(self):
		"""Async context manager entry"""
		self.session = httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=self._get_headers())
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Async context manager exit"""
		if self.session:
			await self.session.aclose()

	def _get_headers(self) -> Dict[str, str]:
		"""Get randomized headers for requests"""
		return {
			"User-Agent": self.user_agent.random,
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			"Accept-Language": "en-US,en;q=0.5",
			"Accept-Encoding": "gzip, deflate",
			"Connection": "keep-alive",
			"Upgrade-Insecure-Requests": "1",
		}

	async def _make_request(self, url: str, **kwargs) -> Optional[httpx.Response]:
		"""Make a rate-limited HTTP request"""
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		await self.rate_limiter.wait()

		try:
			# Rotate user agent for each request
			headers = self._get_headers()
			if "headers" in kwargs:
				headers.update(kwargs["headers"])
			kwargs["headers"] = headers

			if self._request_override:
				return await self._request_override(url, kwargs)

			logger.debug(f"Making request to: {url}")
			response = await self.session.get(url, **kwargs)
			response.raise_for_status()
			return response

		except httpx.HTTPStatusError as e:
			logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
			return None
		except httpx.RequestError as e:
			logger.error(f"Request error for {url}: {e}")
			return None
		except Exception as e:
			logger.error(f"Unexpected error for {url}: {e}")
			return None

	def _parse_html(self, html_content: str) -> BeautifulSoup:
		"""Parse HTML content with BeautifulSoup"""
		return BeautifulSoup(html_content, "lxml")

	def _clean_text(self, text: str) -> str:
		"""Clean and normalize text content"""
		if not text:
			return ""

		# Remove extra whitespace and normalize
		cleaned = " ".join(text.strip().split())
		return cleaned

	def _extract_salary(self, salary_text: str) -> Dict[str, Optional[int]]:
		"""Extract salary information from text"""
		import re

		if not salary_text:
			return {"min": None, "max": None, "currency": "USD"}

		# Common salary patterns
		patterns = [
			r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",  # $50,000 - $70,000
			r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",  # $50,000
			r"(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)",  # 50,000 - 70,000
		]

		for pattern in patterns:
			match = re.search(pattern, salary_text)
			if match:
				if len(match.groups()) == 2:
					return {"min": int(match.group(1).replace(",", "")), "max": int(match.group(2).replace(",", "")), "currency": "USD"}
				else:
					return {"min": int(match.group(1).replace(",", "")), "max": None, "currency": "USD"}

		return {"min": None, "max": None, "currency": "USD"}

	def _validate_job_data(self, job_data: Dict[str, Any]) -> bool:
		"""Validate that job data meets minimum requirements"""
		required_fields = ["title", "company"]

		for field in required_fields:
			if not job_data.get(field) or not job_data[field].strip():
				logger.warning(f"Job missing required field: {field}")
				return False

		# Additional validation
		if len(job_data.get("title", "")) < 3:
			logger.warning("Job title too short")
			return False

		if len(job_data.get("company", "")) < 2:
			logger.warning("Company name too short")
			return False

		return True

	def _create_job_object(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
		"""Create a JobCreate object from scraped data"""
		if not self._validate_job_data(job_data):
			return None

		try:
			# Extract salary information
			salary_info = self._extract_salary(job_data.get("salary", ""))

			return JobCreate(
				title=self._clean_text(job_data["title"]),
				company=self._clean_text(job_data["company"]),
				location=self._clean_text(job_data.get("location", "")),
				description=self._clean_text(job_data.get("description", "")),
				salary_min=salary_info["min"],
				salary_max=salary_info["max"],
				currency=salary_info["currency"],
				application_url=job_data.get("url", ""),
				source=job_data.get("source", "scraped"),
				requirements=self._clean_text(job_data.get("requirements", "")),
				tech_stack=job_data.get("tech_stack", []),
				responsibilities=self._clean_text(job_data.get("responsibilities", "")),
				job_type=job_data.get("job_type") or "",
			)
		except Exception as e:
			logger.error(f"Error creating job object: {e}")
			return None

	@abstractmethod
	async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
		"""Search for jobs on the job board"""
		pass

	@abstractmethod
	def _parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
		"""Parse a single job listing element"""
		pass

	@abstractmethod
	def _build_search_url(self, keywords: str, location: str, page: int = 0) -> str:
		"""Build search URL for the job board"""
		pass
