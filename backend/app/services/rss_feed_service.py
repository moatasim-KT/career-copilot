"""
RSS feed service for monitoring company career pages and job feeds
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import httpx
import feedparser

from app.schemas.job import JobCreate
from app.core.config import get_settings

settings = get_settings()


logger = logging.getLogger(__name__)


class RSSFeedService:
	"""Service for monitoring RSS feeds from company career pages"""

	def __init__(self):
		self.session = None
		self.feed_cache = {}
		self.last_check_times = {}

	async def __aenter__(self):
		"""Async context manager entry"""
		self.session = httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=self._get_headers())
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Async context manager exit"""
		if self.session:
			await self.session.aclose()

	def _get_headers(self) -> Dict[str, str]:
		"""Get headers for RSS requests"""
		return {
			"User-Agent": "Career-Copilot RSS Reader 1.0",
			"Accept": "application/rss+xml, application/xml, text/xml, */*",
			"Accept-Language": "en-US,en;q=0.9",
			"Connection": "keep-alive",
		}

	async def fetch_feed(self, feed_url: str) -> Optional[Dict[str, Any]]:
		"""Fetch and parse an RSS feed"""
		try:
			logger.info(f"Fetching RSS feed: {feed_url}")

			if not self.session:
				raise RuntimeError("RSS service must be used as async context manager")

			response = await self.session.get(feed_url)
			response.raise_for_status()

			# Parse the RSS feed
			feed_data = feedparser.parse(response.text)

			if feed_data.bozo:
				logger.warning(f"RSS feed has parsing issues: {feed_url}")

			return {
				"url": feed_url,
				"title": feed_data.feed.get("title", ""),
				"description": feed_data.feed.get("description", ""),
				"last_updated": feed_data.feed.get("updated", ""),
				"entries": feed_data.entries,
				"fetched_at": datetime.now(timezone.utc),
			}

		except httpx.HTTPStatusError as e:
			logger.error(f"HTTP error fetching RSS feed {feed_url}: {e}")
			return None
		except Exception as e:
			logger.error(f"Error fetching RSS feed {feed_url}: {e}")
			return None

	async def parse_job_entries(self, feed_data: Dict[str, Any], keywords: List[str] | None = None, max_age_days: int = 30) -> List[JobCreate]:
		"""Parse RSS entries and extract job information"""
		jobs = []

		if not feed_data or "entries" not in feed_data:
			return jobs

		# Calculate cutoff date for filtering old entries
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

		for entry in feed_data["entries"]:
			try:
				job = await self._parse_rss_entry(entry, feed_data["url"])

				if not job:
					continue

				# Filter by keywords if provided
				if keywords and not self._matches_keywords(job, keywords):
					continue

				# Filter by age
				if hasattr(entry, "published_parsed") and entry.published_parsed:
					entry_date = datetime(*entry.published_parsed[:6])
					if entry_date < cutoff_date:
						continue

				jobs.append(job)

			except Exception as e:
				logger.error(f"Error parsing RSS entry: {e}")
				continue

		logger.info(f"Parsed {len(jobs)} jobs from RSS feed")
		return jobs

	async def _parse_rss_entry(self, entry: Any, feed_url: str) -> Optional[JobCreate]:
		"""Parse a single RSS entry into a job"""
		try:
			# Extract basic information
			title = entry.get("title", "").strip()
			description = entry.get("description", "") or entry.get("summary", "")
			link = entry.get("link", "")

			if not title:
				return None

			# Try to extract company name from feed or entry
			company = self._extract_company_name(entry, feed_url)

			# Extract location from title or description
			location = self._extract_location(title, description)

			# Clean up description
			description = self._clean_html_description(description)

			# Extract requirements and tags
			requirements = self._extract_requirements(description)
			tags = self._extract_tags(title, description)

			return JobCreate(
				title=title,
				company=company,
				location=location,
				description=description,
				application_url=link,
				source="rss",
				requirements=requirements,
				tags=tags,
				date_posted=self._parse_entry_date(entry),
			)

		except Exception as e:
			logger.error(f"Error parsing RSS entry: {e}")
			return None

	def _extract_company_name(self, entry: Any, feed_url: str) -> str:
		"""Extract company name from RSS entry or feed URL"""
		# Try to get from entry author
		if hasattr(entry, "author") and entry.author:
			return entry.author.strip()

		# Try to extract from feed URL domain
		try:
			domain = urlparse(feed_url).netloc
			# Remove common prefixes and suffixes
			domain = domain.replace("www.", "").replace("careers.", "").replace("jobs.", "")
			# Take the main domain name
			company = domain.split(".")[0]
			return company.title()
		except:
			return "Unknown Company"

	def _extract_location(self, title: str, description: str) -> str:
		"""Extract location information from title or description"""
		import re

		text = f"{title} {description}".lower()

		# Common location patterns
		location_patterns = [
			r"\b(remote|work from home|wfh)\b",
			r"\b([a-z\s]+),\s*([a-z]{2})\b",  # City, State
			r"\b([a-z\s]+),\s*([a-z\s]+)\b",  # City, Country
			r"\bin\s+([a-z\s,]+)\b",
		]

		for pattern in location_patterns:
			match = re.search(pattern, text)
			if match:
				location = match.group(1) if len(match.groups()) == 1 else match.group(0)
				return location.strip().title()

		return ""

	def _clean_html_description(self, description: str) -> str:
		"""Clean HTML tags from description"""
		import re
		from html import unescape

		if not description:
			return ""

		# Remove HTML tags
		clean_desc = re.sub(r"<[^>]+>", "", description)

		# Unescape HTML entities
		clean_desc = unescape(clean_desc)

		# Clean up whitespace
		clean_desc = " ".join(clean_desc.split())

		return clean_desc

	def _extract_requirements(self, description: str) -> Dict[str, Any]:
		"""Extract requirements from job description"""
		import re

		requirements = {"skills": [], "experience": "", "education": ""}

		if not description:
			return requirements

		# Common skill patterns
		skill_patterns = [
			r"\b(python|java|javascript|react|node\.?js|sql|aws|docker|kubernetes)\b",
			r"\b(\d+\+?\s*years?\s*(?:of\s*)?experience)\b",
			r"\b(bachelor\'?s?|master\'?s?|phd|degree)\b",
		]

		text = description.lower()

		# Extract skills
		skills = re.findall(skill_patterns[0], text, re.IGNORECASE)
		requirements["skills"] = list(set(skills))

		# Extract experience
		exp_matches = re.findall(skill_patterns[1], text, re.IGNORECASE)
		if exp_matches:
			requirements["experience"] = exp_matches[0]

		# Extract education
		edu_matches = re.findall(skill_patterns[2], text, re.IGNORECASE)
		if edu_matches:
			requirements["education"] = edu_matches[0]

		return requirements

	def _extract_tags(self, title: str, description: str) -> List[str]:
		"""Extract relevant tags from title and description"""
		import re

		tags = []
		text = f"{title} {description}".lower()

		# Common job type tags
		tag_patterns = {
			"remote": r"\b(remote|work from home|wfh)\b",
			"full-time": r"\b(full.?time|permanent)\b",
			"part-time": r"\b(part.?time|contract)\b",
			"senior": r"\b(senior|lead|principal)\b",
			"junior": r"\b(junior|entry.?level|graduate)\b",
			"startup": r"\b(startup|early.?stage)\b",
			"enterprise": r"\b(enterprise|fortune\s*\d+)\b",
		}

		for tag, pattern in tag_patterns.items():
			if re.search(pattern, text):
				tags.append(tag)

		return tags

	def _parse_entry_date(self, entry: Any) -> Optional[datetime]:
		"""Parse entry publication date"""
		try:
			if hasattr(entry, "published_parsed") and entry.published_parsed:
				return datetime(*entry.published_parsed[:6])
			elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
				return datetime(*entry.updated_parsed[:6])
		except:
			pass

		return None

	def _matches_keywords(self, job: JobCreate, keywords: List[str]) -> bool:
		"""Check if job matches any of the provided keywords"""
		if not keywords:
			return True

		text = f"{job.title} {job.description} {job.company}".lower()

		for keyword in keywords:
			if keyword.lower() in text:
				return True

		return False

	async def monitor_feeds(self, feed_urls: List[str], keywords: List[str] | None = None, max_concurrent: int = 5) -> List[JobCreate]:
		"""Monitor multiple RSS feeds concurrently"""
		if not feed_urls:
			return []

		logger.info(f"Monitoring {len(feed_urls)} RSS feeds")

		# Create semaphore for concurrency control
		semaphore = asyncio.Semaphore(max_concurrent)

		async def fetch_and_parse(feed_url: str) -> List[JobCreate]:
			async with semaphore:
				feed_data = await self.fetch_feed(feed_url)
				if feed_data:
					return await self.parse_job_entries(feed_data, keywords)
				return []

		# Fetch all feeds concurrently
		tasks = [fetch_and_parse(url) for url in feed_urls]
		results = await asyncio.gather(*tasks, return_exceptions=True)

		# Collect all jobs
		all_jobs = []
		for i, result in enumerate(results):
			if isinstance(result, Exception):
				logger.error(f"Error processing feed {feed_urls[i]}: {result}")
				continue

			if isinstance(result, list):
				all_jobs.extend(result)

		logger.info(f"Collected {len(all_jobs)} jobs from RSS feeds")
		return all_jobs

	def get_default_feed_urls(self) -> List[str]:
		"""Get a list of default RSS feed URLs for popular companies"""
		return [
			# Tech companies with RSS feeds
			"https://jobs.github.com/positions.atom",
			"https://stackoverflow.com/jobs/feed",
			"https://careers.google.com/api/v3/search/?format=rss",
			"https://www.apple.com/careers/us/rss-feed.xml",
			"https://careers.microsoft.com/us/en/search-results?rt=professional&format=rss",
			# Job boards with RSS
			"https://remoteok.io/remote-jobs.rss",
			"https://weworkremotely.com/remote-jobs.rss",
			"https://angel.co/jobs.rss",
			# Industry-specific feeds
			"https://jobs.techcrunch.com/jobs.rss",
			"https://news.ycombinator.com/jobs.rss",
		]

	async def discover_company_feeds(self, company_domains: List[str]) -> List[str]:
		"""Discover RSS feeds for company career pages"""
		discovered_feeds = []

		for domain in company_domains:
			try:
				# Common RSS feed paths
				potential_paths = ["/careers/rss", "/careers/feed", "/jobs/rss", "/jobs/feed", "/careers.rss", "/jobs.rss", "/feed", "/rss"]

				for path in potential_paths:
					feed_url = f"https://{domain}{path}"

					# Test if feed exists
					try:
						response = await self.session.head(feed_url)
						if response.status_code == 200:
							content_type = response.headers.get("content-type", "").lower()
							if any(ct in content_type for ct in ["xml", "rss", "atom"]):
								discovered_feeds.append(feed_url)
								logger.info(f"Discovered RSS feed: {feed_url}")
								break
					except:
						continue

			except Exception as e:
				logger.error(f"Error discovering feeds for {domain}: {e}")
				continue

		return discovered_feeds
