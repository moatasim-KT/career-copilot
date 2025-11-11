"""
Comprehensive tests for data import functionality
Tests CSV import for jobs and applications with various scenarios
"""

import pytest
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.import_service import import_service
from app.models.job import Job
from app.models.application import Application
from app.models.user import User


@pytest.mark.asyncio
async def test_import_jobs_csv_basic(db: AsyncSession):
    """Test basic CSV import of jobs"""
    # Create test user
    user = User(email="import_test@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create CSV content
    csv_content = """company,title,location,job_type,remote_option,salary_min,salary_max,tech_stack,status
Tech Corp,Software Engineer,San Francisco,full-time,hybrid,120000,180000,"Python, FastAPI, PostgreSQL",not_applied
Data Inc,Data Scientist,Remote,full-time,remote,130000,200000,"Python, SQL, Machine Learning",not_applied
Web Solutions,Frontend Developer,New York,contract,onsite,90000,140000,"JavaScript, React, TypeScript",applied"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.total_records == 3
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.created_ids) == 3

    # Verify jobs were created
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id))
    jobs = jobs_result.scalars().all()
    assert len(jobs) == 3

    # Verify first job details
    job1 = next(j for j in jobs if j.company == "Tech Corp")
    assert job1.title == "Software Engineer"
    assert job1.location == "San Francisco"
    assert job1.job_type == "full-time"
    assert job1.remote_option == "hybrid"
    assert job1.salary_min == 120000
    assert job1.salary_max == 180000
    assert "Python" in job1.tech_stack
    assert "FastAPI" in job1.tech_stack
    assert job1.status == "not_applied"


@pytest.mark.asyncio
async def test_import_jobs_csv_with_missing_optional_fields(db: AsyncSession):
    """Test CSV import with missing optional fields"""
    # Create test user
    user = User(email="import_test2@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create CSV with minimal required fields
    csv_content = """company,title
Minimal Corp,Basic Job
Another Co,Simple Position"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.successful == 2
    assert result.failed == 0

    # Verify jobs were created with defaults
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id))
    jobs = jobs_result.scalars().all()
    assert len(jobs) == 2

    job = jobs[0]
    assert job.company == "Minimal Corp"
    assert job.title == "Basic Job"
    assert job.status == "not_applied"
    assert job.source == "manual"


@pytest.mark.asyncio
async def test_import_jobs_csv_with_invalid_rows(db: AsyncSession):
    """Test CSV import with some invalid rows"""
    # Create test user
    user = User(email="import_test3@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create CSV with some invalid rows (missing required fields)
    csv_content = """company,title,location
Valid Corp,Valid Job,Valid Location
,Missing Company,Location
Invalid Inc,,Missing Title
Another Valid,Another Job,Another Location"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.total_records == 4
    assert result.successful == 2  # Only 2 valid rows
    assert result.failed == 2  # 2 invalid rows
    assert len(result.errors) == 2

    # Verify only valid jobs were created
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id))
    jobs = jobs_result.scalars().all()
    assert len(jobs) == 2
    assert all(j.company and j.title for j in jobs)


@pytest.mark.asyncio
async def test_import_jobs_csv_with_tech_stack_parsing(db: AsyncSession):
    """Test CSV import with tech stack parsing"""
    # Create test user
    user = User(email="import_test4@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create CSV with various tech stack formats
    csv_content = """company,title,tech_stack
Tech1,Job1,"Python, FastAPI, PostgreSQL"
Tech2,Job2,"JavaScript,React,Node.js"
Tech3,Job3,Single Tech
Tech4,Job4,"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.successful == 4

    # Verify tech stack parsing
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id).order_by(Job.id))
    jobs = jobs_result.scalars().all()

    # Job with comma-separated tech stack
    assert len(jobs[0].tech_stack) == 3
    assert "Python" in jobs[0].tech_stack
    assert "FastAPI" in jobs[0].tech_stack

    # Job with no spaces after commas
    assert len(jobs[1].tech_stack) == 3
    assert "JavaScript" in jobs[1].tech_stack

    # Job with single tech
    assert len(jobs[2].tech_stack) == 1
    assert "Single Tech" in jobs[2].tech_stack

    # Job with empty tech stack
    assert jobs[3].tech_stack is None or len(jobs[3].tech_stack) == 0


@pytest.mark.asyncio
async def test_import_jobs_csv_with_dates(db: AsyncSession):
    """Test CSV import with date fields"""
    # Create test user
    user = User(email="import_test5@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create CSV with date fields
    csv_content = """company,title,date_applied,status
DateCorp,Job With Date,2024-01-15,applied
NoDates,Job Without Date,,not_applied"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.successful == 2

    # Verify date parsing
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id).order_by(Job.id))
    jobs = jobs_result.scalars().all()

    # Job with date
    assert jobs[0].date_applied is not None
    assert jobs[0].date_applied.year == 2024
    assert jobs[0].date_applied.month == 1
    assert jobs[0].date_applied.day == 15

    # Job without date
    assert jobs[1].date_applied is None


@pytest.mark.asyncio
async def test_import_applications_csv_basic(db: AsyncSession):
    """Test basic CSV import of applications"""
    # Create test user
    user = User(email="app_import_test@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create test jobs first
    job1 = Job(user_id=user.id, company="Company A", title="Job A", status="not_applied")
    job2 = Job(user_id=user.id, company="Company B", title="Job B", status="not_applied")
    db.add_all([job1, job2])
    await db.commit()
    await db.refresh(job1)
    await db.refresh(job2)

    # Create CSV content
    csv_content = f"""job_id,status,applied_date,notes
{job1.id},applied,2024-01-10,First application
{job2.id},interview,2024-01-15,Got interview call"""

    # Import applications
    result = await import_service.import_applications_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.total_records == 2
    assert result.successful == 2
    assert result.failed == 0
    assert len(result.created_ids) == 2

    # Verify applications were created
    apps_result = await db.execute(select(Application).where(Application.user_id == user.id))
    apps = apps_result.scalars().all()
    assert len(apps) == 2

    # Verify first application details
    app1 = next(a for a in apps if a.job_id == job1.id)
    assert app1.status == "applied"
    assert app1.applied_date == date(2024, 1, 10)
    assert app1.notes == "First application"


@pytest.mark.asyncio
async def test_import_applications_csv_with_invalid_job_id(db: AsyncSession):
    """Test CSV import with invalid job IDs"""
    # Create test user
    user = User(email="app_import_test2@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create one valid job
    job = Job(user_id=user.id, company="Valid Company", title="Valid Job", status="not_applied")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Create CSV with valid and invalid job IDs
    csv_content = f"""job_id,status,applied_date
{job.id},applied,2024-01-10
99999,applied,2024-01-11
{job.id + 1000},interview,2024-01-12"""

    # Import applications
    result = await import_service.import_applications_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.total_records == 3
    assert result.successful == 1  # Only 1 valid job_id
    assert result.failed == 2  # 2 invalid job_ids
    assert len(result.errors) == 2

    # Verify only valid application was created
    apps_result = await db.execute(select(Application).where(Application.user_id == user.id))
    apps = apps_result.scalars().all()
    assert len(apps) == 1
    assert apps[0].job_id == job.id


@pytest.mark.asyncio
async def test_import_applications_csv_with_all_date_fields(db: AsyncSession):
    """Test CSV import with all date fields"""
    # Create test user
    user = User(email="app_import_test3@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create test job
    job = Job(user_id=user.id, company="Date Test Co", title="Date Job", status="not_applied")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Create CSV with all date fields
    csv_content = f"""job_id,status,applied_date,response_date,interview_date,offer_date,follow_up_date
{job.id},offer,2024-01-10,2024-01-15,2024-01-20T10:00:00,2024-01-25,2024-02-01"""

    # Import applications
    result = await import_service.import_applications_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.successful == 1

    # Verify all dates were parsed correctly
    apps_result = await db.execute(select(Application).where(Application.user_id == user.id))
    app = apps_result.scalar_one()

    assert app.applied_date == date(2024, 1, 10)
    assert app.response_date == date(2024, 1, 15)
    assert app.interview_date.year == 2024
    assert app.interview_date.month == 1
    assert app.interview_date.day == 20
    assert app.offer_date == date(2024, 1, 25)
    assert app.follow_up_date == date(2024, 2, 1)


@pytest.mark.asyncio
async def test_import_applications_csv_with_interview_feedback(db: AsyncSession):
    """Test CSV import with interview feedback JSON"""
    # Create test user
    user = User(email="app_import_test4@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create test job
    job = Job(user_id=user.id, company="Feedback Co", title="Feedback Job", status="not_applied")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Create CSV with interview feedback
    feedback_json = '{"questions": ["Tell me about yourself", "Technical question"], "rating": 4}'
    csv_content = f"""job_id,status,interview_feedback
{job.id},interview,"{feedback_json}\""""

    # Import applications
    result = await import_service.import_applications_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.successful == 1

    # Verify interview feedback was parsed
    apps_result = await db.execute(select(Application).where(Application.user_id == user.id))
    app = apps_result.scalar_one()

    assert app.interview_feedback is not None
    assert "questions" in app.interview_feedback
    assert len(app.interview_feedback["questions"]) == 2
    assert app.interview_feedback["rating"] == 4


@pytest.mark.asyncio
async def test_import_applications_csv_with_invalid_status(db: AsyncSession):
    """Test CSV import with invalid status values"""
    # Create test user
    user = User(email="app_import_test5@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create test job
    job = Job(user_id=user.id, company="Status Test Co", title="Status Job", status="not_applied")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Create CSV with invalid status (should default to "interested")
    csv_content = f"""job_id,status
{job.id},invalid_status
{job.id},applied"""

    # Import applications
    result = await import_service.import_applications_csv(db, user.id, csv_content)

    # Verify result - invalid status should be converted to default
    assert result.success is True
    assert result.successful == 2

    # Verify status handling
    apps_result = await db.execute(select(Application).where(Application.user_id == user.id).order_by(Application.id))
    apps = apps_result.scalars().all()

    # First app with invalid status should default to "interested"
    assert apps[0].status == "interested"
    # Second app should have correct status
    assert apps[1].status == "applied"


@pytest.mark.asyncio
async def test_import_jobs_csv_empty_file(db: AsyncSession):
    """Test CSV import with empty file"""
    # Create test user
    user = User(email="empty_test@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create empty CSV (only header)
    csv_content = """company,title,location"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.total_records == 0
    assert result.successful == 0
    assert result.failed == 0


@pytest.mark.asyncio
async def test_import_jobs_csv_with_special_characters(db: AsyncSession):
    """Test CSV import with special characters in fields"""
    # Create test user
    user = User(email="special_test@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create CSV with special characters
    csv_content = """company,title,description,notes
"Tech, Inc.",Senior Engineer,"Job with ""quotes"" and commas","Notes with
newlines and special chars: @#$%"""

    # Import jobs
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify result
    assert result.success is True
    assert result.successful == 1

    # Verify special characters were handled
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id))
    job = jobs_result.scalar_one()

    assert job.company == "Tech, Inc."
    assert job.title == "Senior Engineer"
    assert "quotes" in job.description
    assert "commas" in job.description


@pytest.mark.asyncio
async def test_import_rollback_on_error(db: AsyncSession):
    """Test that import rolls back on critical errors"""
    # Create test user
    user = User(email="rollback_test@example.com", hashed_password="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create malformed CSV that will cause parsing error
    csv_content = "This is not valid CSV content at all"

    # Import should fail gracefully
    result = await import_service.import_jobs_csv(db, user.id, csv_content)

    # Verify no jobs were created
    jobs_result = await db.execute(select(Job).where(Job.user_id == user.id))
    jobs = jobs_result.scalars().all()
    assert len(jobs) == 0
