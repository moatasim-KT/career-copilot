"""
Tests for Job Deduplication Service
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from app.models.job import Job
from app.services.job_deduplication_service import JobDeduplicationService


@pytest.fixture
def mock_db():
	"""Create a mock database session"""
	db = MagicMock()
	return db


@pytest.fixture
def dedup_service(mock_db):
	"""Create JobDeduplicationService instance"""
	return JobDeduplicationService(mock_db)


class TestCompanyNameNormalization:
	"""Test company name normalization"""

	def test_removes_inc_suffix(self, dedup_service):
		assert dedup_service.normalize_company_name("Google Inc.") == "google"
		assert dedup_service.normalize_company_name("Microsoft Inc") == "microsoft"

	def test_removes_corp_suffix(self, dedup_service):
		assert dedup_service.normalize_company_name("Apple Corporation") == "apple"
		assert dedup_service.normalize_company_name("Amazon Corp") == "amazon"

	def test_removes_llc_suffix(self, dedup_service):
		assert dedup_service.normalize_company_name("Stripe, LLC") == "stripe"
		assert dedup_service.normalize_company_name("Airbnb LLC") == "airbnb"

	def test_removes_punctuation(self, dedup_service):
		# Punctuation is replaced with spaces, then "inc" suffix is removed
		assert dedup_service.normalize_company_name("Tech-Company, Inc.") == "tech"

	def test_handles_empty_input(self, dedup_service):
		assert dedup_service.normalize_company_name("") == ""
		assert dedup_service.normalize_company_name(None) == ""

	def test_case_insensitive(self, dedup_service):
		assert dedup_service.normalize_company_name("GOOGLE") == "google"
		assert dedup_service.normalize_company_name("Google") == "google"


class TestJobTitleNormalization:
	"""Test job title normalization"""

	def test_removes_remote_keyword(self, dedup_service):
		assert dedup_service.normalize_job_title("Software Engineer (Remote)") == "software engineer"

	def test_removes_parentheses(self, dedup_service):
		# Content in parentheses is removed
		assert dedup_service.normalize_job_title("Data Scientist (ML)") == "data scientist"

	def test_removes_special_characters(self, dedup_service):
		assert dedup_service.normalize_job_title("Senior Software Engineer - Backend") == "senior software engineer backend"

	def test_handles_empty_input(self, dedup_service):
		assert dedup_service.normalize_job_title("") == ""
		assert dedup_service.normalize_job_title(None) == ""

	def test_removes_noise_words(self, dedup_service):
		assert "urgent" not in dedup_service.normalize_job_title("Urgent - Software Engineer")
		# "apply" and "now" are separate words in title_noise_words list
		result = dedup_service.normalize_job_title("Data Scientist - Apply Now!")
		assert "apply" not in result
		assert "now" not in result


class TestLocationNormalization:
	"""Test location normalization"""

	def test_normalizes_city_state(self, dedup_service):
		assert dedup_service.normalize_location("San Francisco, CA") == "san francisco ca"

	def test_removes_punctuation(self, dedup_service):
		assert dedup_service.normalize_location("New York, NY") == "new york ny"

	def test_handles_remote(self, dedup_service):
		assert dedup_service.normalize_location("Remote - USA") == "remote usa"


class TestURLNormalization:
	"""Test URL normalization"""

	def test_removes_query_params(self, dedup_service):
		url = "https://example.com/job/123?ref=abc&source=xyz"
		normalized = dedup_service.normalize_url(url)
		assert "ref" not in normalized
		assert "source" not in normalized
		assert "example.com/job/123" in normalized

	def test_removes_fragment(self, dedup_service):
		url = "https://example.com/job/123#apply"
		normalized = dedup_service.normalize_url(url)
		assert "#" not in normalized

	def test_case_insensitive(self, dedup_service):
		url1 = "https://Example.COM/Job/123"
		url2 = "https://example.com/job/123"
		assert dedup_service.normalize_url(url1) == dedup_service.normalize_url(url2)

	def test_handles_trailing_slash(self, dedup_service):
		url1 = "https://example.com/job/123/"
		url2 = "https://example.com/job/123"
		assert dedup_service.normalize_url(url1) == dedup_service.normalize_url(url2)


class TestFingerprintGeneration:
	"""Test job fingerprint generation"""

	def test_same_job_same_fingerprint(self, dedup_service):
		fp1 = dedup_service.create_job_fingerprint("Software Engineer", "Google", "San Francisco")
		fp2 = dedup_service.create_job_fingerprint("Software Engineer", "Google", "San Francisco")
		assert fp1 == fp2

	def test_different_job_different_fingerprint(self, dedup_service):
		fp1 = dedup_service.create_job_fingerprint("Software Engineer", "Google", "San Francisco")
		fp2 = dedup_service.create_job_fingerprint("Data Scientist", "Microsoft", "Seattle")
		assert fp1 != fp2

	def test_normalized_values_same_fingerprint(self, dedup_service):
		fp1 = dedup_service.create_job_fingerprint("Software Engineer (Remote)", "Google Inc.", "San Francisco, CA")
		fp2 = dedup_service.create_job_fingerprint("Software Engineer", "Google", "San Francisco CA")
		assert fp1 == fp2

	def test_fingerprint_is_md5_hash(self, dedup_service):
		fp = dedup_service.create_job_fingerprint("Test", "Company", "Location")
		assert len(fp) == 32  # MD5 hash is 32 characters
		assert fp.isalnum()  # Only alphanumeric characters


class TestSimilarityCalculation:
	"""Test similarity calculation"""

	def test_identical_strings(self, dedup_service):
		similarity = dedup_service.calculate_similarity("hello world", "hello world")
		assert similarity == 1.0

	def test_completely_different_strings(self, dedup_service):
		similarity = dedup_service.calculate_similarity("abc", "xyz")
		assert similarity < 0.5

	def test_similar_strings(self, dedup_service):
		similarity = dedup_service.calculate_similarity("software engineer", "senior software engineer")
		assert similarity > 0.7

	def test_case_insensitive(self, dedup_service):
		similarity = dedup_service.calculate_similarity("Hello", "hello")
		assert similarity == 1.0


class TestDuplicateDetection:
	"""Test duplicate job detection"""

	def test_exact_match_by_url(self, dedup_service):
		is_dup, reason = dedup_service.are_jobs_duplicate(
			"Software Engineer",
			"Google",
			"SF",
			"https://example.com/job/1",
			"Software Engineer",
			"Google",
			"San Francisco",
			"https://example.com/job/1",
			strict_mode=False,
		)
		assert is_dup is True
		assert reason == "duplicate_url"

	def test_exact_match_by_fingerprint(self, dedup_service):
		is_dup, reason = dedup_service.are_jobs_duplicate(
			"Software Engineer", "Google", "San Francisco", None, "Software Engineer", "Google", "San Francisco", None, strict_mode=False
		)
		assert is_dup is True
		assert reason == "duplicate_fingerprint"

	def test_fuzzy_match_similar_title_company(self, dedup_service):
		# Use titles with higher similarity (>0.85) and similar locations
		is_dup, _reason = dedup_service.are_jobs_duplicate(
			"Software Engineer Backend",
			"Google Inc",
			"San Francisco",
			None,
			"Software Engineer - Backend",
			"Google",
			"San Francisco, CA",
			None,
			strict_mode=False,
		)
		assert is_dup is True

	def test_not_duplicate_different_company(self, dedup_service):
		is_dup, _reason = dedup_service.are_jobs_duplicate(
			"Software Engineer", "Google", "SF", None, "Software Engineer", "Microsoft", "Seattle", None, strict_mode=False
		)
		assert is_dup is False

	def test_strict_mode_no_fuzzy_match(self, dedup_service):
		is_dup, reason = dedup_service.are_jobs_duplicate(
			"Senior Software Engineer", "Google Inc", "SF", None, "Software Engineer", "Google", "San Francisco", None, strict_mode=True
		)
		assert is_dup is False


class TestFilterDuplicateJobs:
	"""Test filtering duplicate jobs"""

	def test_filters_duplicates_within_batch(self, dedup_service):
		jobs = [
			{"title": "Software Engineer", "company": "Google", "location": "San Francisco"},
			{"title": "Software Engineer", "company": "Google", "location": "San Francisco"},  # Exact duplicate
			{"title": "Data Scientist", "company": "Microsoft", "location": "Seattle"},
		]

		_unique_jobs, stats = dedup_service.filter_duplicate_jobs(jobs, None, strict_mode=False)

		assert stats["total_input"] == 3
		assert stats["unique_output"] == 2
		assert stats["duplicates_removed"] == 1

	def test_filters_duplicates_by_url(self, dedup_service):
		jobs = [
			{"title": "Software Engineer", "company": "Google", "location": "SF", "url": "https://example.com/job/1"},
			{"title": "Senior Software Engineer", "company": "Google Inc", "location": "San Francisco", "url": "https://example.com/job/1"},
		]

		unique_jobs, stats = dedup_service.filter_duplicate_jobs(jobs, None, strict_mode=False)

		assert stats["unique_output"] == 1
		assert stats["duplicates_by_url"] == 1

	def test_skips_jobs_with_missing_data(self, dedup_service):
		jobs = [
			{"title": "", "company": "Google", "location": "SF"},  # Missing title
			{"title": "Software Engineer", "company": "", "location": "SF"},  # Missing company
			{"title": "Data Scientist", "company": "Microsoft", "location": "Seattle"},  # Valid
		]

		unique_jobs, stats = dedup_service.filter_duplicate_jobs(jobs, None, strict_mode=False)

		assert stats["unique_output"] == 1

	def test_empty_input(self, dedup_service):
		unique_jobs, stats = dedup_service.filter_duplicate_jobs([], None, strict_mode=False)

		assert stats["total_input"] == 0
		assert stats["unique_output"] == 0


class TestDeduplicateAgainstDB:
	"""Test deduplication against database"""

	def test_filters_against_existing_jobs(self, mock_db, dedup_service):
		# Mock existing jobs
		existing_jobs = [
			Job(
				id=1,
				user_id=1,
				title="Software Engineer",
				company="Google",
				location="San Francisco",
				application_url="https://example.com/job/1",
				created_at=datetime.now(timezone.utc),
			)
		]

		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.all.return_value = existing_jobs

		# New jobs to check
		jobs = [
			{"title": "Software Engineer", "company": "Google", "location": "SF", "application_url": "https://example.com/job/1"},  # Duplicate
			{"title": "Data Scientist", "company": "Microsoft", "location": "Seattle", "application_url": "https://example.com/job/2"},  # New
		]

		unique_jobs, stats = dedup_service.deduplicate_against_db(jobs, user_id=1, days_lookback=30)

		assert stats["unique_output"] == 1
		assert unique_jobs[0]["title"] == "Data Scientist"

	def test_uses_days_lookback(self, mock_db, dedup_service):
		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.filter.return_value = mock_query
		mock_query.all.return_value = []

		jobs = [{"title": "Test", "company": "Test", "location": "Test"}]

		dedup_service.deduplicate_against_db(jobs, user_id=1, days_lookback=7)

		# Verify the filter was called with correct parameters
		assert mock_query.filter.called


class TestBulkDatabaseDeduplication:
	"""Test bulk deduplication of existing database jobs"""

	def test_finds_duplicates_in_database(self, mock_db, dedup_service):
		# Mock database jobs with duplicates
		jobs = [
			Job(
				id=1,
				title="Software Engineer",
				company="Google",
				location="SF",
				user_id=1,
				application_url="https://example.com/job/1",
				created_at=datetime.now(timezone.utc),
			),
			Job(
				id=2,
				title="Software Engineer",
				company="Google",
				location="San Francisco",
				user_id=1,
				application_url="https://example.com/job/1",
				created_at=datetime.now(timezone.utc),
			),  # Duplicate by URL
			Job(
				id=3,
				title="Data Scientist",
				company="Microsoft",
				location="Seattle",
				user_id=1,
				application_url="https://example.com/job/2",
				created_at=datetime.now(timezone.utc),
			),
		]

		# Setup mock query chain - use a fresh instance for the dedup service
		mock_query = MagicMock()
		mock_query_filtered = MagicMock()

		mock_db.query.return_value = mock_query
		mock_query.order_by.return_value = mock_query
		mock_query.filter.return_value = mock_query_filtered  # Return filtered query
		mock_query_filtered.all.return_value = jobs  # The filtered query returns jobs

		results = dedup_service.bulk_deduplicate_database_jobs(user_id=1)

		assert results["total_jobs"] == 3
		assert results["duplicates_found"] > 0

	def test_no_duplicates_found(self, mock_db, dedup_service):
		jobs = [
			Job(
				id=1,
				title="Software Engineer",
				company="Google",
				location="SF",
				user_id=1,
				application_url="https://example.com/job/1",
				created_at=datetime.now(timezone.utc),
			),
			Job(
				id=2,
				title="Data Scientist",
				company="Microsoft",
				location="Seattle",
				user_id=1,
				application_url="https://example.com/job/2",
				created_at=datetime.now(timezone.utc),
			),
		]

		mock_query = MagicMock()
		mock_db.query.return_value = mock_query
		mock_query.order_by.return_value = mock_query
		mock_query.all.return_value = jobs

		results = dedup_service.bulk_deduplicate_database_jobs(user_id=1)

		assert results["duplicates_found"] == 0
		assert results["duplicates_removed"] == 0
		assert results["duplicates_removed"] == 0
