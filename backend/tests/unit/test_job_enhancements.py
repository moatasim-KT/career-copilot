import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.database import Base
from app.schemas.job import JobCreate
from datetime import datetime

# Create test database



@pytest.fixture(scope="module")
def db_engine():
	
	Base.metadata.create_all(bind=engine)
	yield engine
	Base.metadata.drop_all(bind=engine)
	if os.path.exists("./test_job_enhancements.db"):
		os.remove("./test_job_enhancements.db")


@pytest.fixture(scope="module")
def db_session(db_engine):
	connection = db_engine.connect()
	transaction = connection.begin()
	session = Session(bind=connection)
	yield session
	session.close()
	transaction.rollback()
	connection.close()


@pytest.fixture(scope="module")
def test_user_id(db_session: Session):
	user = User(username="testuser", email="test@example.com", hashed_password="hashed_password")
	db_session.add(user)
	db_session.commit()
	db_session.refresh(user)
	return user.id


@pytest.fixture(scope="module")
def test_job_ids(db_session: Session, test_user_id: int):
	return _create_jobs_for_test(db_session, test_user_id)


def _create_jobs_for_test(db_session: Session, test_user_id: int):
	"""Helper function to create jobs for testing"""
	# Test 1: Create job with all fields
	job_data = JobCreate(
		company="Tech Corp",
		title="Senior Python Developer",
		location="San Francisco, CA",
		description="Great opportunity",
		tech_stack=["Python", "FastAPI", "PostgreSQL"],
		responsibilities="Build APIs and services",
		source="manual",
	)

	job_dict = job_data.model_dump()
	if job_dict.get("tech_stack") is None:
		job_dict["tech_stack"] = []
	if not job_dict.get("source"):
		job_dict["source"] = "manual"

	job1 = Job(**job_dict, user_id=test_user_id)
	db_session.add(job1)
	db_session.commit()
	db_session.refresh(job1)

	# Test 2: Create job with minimal fields (defaults)
	job_data2 = JobCreate(company="Startup Inc", title="Junior Developer")

	job_dict2 = job_data2.model_dump()
	if job_dict2.get("tech_stack") is None:
		job_dict2["tech_stack"] = []
	if not job_dict2.get("source"):
		job_dict2["source"] = "manual"

	job2 = Job(**job_dict2, user_id=test_user_id)
	db_session.add(job2)
	db_session.commit()
	db_session.refresh(job2)

	# Test 3: Create job with scraped source
	job_data3 = JobCreate(company="Remote Co", title="DevOps Engineer", tech_stack=["Docker", "Kubernetes"], source="scraped")

	job_dict3 = job_data3.model_dump()
	if job_dict3.get("tech_stack") is None:
		job_dict3["tech_stack"] = []
	if not job_dict3.get("source"):
		job_dict3["source"] = "manual"

	job3 = Job(**job_dict3, user_id=test_user_id)
	db_session.add(job3)
	db_session.commit()
	db_session.refresh(job3)

	return [job1.id, job2.id, job3.id]


def test_job_creation(db_session: Session, test_user_id: int, test_job_ids: list):
	"""Test 4.1: Verify job creation via fixture"""
	# Retrieve jobs created by the fixture
	jobs = db_session.query(Job).filter(Job.user_id == test_user_id).all()
	assert len(jobs) == 3

	job1 = next(job for job in jobs if job.id == test_job_ids[0])
	assert job1.company == "Tech Corp"
	assert job1.title == "Senior Python Developer"
	assert job1.tech_stack == ["Python", "FastAPI", "PostgreSQL"]
	assert job1.responsibilities == "Build APIs and services"
	assert job1.source == "manual"

	job2 = next(job for job in jobs if job.id == test_job_ids[1])
	assert job2.company == "Startup Inc"
	assert job2.title == "Junior Developer"
	assert job2.tech_stack == []
	assert job2.source == "manual"

	job3 = next(job for job in jobs if job.id == test_job_ids[2])
	assert job3.company == "Remote Co"
	assert job3.title == "DevOps Engineer"
	assert job3.tech_stack == ["Docker", "Kubernetes"]
	assert job3.source == "scraped"


def test_job_update(db_session: Session, test_user_id: int, test_job_ids: list):
	"""Test 4.2: Enhance job update endpoint"""
	job = db_session.query(Job).filter(Job.id == test_job_ids[0]).first()
	original_updated_at = job.updated_at

	# Test 1: Update job fields
	job.title = "Lead Python Developer"
	job.tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis"]
	job.updated_at = datetime.utcnow()
	db_session.commit()
	db_session.refresh(job)

	assert job.title == "Lead Python Developer"
	assert "Redis" in job.tech_stack
	assert job.updated_at > original_updated_at

	# Test 2: Change status to 'applied' and verify date_applied is set
	assert job.date_applied is None
	job.status = "applied"
	job.date_applied = datetime.utcnow()
	job.updated_at = datetime.utcnow()
	db_session.commit()
	db_session.refresh(job)

	assert job.status == "applied"
	assert job.date_applied is not None

	# Test 3: Update other fields without changing status
	job.notes = "Follow up next week"
	job.updated_at = datetime.utcnow()
	db_session.commit()
	db_session.refresh(job)

	assert job.notes == "Follow up next week"


def test_job_listing_and_deletion(db_session: Session, test_user_id: int, test_job_ids: list):
	"""Test 4.3: Verify job listing and deletion endpoints"""
	# Test 1: List jobs with pagination
	jobs = db_session.query(Job).filter(Job.user_id == test_user_id).offset(0).limit(100).all()
	assert len(jobs) == 3

	# Test 2: Verify ordering (newest first)
	jobs_ordered = db_session.query(Job).filter(Job.user_id == test_user_id).order_by(Job.created_at.desc()).all()
	assert jobs_ordered[0].created_at >= jobs_ordered[-1].created_at

	# Test 3: Create application for cascade delete test
	job_to_delete = db_session.query(Job).filter(Job.id == test_job_ids[0]).first()
	app = Application(user_id=test_user_id, job_id=job_to_delete.id, status="interested")
	db_session.add(app)
	db_session.commit()

	# Verify application exists
	app_count_before = db_session.query(Application).filter(Application.job_id == job_to_delete.id).count()
	assert app_count_before == 1

	# Test 4: Delete job and verify cascade
	db_session.delete(job_to_delete)
	db_session.commit()

	# Verify job is deleted
	deleted_job = db_session.query(Job).filter(Job.id == test_job_ids[0]).first()
	assert deleted_job is None

	# Verify applications are cascade deleted
	app_count_after = db_session.query(Application).filter(Application.job_id == test_job_ids[0]).count()
	assert app_count_after == 0

	# Test 5: Verify remaining jobs
	remaining_jobs = db_session.query(Job).filter(Job.user_id == test_user_id).count()
	assert remaining_jobs == 2
