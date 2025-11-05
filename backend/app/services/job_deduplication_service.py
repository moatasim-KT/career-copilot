"""
Advanced Job Deduplication Service

Provides sophisticated duplicate detection and job uniqueness checking:
- Fuzzy matching for company names and job titles
- Normalizes text for better comparison
- URL-based deduplication
- Multiple deduplication strategies
- Hash-based fingerprinting
"""

import hashlib
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from app.core.logging import get_logger
from app.models.job import Job
from app.schemas.job import JobCreate
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class JobDeduplicationService:
	"""Advanced deduplication service for job postings"""

	def __init__(self, db: Session):
		self.db = db

		# Common company name variations for normalization
		self.company_suffixes = [
			"inc",
			"incorporated",
			"corp",
			"corporation",
			"llc",
			"ltd",
			"limited",
			"co",
			"company",
			"gmbh",
			"ag",
			"sa",
			"nv",
			"bv",
			"plc",
			"llp",
		]

		# Words to remove from job titles for better matching
		self.title_noise_words = [
			"remote",
			"hybrid",
			"onsite",
			"full-time",
			"part-time",
			"contract",
			"permanent",
			"temporary",
			"urgent",
			"immediate",
			"apply",
			"now",
		]

	def normalize_company_name(self, company: str) -> str:
		"""
		Normalize company name for comparison

		Examples:
		- "Google Inc." -> "google"
		- "Microsoft Corporation" -> "microsoft"
		- "Amazon, Inc" -> "amazon"
		"""
		if not company:
			return ""

		# Convert to lowercase and remove extra whitespace
		normalized = " ".join(company.lower().strip().split())

		# Remove common punctuation
		normalized = re.sub(r"[,\.;:\-_]", " ", normalized)

		# Remove common suffixes
		for suffix in self.company_suffixes:
			# Match suffix as whole word at the end
			pattern = rf"\b{re.escape(suffix)}\b\s*$"
			normalized = re.sub(pattern, "", normalized)

		# Remove extra spaces again
		normalized = " ".join(normalized.split())

		return normalized.strip()

	def normalize_job_title(self, title: str) -> str:
		"""
		Normalize job title for comparison

		Examples:
		- "Senior Software Engineer (Remote)" -> "senior software engineer"
		- "Data Scientist - ML" -> "data scientist ml"
		"""
		if not title:
			return ""

		# Convert to lowercase
		normalized = title.lower().strip()

		# Remove content in parentheses and brackets
		normalized = re.sub(r"\([^)]*\)", "", normalized)
		normalized = re.sub(r"\[[^\]]*\]", "", normalized)

		# Remove special characters but keep spaces and alphanumeric
		normalized = re.sub(r"[^\w\s]", " ", normalized)

		# Remove noise words
		words = normalized.split()
		filtered_words = [w for w in words if w not in self.title_noise_words]
		normalized = " ".join(filtered_words)

		# Remove extra whitespace
		normalized = " ".join(normalized.split())

		return normalized.strip()

	def normalize_location(self, location: str) -> str:
		"""
		Normalize location for comparison

		Examples:
		- "San Francisco, CA" -> "san francisco ca"
		- "Remote - USA" -> "remote usa"
		"""
		if not location:
			return ""

		normalized = location.lower().strip()

		# Remove common punctuation
		normalized = re.sub(r"[,\-]", " ", normalized)

		# Remove extra whitespace
		normalized = " ".join(normalized.split())

		return normalized.strip()

	def normalize_url(self, url: str) -> str:
		"""
		Normalize URL for comparison (removes query params and fragments)

		Examples:
		- "https://example.com/job/123?ref=abc" -> "example.com/job/123"
		"""
		if not url:
			return ""

		try:
			parsed = urlparse(url.lower().strip())
			# Use domain + path, ignore query params and fragments
			normalized = f"{parsed.netloc}{parsed.path}".rstrip("/")
			return normalized
		except Exception:
			return url.lower().strip()

	def create_job_fingerprint(self, title: str, company: str, location: Optional[str] = None) -> str:
		"""
		Create a unique fingerprint for a job posting

		Uses normalized values to create a consistent hash
		"""
		norm_title = self.normalize_job_title(title)
		norm_company = self.normalize_company_name(company)
		norm_location = self.normalize_location(location or "")

		# Create composite key
		composite = f"{norm_company}|{norm_title}|{norm_location}"

		# Generate hash
		return hashlib.md5(composite.encode()).hexdigest()

	def calculate_similarity(self, str1: str, str2: str) -> float:
		"""
		Calculate similarity ratio between two strings (0.0 to 1.0)

		Uses SequenceMatcher for fuzzy matching
		"""
		if not str1 or not str2:
			return 0.0

		return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

	def are_jobs_duplicate(
		self,
		job1_title: str,
		job1_company: str,
		job1_location: Optional[str],
		job1_url: Optional[str],
		job2_title: str,
		job2_company: str,
		job2_location: Optional[str],
		job2_url: Optional[str],
		strict_mode: bool = False,
	) -> Tuple[bool, str]:
		"""
		Determine if two jobs are duplicates

		Returns:
			Tuple of (is_duplicate: bool, reason: str)

		Strategies:
		1. Exact URL match (if URLs provided)
		2. Exact fingerprint match
		3. Fuzzy matching (if not strict_mode)
		"""

		# Strategy 1: URL-based deduplication (most reliable)
		if job1_url and job2_url:
			norm_url1 = self.normalize_url(job1_url)
			norm_url2 = self.normalize_url(job2_url)

			if norm_url1 and norm_url2 and norm_url1 == norm_url2:
				return True, "duplicate_url"

		# Strategy 2: Fingerprint-based (exact match after normalization)
		fp1 = self.create_job_fingerprint(job1_title, job1_company, job1_location)
		fp2 = self.create_job_fingerprint(job2_title, job2_company, job2_location)

		if fp1 == fp2:
			return True, "duplicate_fingerprint"

		# Strategy 3: Fuzzy matching (unless strict mode)
		if not strict_mode:
			# Normalize values
			norm_title1 = self.normalize_job_title(job1_title)
			norm_title2 = self.normalize_job_title(job2_title)
			norm_company1 = self.normalize_company_name(job1_company)
			norm_company2 = self.normalize_company_name(job2_company)
			norm_location1 = self.normalize_location(job1_location or "")
			norm_location2 = self.normalize_location(job2_location or "")

			# Calculate similarities
			company_sim = self.calculate_similarity(norm_company1, norm_company2)
			title_sim = self.calculate_similarity(norm_title1, norm_title2)
			location_sim = self.calculate_similarity(norm_location1, norm_location2)

			# Thresholds for fuzzy matching
			# High similarity in company (0.8+) and title (0.85+) = duplicate
			if company_sim >= 0.8 and title_sim >= 0.85:
				# If locations are very different, might not be duplicate
				if norm_location1 and norm_location2 and location_sim < 0.5:
					return False, "different_location"

				return True, f"fuzzy_match (company: {company_sim:.2f}, title: {title_sim:.2f})"

		return False, "not_duplicate"

	def filter_duplicate_jobs(
		self, jobs: List[Dict[str, Any]], existing_jobs: Optional[List[Job]] = None, strict_mode: bool = False
	) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
		"""
		Filter out duplicate jobs from a list

		Args:
			jobs: List of scraped job dictionaries
			existing_jobs: Optional list of existing Job models from database
			strict_mode: If True, only uses exact matching (no fuzzy)

		Returns:
			Tuple of (unique_jobs, deduplication_stats)
		"""

		if not jobs:
			return [], {"total_input": 0, "duplicates_removed": 0, "unique_output": 0}

		logger.info(f"Starting deduplication of {len(jobs)} jobs (strict_mode={strict_mode})")

		unique_jobs: List[Dict[str, Any]] = []
		seen_fingerprints: Set[str] = set()
		seen_urls: Set[str] = set()

		# Stats tracking
		stats = {
			"total_input": len(jobs),
			"duplicates_within_batch": 0,
			"duplicates_against_db": 0,
			"duplicates_by_url": 0,
			"duplicates_by_fingerprint": 0,
			"duplicates_by_fuzzy": 0,
			"unique_output": 0,
		}

		# Build existing jobs lookup
		existing_fingerprints: Set[str] = set()
		existing_urls: Set[str] = set()
		existing_jobs_data: List[Tuple[str, str, str, str]] = []

		if existing_jobs:
			for job in existing_jobs:
				# Add fingerprint
				fp = self.create_job_fingerprint(job.title, job.company, job.location)
				existing_fingerprints.add(fp)

				# Add URL if available
				if job.application_url:
					norm_url = self.normalize_url(job.application_url)
					if norm_url:
						existing_urls.add(norm_url)

				# Store for fuzzy matching
				existing_jobs_data.append((job.title, job.company, job.location or "", job.application_url or ""))

		# Process each job
		for job_data in jobs:
			# Handle both dict and Pydantic model
			if hasattr(job_data, "model_dump"):
				# Pydantic v2
				job_dict = job_data.model_dump()
			elif hasattr(job_data, "dict"):
				# Pydantic v1
				job_dict = job_data.dict()
			elif isinstance(job_data, dict):
				job_dict = job_data
			else:
				logger.warning(f"Unexpected job_data type: {type(job_data)}")
				continue

			title = job_dict.get("title", "")
			company = job_dict.get("company", "")
			location = job_dict.get("location", "")
			url = job_dict.get("application_url") or job_dict.get("url", "")

			# Skip jobs with missing critical data
			if not title or not company:
				logger.debug(f"Skipping job with missing data: title='{title}', company='{company}'")
				continue

			is_duplicate = False
			duplicate_reason = ""

			# Check URL first (fastest)
			if url:
				norm_url = self.normalize_url(url)
				if norm_url:
					if norm_url in seen_urls or norm_url in existing_urls:
						is_duplicate = True
						duplicate_reason = "duplicate_url"
						stats["duplicates_by_url"] += 1
					else:
						seen_urls.add(norm_url)

			# Check fingerprint
			if not is_duplicate:
				fp = self.create_job_fingerprint(title, company, location)
				if fp in seen_fingerprints or fp in existing_fingerprints:
					is_duplicate = True
					duplicate_reason = "duplicate_fingerprint"
					stats["duplicates_by_fingerprint"] += 1
				else:
					seen_fingerprints.add(fp)

			# Fuzzy matching against existing jobs (if not strict)
			if not is_duplicate and not strict_mode and existing_jobs_data:
				for ex_title, ex_company, ex_location, ex_url in existing_jobs_data:
					is_dup, reason = self.are_jobs_duplicate(
						title, company, location, url, ex_title, ex_company, ex_location, ex_url, strict_mode=strict_mode
					)
					if is_dup:
						is_duplicate = True
						duplicate_reason = f"existing_db_{reason}"
						stats["duplicates_by_fuzzy"] += 1
						stats["duplicates_against_db"] += 1
						break

			# Fuzzy matching within batch (if not strict)
			if not is_duplicate and not strict_mode and len(unique_jobs) > 0:
				for unique_job in unique_jobs:
					# Handle both dict and Pydantic model for comparison
					if hasattr(unique_job, "model_dump"):
						uj_dict = unique_job.model_dump()
					elif hasattr(unique_job, "dict"):
						uj_dict = unique_job.dict()
					elif isinstance(unique_job, dict):
						uj_dict = unique_job
					else:
						continue

					is_dup, reason = self.are_jobs_duplicate(
						title,
						company,
						location,
						url,
						uj_dict.get("title", ""),
						uj_dict.get("company", ""),
						uj_dict.get("location", ""),
						uj_dict.get("application_url") or uj_dict.get("url", ""),
						strict_mode=strict_mode,
					)
					if is_dup:
						is_duplicate = True
						duplicate_reason = f"batch_{reason}"
						stats["duplicates_by_fuzzy"] += 1
						stats["duplicates_within_batch"] += 1
						break

			# Add to unique jobs if not duplicate
			if not is_duplicate:
				unique_jobs.append(job_data)
			else:
				logger.debug(f"Filtered duplicate job: {title} at {company} (reason: {duplicate_reason})")

		stats["unique_output"] = len(unique_jobs)
		stats["duplicates_removed"] = stats["total_input"] - stats["unique_output"]

		logger.info(
			f"Deduplication complete: {stats['unique_output']}/{stats['total_input']} unique jobs ({stats['duplicates_removed']} duplicates removed)"
		)

		return unique_jobs, stats

	def deduplicate_against_db(
		self, jobs: List[Dict[str, Any]], user_id: int, days_lookback: int = 30, strict_mode: bool = False
	) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
		"""
		Deduplicate jobs against existing database entries for a user

		Args:
			jobs: List of scraped job dictionaries
			user_id: User ID to check against
			days_lookback: How many days back to check (default 30)
			strict_mode: If True, only uses exact matching

		Returns:
			Tuple of (unique_jobs, deduplication_stats)
		"""

		# Get existing jobs from database
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_lookback)

		existing_jobs = self.db.query(Job).filter(Job.user_id == user_id, Job.created_at >= cutoff_date).all()

		logger.info(f"Checking {len(jobs)} jobs against {len(existing_jobs)} existing jobs from last {days_lookback} days for user {user_id}")

		return self.filter_duplicate_jobs(jobs, existing_jobs, strict_mode)

	def bulk_deduplicate_database_jobs(self, user_id: Optional[int] = None, batch_size: int = 100) -> Dict[str, Any]:
		"""
		Find and mark/remove duplicate jobs already in the database

		Useful for cleaning up existing data

		Args:
			user_id: Optional user ID to limit scope
			batch_size: Process jobs in batches

		Returns:
			Dictionary with deduplication results
		"""

		logger.info(f"Starting bulk database deduplication (user_id={user_id})")

		# Query jobs
		query = self.db.query(Job).order_by(Job.created_at.desc())
		if user_id:
			query = query.filter(Job.user_id == user_id)

		all_jobs = query.all()

		if len(all_jobs) < 2:
			logger.info("Less than 2 jobs found, no deduplication needed")
			return {"total_jobs": len(all_jobs), "duplicates_found": 0, "duplicates_removed": 0}

		logger.info(f"Found {len(all_jobs)} jobs to check for duplicates")

		# Track duplicates
		seen_fingerprints: Dict[str, int] = {}  # fingerprint -> job_id (keep the oldest)
		seen_urls: Dict[str, int] = {}  # url -> job_id
		duplicate_job_ids: Set[int] = set()

		results = {"total_jobs": len(all_jobs), "duplicates_found": 0, "duplicates_removed": 0, "duplicates_by_type": {"url": 0, "fingerprint": 0}}

		# First pass: exact matches
		for job in all_jobs:
			# URL-based deduplication
			if job.application_url:
				norm_url = self.normalize_url(job.application_url)
				if norm_url:
					if norm_url in seen_urls:
						# Duplicate found
						duplicate_job_ids.add(job.id)
						results["duplicates_by_type"]["url"] += 1
						logger.debug(f"Duplicate URL found: {job.title} at {job.company} (id={job.id})")
					else:
						seen_urls[norm_url] = job.id

			# Fingerprint-based deduplication
			if job.id not in duplicate_job_ids:  # Only if not already marked as duplicate
				fp = self.create_job_fingerprint(job.title, job.company, job.location)
				if fp in seen_fingerprints:
					# Duplicate found
					duplicate_job_ids.add(job.id)
					results["duplicates_by_type"]["fingerprint"] += 1
					logger.debug(f"Duplicate fingerprint found: {job.title} at {job.company} (id={job.id})")
				else:
					seen_fingerprints[fp] = job.id

		results["duplicates_found"] = len(duplicate_job_ids)

		# Remove duplicates if any found
		if duplicate_job_ids:
			logger.info(f"Removing {len(duplicate_job_ids)} duplicate jobs from database")

			# Delete in batches
			for i in range(0, len(duplicate_job_ids), batch_size):
				batch_ids = list(duplicate_job_ids)[i : i + batch_size]
				self.db.query(Job).filter(Job.id.in_(batch_ids)).delete(synchronize_session=False)

			self.db.commit()
			results["duplicates_removed"] = len(duplicate_job_ids)

			logger.info(f"Successfully removed {results['duplicates_removed']} duplicate jobs")
		else:
			logger.info("No duplicates found in database")

		return results
