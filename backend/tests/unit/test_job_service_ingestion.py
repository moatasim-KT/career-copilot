"""Additional coverage tests for JobManagementSystem ingestion and helpers."""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import Session

from app.models.job import Job
from app.services.job_service import JobManagementSystem


@pytest.fixture
def job_service(db: Session) -> JobManagementSystem:
	"""Provide a JobManagementSystem wired to the real test database session."""
	return JobManagementSystem(db)


def _sample_job(title: str, url: str) -> Dict[str, Any]:
	return {
		"title": title,
		"company": "Test Corp",
		"location": "Remote",
		"description": "Exciting role",
		"source_url": url,
		"source": "scraped",
		"salary_min": 50000,
		"salary_max": 80000,
		"job_type": "full-time",
		"remote_option": "remote",
	}


def test_ingest_jobs_for_user_saves_unique_jobs(db: Session, test_user, job_service: JobManagementSystem, monkeypatch):
	"""Verify ingest_jobs_for_user persists new jobs and tracks duplicates."""

	sample_jobs = [
		_sample_job("Engineer", "https://example.com/jobs/1"),
		_sample_job("Engineer", "https://example.com/jobs/1"),
		_sample_job("Designer", "https://example.com/jobs/2"),
	]

	monkeypatch.setattr(job_service, "_scrape_sync", lambda prefs: sample_jobs)

	result = job_service.ingest_jobs_for_user(user_id=test_user.id, max_jobs=10)

	assert result["jobs_found"] == len(sample_jobs)
	assert result["jobs_saved"] == 2  # duplicate filtered
	assert result["duplicates_filtered"] == 1
	saved_jobs = db.query(Job).filter(Job.user_id == test_user.id).all()
	assert len(saved_jobs) == 2
	assert {job.title for job in saved_jobs} == {"Engineer", "Designer"}


def test_ingest_jobs_for_user_missing_user_returns_error(job_service: JobManagementSystem):
	"""Ensure ingest_jobs_for_user gracefully handles unknown users."""

	result = job_service.ingest_jobs_for_user(user_id=99999, max_jobs=5)

	assert result["jobs_saved"] == 0
	assert result["jobs_found"] == 0
	assert result["duplicates_filtered"] == 0
	assert result["errors"]
	assert any("not found" in error.lower() for error in result["errors"])


def test_scrape_sync_runs_async_scrape(monkeypatch, job_service: JobManagementSystem):
	"""_scrape_sync should run the async scrape_jobs helper and return its payload."""

	async_mock = AsyncMock(return_value=[{"title": "Async role"}])
	monkeypatch.setattr(job_service, "scrape_jobs", async_mock)

	prefs = {"skills": ["python"], "locations": ["Remote"], "max_jobs": 5}
	result = job_service._scrape_sync(prefs)

	assert result == [{"title": "Async role"}]
	async_mock.assert_awaited()


def test_normalize_adzuna_job_handles_missing_fields(job_service: JobManagementSystem):
	"""Normalization should provide defaults for Adzuna payloads."""

	payload = {"title": "Role", "company": {}, "location": {}, "description": "desc", "redirect_url": "https://adzuna/job/1"}
	normalized = job_service._normalize_adzuna_job(payload)

	assert normalized["company"] == ""
	assert normalized["location"] == ""
	assert normalized["source"] == "adzuna"
	assert normalized["url"].startswith("https://adzuna")


def test_normalize_remoteok_job_handles_missing_fields(job_service: JobManagementSystem):
	"""Normalization should handle RemoteOK payload shapes consistently."""

	payload = {"position": "Remote Engineer", "company": "Remote Inc", "url": "https://remoteok.com/1"}
	normalized = job_service._normalize_remoteok_job(payload)

	assert normalized["title"] == "Remote Engineer"
	assert normalized["company"] == "Remote Inc"
	assert normalized["source"] == "remoteok"
	assert normalized["salary_min"] is None
	assert normalized["salary_max"] is None
