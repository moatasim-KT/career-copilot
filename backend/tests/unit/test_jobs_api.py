"""Tests for the Jobs API endpoints"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.security import create_access_token


def create_user(db: Session, username: str = "testuser", email: str = "test@example.com") -> User:
	user = User(username=username, email=email, hashed_password="fake_password")
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


def create_job(db: Session, user_id: int, company: str = "Test Inc", title: str = "Tester") -> Job:
	job = Job(user_id=user_id, company=company, title=title)
	db.add(job)
	db.commit()
	db.refresh(job)
	return job


def create_application(db: Session, user_id: int, job_id: int) -> Application:
	app = Application(user_id=user_id, job_id=job_id, status="applied")
	db.add(app)
	db.commit()
	db.refresh(app)
	return app


def get_auth_headers(user_id: int, username: str) -> dict:
	token = create_access_token({"sub": username, "user_id": user_id})
	return {"Authorization": f"Bearer {token}"}


def test_list_jobs_pagination(client: TestClient, db: Session):
	"""Verify that the GET /jobs endpoint correctly handles pagination."""
	user = create_user(db)
	headers = get_auth_headers(user.id, user.username)

	# Create 2 jobs for the user
	create_job(db, user.id, title="Job 1")
	create_job(db, user.id, title="Job 2")

	# Test limit
	response = client.get("/api/v1/jobs?limit=1", headers=headers)
	assert response.status_code == 200
	assert len(response.json()) == 1
	assert response.json()[0]["title"] == "Job 1"

	# Test skip
	response = client.get("/api/v1/jobs?skip=1&limit=1", headers=headers)
	assert response.status_code == 200
	assert len(response.json()) == 1
	assert response.json()[0]["title"] == "Job 2"


def test_delete_job_cascade(client: TestClient, db: Session):
	"""Verify that deleting a job also deletes its associated applications."""
	user = create_user(db)
	headers = get_auth_headers(user.id, user.username)

	job = create_job(db, user.id)
	application = create_application(db, user.id, job.id)

	# Verify application exists
	assert db.query(Application).count() == 1

	# Delete the job
	response = client.delete(f"/api/v1/jobs/{job.id}", headers=headers)
	assert response.status_code == 200
	assert response.json()["message"] == "Job deleted successfully"

	# Verify job is deleted
	assert db.query(Job).count() == 0
	# Verify application is also deleted due to cascade
	assert db.query(Application).count() == 0


def test_delete_job_not_found(client: TestClient, db: Session):
	"""Verify that trying to delete a non-existent job returns a 404 error."""
	user = create_user(db)
	headers = get_auth_headers(user.id, user.username)

	response = client.delete("/api/v1/jobs/999", headers=headers)
	assert response.status_code == 404
	assert response.json()["detail"] == "Job not found"


def test_delete_job_unauthorized(client: TestClient, db: Session):
	"""Verify that a user cannot delete a job belonging to another user."""
	user1 = create_user(db, username="user1", email="user1@test.com")
	user2 = create_user(db, username="user2", email="user2@test.com")

	job_of_user1 = create_job(db, user1.id)

	# Authenticate as user2
	headers_user2 = get_auth_headers(user2.id, user2.username)

	# Try to delete user1's job
	response = client.delete(f"/api/v1/jobs/{job_of_user1.id}", headers=headers_user2)

	# The endpoint should return 404 as the job is not found for this user
	assert response.status_code == 404
	assert response.json()["detail"] == "Job not found"

	# Verify the job still exists in the database
	assert db.query(Job).count() == 1
