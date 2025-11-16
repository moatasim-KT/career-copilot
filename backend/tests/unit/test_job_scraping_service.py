"""
Unit Tests for Job Management System (formerly Job Scraping Service)
Tests the consolidated job scraping service (job scraper + ingestion + API integration)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate
from app.services.job_service import JobManagementSystem


class TestJobManagementSystemInitialization:
	"""Test service initialization"""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session"""
		return MagicMock(spec=Session)

	def test_initialization_with_db(self, mock_db):
		"""Test service initialization with database"""
		# Execute
		service = JobManagementSystem(db=mock_db)

		# Verify
		assert service.db == mock_db
		assert service.settings is not None
		assert service.notification_service is not None
		assert service.skill_matcher is not None
		assert service.quota_manager is not None

	def test_initialization_without_db(self):
		"""Test service initialization without database"""
		# Execute
		service = JobManagementSystem(db=None)

		# Verify
		assert service.db is None
		assert service.settings is not None

	def test_api_configurations(self, mock_db):
		"""Test API configurations are properly set"""
		# Execute
		service = JobManagementSystem(db=mock_db)

		# Verify
		assert "adzuna" in service.apis
		assert "github" in service.apis
		assert "weworkremotely" in service.apis
		assert "stackoverflow" in service.apis
		assert "usajobs" in service.apis
		assert "remoteok" in service.apis

		# Verify structure
		for api_name, api_config in service.apis.items():
			assert "enabled" in api_config
			assert "base_url" in api_config


class TestJobManagementSystemScrapers:
	"""Tests focused on the new ScraperManager-driven architecture."""

	@pytest.fixture
	def mock_db(self):
		return MagicMock(spec=Session)

	@pytest.fixture
	def service(self, mock_db):
		return JobManagementSystem(db=mock_db)

	@pytest.mark.asyncio
	async def test_scrape_adzuna_api_success(self, service):
		"""Ensure the private Adzuna scraper normalizes API payloads via aiohttp."""
		service.apis["adzuna"].update({"enabled": True, "app_id": "id", "app_key": "key"})
		preferences = {"skills": ["python"], "locations": ["Berlin"]}

		mock_resp = MagicMock()
		mock_resp.status = 200
		mock_resp.json = AsyncMock(
			return_value={
				"results": [
					{
						"title": "Python Developer",
						"company": {"display_name": "Tech Corp"},
						"location": {"display_name": "Berlin, Germany"},
						"description": "A great role",
						"redirect_url": "https://example.com/job1",
						"salary_min": 90000,
						"salary_max": 120000,
					}
				]
			}
		)

		with patch("app.services.job_service.aiohttp.ClientSession") as mock_session_class:
			mock_session = MagicMock()
			mock_session_class.return_value.__aenter__.return_value = mock_session
			mock_ctx = MagicMock()
			mock_ctx.__aenter__.return_value = mock_resp
			mock_session.get.return_value = mock_ctx

			result = await service._scrape_adzuna(preferences)

		assert len(result) == 1
		assert result[0]["title"] == "Python Developer"
		assert result[0]["company"] == "Tech Corp"

	@pytest.mark.asyncio
	async def test_scrape_remoteok_api_success(self, service):
		"""RemoteOK scraper should parse JSON payloads via aiohttp."""
		mock_resp = MagicMock()
		mock_resp.status = 200
		mock_resp.json = AsyncMock(
			return_value=[
				{
					"position": "ML Engineer",
					"company": "AI Labs",
					"location": "Remote, EU",
					"description": "Research role",
					"url": "https://example.com/ml",
				}
			]
		)

		with patch("app.services.job_service.aiohttp.ClientSession") as mock_session_class:
			mock_session = MagicMock()
			mock_session_class.return_value.__aenter__.return_value = mock_session
			mock_ctx = MagicMock()
			mock_ctx.__aenter__.return_value = mock_resp
			mock_session.get.return_value = mock_ctx

			result = await service._scrape_remoteok({})

		assert result[0]["title"] == "ML Engineer"
		assert result[0]["source"] == "remoteok"

	@pytest.mark.asyncio
	async def test_scrape_jobs_prefers_scraper_manager_results(self, service, monkeypatch):
		"""scrape_jobs should return ScraperManager output (converted to dicts)."""
		job = JobCreate(company="Data Co", title="Data Scientist", location="Berlin")
		monkeypatch.setattr(service, "_ingest_from_scrapers", AsyncMock(return_value=[job]))
		service.apis["adzuna"]["enabled"] = False
		service.apis["remoteok"]["enabled"] = False

		result = await service.scrape_jobs({"skills": ["data"], "locations": ["Berlin"], "max_jobs": 10})

		assert len(result) == 1
		assert result[0]["title"] == "Data Scientist"

	@pytest.mark.asyncio
	async def test_scrape_jobs_handles_scraper_errors(self, service, monkeypatch):
		"""Errors from ScraperManager should be logged and not crash scraping."""
		monkeypatch.setattr(service, "_ingest_from_scrapers", AsyncMock(side_effect=RuntimeError("boom")))
		service.apis["adzuna"]["enabled"] = False
		service.apis["remoteok"]["enabled"] = False

		result = await service.scrape_jobs({"skills": [], "locations": [], "max_jobs": 10})

		assert result == []


class TestJobManagementSystemDeduplication:
	"""Ensure wrapper methods delegate to JobDeduplicationService."""

	@pytest.fixture
	def mock_db(self):
		return MagicMock(spec=Session)

	@pytest.fixture
	def service(self, mock_db):
		return JobManagementSystem(db=mock_db)

	def test_deduplicate_against_db_delegates(self, service):
		jobs = [{"title": "Engineer", "company": "Tech", "location": "Berlin"}]
		with patch.object(service.deduplication_service, "deduplicate_against_db", return_value=jobs) as mock_dedupe:
			result = service.deduplicate_against_db(jobs, user_id=42)

		mock_dedupe.assert_called_once_with(jobs, 42)
		assert result == jobs

	def test_filter_duplicate_jobs(self, service):
		jobs = [{"title": "Engineer", "company": "Tech"}]
		with patch.object(service.deduplication_service, "filter_duplicate_jobs", return_value=jobs) as mock_filter:
			result = service.filter_duplicate_jobs(jobs)

		mock_filter.assert_called_once()
		assert result == jobs


class TestJobManagementSystemDataNormalization:
	"""Validate helper normalization routines."""

	@pytest.fixture
	def mock_db(self):
		return MagicMock(spec=Session)

	@pytest.fixture
	def service(self, mock_db):
		return JobManagementSystem(db=mock_db)

	def test_normalize_adzuna_job(self, service):
		job = {
			"title": "Engineer",
			"company": {"display_name": "Tech"},
			"location": {"display_name": "Berlin"},
			"description": "desc",
			"redirect_url": "https://example.com",
		}
		result = service._normalize_adzuna_job(job)
		assert result["company"] == "Tech"
		assert result["source"] == "adzuna"

	def test_normalize_remoteok_job(self, service):
		job = {
			"position": "Data Engineer",
			"company": "Data Corp",
			"location": "Remote",
			"description": "desc",
			"url": "https://example.com",
		}
		result = service._normalize_remoteok_job(job)
		assert result["title"] == "Data Engineer"
		assert result["source"] == "remoteok"


class TestJobManagementSystemIntegration:
	"""Retain lightweight integration tests for composed services."""

	@pytest.fixture
	def mock_db(self):
		return MagicMock(spec=Session)

	@pytest.fixture
	def service(self, mock_db):
		return JobManagementSystem(db=mock_db)

	def test_notification_service_integration(self, service):
		assert service.notification_service is not None
		assert hasattr(service.notification_service, "create_notification")

	def test_skill_matcher_integration(self, service):
		assert service.skill_matcher is not None

	def test_quota_manager_integration(self, service):
		assert service.quota_manager is not None


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
