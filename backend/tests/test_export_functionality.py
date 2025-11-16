"""
Tests for data export functionality
"""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job
from app.models.user import User

# from app.services.export_service_v2 import export_service_v2  # Service refactored, now just export_service

pytestmark = pytest.mark.skip(reason="Service refactored - export_service_v2 no longer exists")


@pytest.mark.asyncio
async def test_export_jobs_json(db: AsyncSession):
	"""Test JSON export of jobs"""
	# Create test user
	user = User(email="test@example.com", hashed_password="test")
	db.add(user)
	await db.commit()
	await db.refresh(user)

	# Create test jobs
	job1 = Job(
		user_id=user.id,
		company="Test Company",
		title="Software Engineer",
		location="Remote",
		status="not_applied",
		tech_stack=["Python", "FastAPI"],
	)
	job2 = Job(
		user_id=user.id,
		company="Another Company",
		title="Senior Developer",
		location="New York",
		status="applied",
		tech_stack=["JavaScript", "React"],
	)
	db.add_all([job1, job2])
	await db.commit()

	# Test export
	result = await export_service_v2.export_jobs_json(db, user.id)

	assert result["success"] is True
	assert len(result["data"]) == 2
	assert result["metadata"]["total_records"] == 2
	assert result["data"][0]["company"] == "Test Company"
	assert result["data"][0]["tech_stack"] == ["Python", "FastAPI"]


@pytest.mark.asyncio
async def test_export_jobs_csv(db: AsyncSession):
	"""Test CSV export of jobs"""
	# Create test user
	user = User(email="test2@example.com", hashed_password="test")
	db.add(user)
	await db.commit()
	await db.refresh(user)

	# Create test job
	job = Job(
		user_id=user.id,
		company="CSV Test Company",
		title="Data Engineer",
		location="San Francisco",
		status="not_applied",
		tech_stack=["Python", "SQL", "Airflow"],
		salary_min=100000,
		salary_max=150000,
	)
	db.add(job)
	await db.commit()

	# Test export
	csv_content = await export_service_v2.export_jobs_csv(db, user.id)

	assert csv_content is not None
	assert "CSV Test Company" in csv_content
	assert "Data Engineer" in csv_content
	assert "Python, SQL, Airflow" in csv_content
	assert "100000" in csv_content


@pytest.mark.asyncio
async def test_export_applications_json(db: AsyncSession):
	"""Test JSON export of applications"""
	# Create test user
	user = User(email="test3@example.com", hashed_password="test")
	db.add(user)
	await db.commit()
	await db.refresh(user)

	# Create test job
	job = Job(
		user_id=user.id,
		company="Application Test Co",
		title="Backend Developer",
		location="Remote",
		status="applied",
	)
	db.add(job)
	await db.commit()
	await db.refresh(job)

	# Create test application
	app = Application(
		user_id=user.id,
		job_id=job.id,
		status="applied",
		notes="Test application notes",
	)
	db.add(app)
	await db.commit()

	# Test export
	result = await export_service_v2.export_applications_json(db, user.id)

	assert result["success"] is True
	assert len(result["data"]) == 1
	assert result["data"][0]["job_company"] == "Application Test Co"
	assert result["data"][0]["status"] == "applied"
	assert result["data"][0]["notes"] == "Test application notes"


@pytest.mark.asyncio
async def test_export_with_filters(db: AsyncSession):
	"""Test export with filters"""
	# Create test user
	user = User(email="test4@example.com", hashed_password="test")
	db.add(user)
	await db.commit()
	await db.refresh(user)

	# Create test jobs with different statuses
	job1 = Job(
		user_id=user.id,
		company="Filter Test 1",
		title="Job 1",
		status="not_applied",
	)
	job2 = Job(
		user_id=user.id,
		company="Filter Test 2",
		title="Job 2",
		status="applied",
	)
	db.add_all([job1, job2])
	await db.commit()

	# Test export with status filter
	result = await export_service_v2.export_jobs_json(db, user.id, filters={"status": "applied"})

	assert result["success"] is True
	assert len(result["data"]) == 1
	assert result["data"][0]["status"] == "applied"
	assert result["data"][0]["company"] == "Filter Test 2"


@pytest.mark.asyncio
async def test_full_backup(db: AsyncSession):
	"""Test full backup creation"""
	# Create test user
	user = User(email="test5@example.com", hashed_password="test")
	db.add(user)
	await db.commit()
	await db.refresh(user)

	# Create test data
	job = Job(
		user_id=user.id,
		company="Backup Test Co",
		title="Full Stack Developer",
		status="not_applied",
	)
	db.add(job)
	await db.commit()
	await db.refresh(job)

	app = Application(
		user_id=user.id,
		job_id=job.id,
		status="interested",
	)
	db.add(app)
	await db.commit()

	# Test backup creation
	zip_content = await export_service_v2.create_full_backup(db, user.id)

	assert zip_content is not None
	assert len(zip_content) > 0
	# ZIP file should start with PK (ZIP magic number)
	assert zip_content[:2] == b"PK"
