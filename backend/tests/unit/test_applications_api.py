"""Tests for application API endpoints"""

import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.application import Application
from app.models.job import Job
from app.models.user import User


async def get_test_user(db: AsyncSession) -> User:
	"""Get the test user that was created by the async_db fixture (id=1)"""
	result = await db.execute(select(User).where(User.id == 1))
	user = result.scalar_one_or_none()
	if not user:
		raise RuntimeError("Test user (id=1) not found. Check async_db fixture.")
	return user


async def create_user_async(db: AsyncSession, username: str = None, email: str = None) -> User:
	"""Create a test user with unique credentials (async)"""
	if username is None:
		unique_id = str(uuid.uuid4())[:8]
		username = f"testuser_{unique_id}"
	if email is None:
		unique_id = str(uuid.uuid4())[:8]
		email = f"test_{unique_id}@example.com"

	# Use naive datetime to avoid timezone issues with PostgreSQL TIMESTAMP WITHOUT TIME ZONE
	now = datetime.utcnow()
	user = User(username=username, email=email, hashed_password="fake_password", created_at=now, updated_at=now)
	db.add(user)
	await db.commit()
	await db.refresh(user)
	return user


async def create_job_async(db: AsyncSession, user_id: int, company: str = "Test Inc", title: str = "Software Engineer") -> Job:
	"""Create a test job (async)"""
	now = datetime.utcnow()
	job = Job(user_id=user_id, company=company, title=title, status="active", created_at=now, updated_at=now)
	db.add(job)
	await db.commit()
	await db.refresh(job)
	return job


def get_auth_headers(user_id: int, username: str) -> dict:
	"""Get authentication headers for testing"""
	token = create_access_token({"sub": username, "user_id": user_id})
	return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_application(async_client: AsyncClient, async_db: AsyncSession):
	"""Test creating a new application"""
	user = await get_test_user(async_db)
	job = await create_job_async(async_db, user.id)
	headers = get_auth_headers(user.id, user.username)

	# Test data
	application_data = {"job_id": job.id, "status": "interested", "notes": "Test application"}

	response = await async_client.post("/api/v1/applications", json=application_data, headers=headers)

	assert response.status_code == 200
	data = response.json()
	assert data["job_id"] == job.id
	assert data["status"] == "interested"
	assert data["notes"] == "Test application"
	assert data["user_id"] == user.id


@pytest.mark.asyncio
async def test_list_applications(async_client: AsyncClient, async_db: AsyncSession):
	"""Test listing applications"""
	user = await get_test_user(async_db)
	job = await create_job_async(async_db, user.id)
	headers = get_auth_headers(user.id, user.username)

	# Create test application
	now = datetime.utcnow()
	application = Application(user_id=user.id, job_id=job.id, status="applied", notes="Test application", created_at=now, updated_at=now)
	async_db.add(application)
	await async_db.commit()

	response = await async_client.get("/api/v1/applications", headers=headers)

	assert response.status_code == 200
	data = response.json()
	# Test that our application is in the list (may have applications from other tests)
	assert len(data) >= 1
	assert any(app["status"] == "applied" and app["notes"] == "Test application" for app in data)


@pytest.mark.asyncio
async def test_update_application_status_to_applied(async_client: AsyncClient, async_db: AsyncSession):
	"""Test updating application status to 'applied' updates job status and date"""
	user = await get_test_user(async_db)
	job = await create_job_async(async_db, user.id)
	headers = get_auth_headers(user.id, user.username)

	# Create test application with initial status
	now = datetime.utcnow()
	application = Application(user_id=user.id, job_id=job.id, status="interested", notes="Test application", created_at=now, updated_at=now)
	async_db.add(application)
	await async_db.commit()
	await async_db.refresh(application)

	# Update application status to 'applied'
	update_data = {"status": "applied"}
	response = await async_client.put(f"/api/v1/applications/{application.id}", json=update_data, headers=headers)

	assert response.status_code == 200
	data = response.json()
	assert data["status"] == "applied"

	# Verify job was updated
	await async_db.refresh(job)
	assert job.status == "applied"
	assert job.date_applied is not None


@pytest.mark.asyncio
async def test_status_validation(async_client: AsyncClient, async_db: AsyncSession):
	"""Test that invalid status values are rejected"""
	user = await get_test_user(async_db)
	job = await create_job_async(async_db, user.id)
	headers = get_auth_headers(user.id, user.username)

	# Test invalid status in create
	invalid_data = {"job_id": job.id, "status": "invalid_status", "notes": "Test application"}

	response = await async_client.post("/api/v1/applications", json=invalid_data, headers=headers)
	assert response.status_code in [400, 422]  # Validation error (400 from custom handler, 422 from FastAPI default)


@pytest.mark.asyncio
async def test_status_transitions(async_client: AsyncClient, async_db: AsyncSession):
	"""Test various status transitions"""
	user = await get_test_user(async_db)
	job = await create_job_async(async_db, user.id)
	headers = get_auth_headers(user.id, user.username)

	# Create test application
	now = datetime.utcnow()
	application = Application(user_id=user.id, job_id=job.id, status="interested", notes="Test application", created_at=now, updated_at=now)
	async_db.add(application)
	await async_db.commit()
	await async_db.refresh(application)

	# Test valid status transitions
	valid_statuses = ["applied", "interview", "offer", "accepted", "rejected", "declined"]

	for status in valid_statuses:
		update_data = {"status": status}
		response = await async_client.put(f"/api/v1/applications/{application.id}", json=update_data, headers=headers)
		assert response.status_code == 200
		data = response.json()
		assert data["status"] == status


@pytest.mark.asyncio
async def test_application_not_found(async_client: AsyncClient, async_db: AsyncSession):
	"""Test handling of non-existent application"""
	user = await get_test_user(async_db)
	headers = get_auth_headers(user.id, user.username)

	# Try to update non-existent application
	response = await async_client.put("/api/v1/applications/999", json={"status": "applied"}, headers=headers)
	assert response.status_code == 404
	assert "Application not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_application_prevention(async_client: AsyncClient, async_db: AsyncSession):
	"""Test that duplicate applications for the same job are prevented"""
	user = await get_test_user(async_db)
	job = await create_job_async(async_db, user.id)
	headers = get_auth_headers(user.id, user.username)

	# Create first application
	now = datetime.utcnow()
	application = Application(user_id=user.id, job_id=job.id, status="applied", created_at=now, updated_at=now)
	async_db.add(application)
	await async_db.commit()

	# Try to create duplicate application
	duplicate_data = {"job_id": job.id, "status": "interested"}

	response = await async_client.post("/api/v1/applications", json=duplicate_data, headers=headers)
	assert response.status_code == 400
	assert "Application already exists" in response.json()["detail"]
