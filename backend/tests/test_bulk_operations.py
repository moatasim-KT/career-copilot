"""
Comprehensive tests for bulk operations endpoints.
Tests bulk create, update, and delete operations for jobs and applications.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.schemas.bulk_operations import (
    ApplicationUpdateWithId,
    BulkApplicationCreateRequest,
    BulkApplicationUpdateRequest,
    BulkDeleteRequest,
    BulkJobCreateRequest,
    BulkJobUpdateRequest,
    JobUpdateWithId,
)
from app.schemas.job import JobCreate, JobUpdate
from app.services.bulk_operations_service import BulkOperationsService


# ============================================================================
# BULK CREATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_create_jobs_success(async_db: AsyncSession, async_test_user: User):
    """Test successful bulk creation of jobs"""
    service = BulkOperationsService(async_db)
    
    jobs_data = [
        JobCreate(
            company="Tech Corp",
            title="Senior Developer",
            location="San Francisco, CA",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            salary_min=120000,
            salary_max=180000
        ),
        JobCreate(
            company="Startup Inc",
            title="Full Stack Engineer",
            location="Remote",
            tech_stack=["JavaScript", "React", "Node.js"],
            remote_option="yes"
        ),
        JobCreate(
            company="Enterprise Co",
            title="DevOps Engineer",
            location="New York, NY",
            tech_stack=["Docker", "Kubernetes", "AWS"]
        )
    ]
    
    result = await service.bulk_create_jobs(jobs_data, async_test_user.id)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.created_ids) == 3
    assert len(result.errors) == 0
    
    # Verify jobs were created in database
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    jobs = db_result.scalars().all()
    
    assert len(jobs) == 3
    assert jobs[0].company == "Tech Corp"
    assert jobs[1].company == "Startup Inc"
    assert jobs[2].company == "Enterprise Co"


@pytest.mark.asyncio
async def test_bulk_create_jobs_with_validation_errors(async_db: AsyncSession, async_test_user: User):
    """Test bulk job creation with some invalid data"""
    service = BulkOperationsService(async_db)
    
    jobs_data = [
        JobCreate(
            company="Valid Corp",
            title="Developer",
            tech_stack=["Python"]
        ),
        JobCreate(
            company="",  # Invalid: empty company name
            title="Engineer",
            tech_stack=["Java"]
        ),
        JobCreate(
            company="Another Corp",
            title="Manager",
            tech_stack=["Leadership"]
        )
    ]
    
    result = await service.bulk_create_jobs(jobs_data, async_test_user.id)
    
    # First and third should succeed, second should fail
    assert result.total == 3
    assert result.successful == 2
    assert result.failed == 1
    assert len(result.created_ids) == 2
    assert len(result.errors) == 1
    assert result.errors[0].index == 1


@pytest.mark.asyncio
async def test_bulk_create_applications_success(async_db: AsyncSession, async_test_user: User):
    """Test successful bulk creation of applications"""
    # First create some jobs
    jobs = []
    for i in range(3):
        job = Job(
            user_id=async_test_user.id,
            company=f"Company {i}",
            title=f"Position {i}",
            tech_stack=["Python"]
        )
        async_db.add(job)
    await async_db.commit()
    
    # Get job IDs
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    jobs = result.scalars().all()
    job_ids = [job.id for job in jobs]
    
    service = BulkOperationsService(async_db)
    
    applications_data = [
        ApplicationCreate(
            job_id=job_ids[0],
            status="applied",
            notes="Applied via website"
        ),
        ApplicationCreate(
            job_id=job_ids[1],
            status="interested"
        ),
        ApplicationCreate(
            job_id=job_ids[2],
            status="interview",
            notes="Phone screen scheduled"
        )
    ]
    
    result = await service.bulk_create_applications(applications_data, async_test_user.id)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.created_ids) == 3
    assert len(result.errors) == 0
    
    # Verify applications were created
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    apps = db_result.scalars().all()
    
    assert len(apps) == 3


@pytest.mark.asyncio
async def test_bulk_create_applications_invalid_job_id(async_db: AsyncSession, async_test_user: User):
    """Test bulk application creation with invalid job IDs"""
    service = BulkOperationsService(async_db)
    
    applications_data = [
        ApplicationCreate(
            job_id=99999,  # Non-existent job
            status="applied"
        )
    ]
    
    result = await service.bulk_create_applications(applications_data, async_test_user.id)
    
    assert result.total == 1
    assert result.successful == 0
    assert result.failed == 1
    assert len(result.errors) == 1
    assert "not found" in result.errors[0].error.lower()


@pytest.mark.asyncio
async def test_bulk_create_applications_duplicate(async_db: AsyncSession, async_test_user: User):
    """Test bulk application creation with duplicate applications"""
    # Create a job
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    # Create first application
    app = Application(
        user_id=async_test_user.id,
        job_id=job.id,
        status="applied"
    )
    async_db.add(app)
    await async_db.commit()
    
    service = BulkOperationsService(async_db)
    
    # Try to create duplicate
    applications_data = [
        ApplicationCreate(
            job_id=job.id,
            status="interested"
        )
    ]
    
    result = await service.bulk_create_applications(applications_data, async_test_user.id)
    
    assert result.total == 1
    assert result.successful == 0
    assert result.failed == 1
    assert "already exists" in result.errors[0].error.lower()


# ============================================================================
# BULK UPDATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_update_jobs_success(async_db: AsyncSession, async_test_user: User):
    """Test successful bulk update of jobs"""
    # Create test jobs
    jobs = []
    for i in range(3):
        job = Job(
            user_id=async_test_user.id,
            company=f"Company {i}",
            title=f"Position {i}",
            status="not_applied",
            tech_stack=["Python"]
        )
        async_db.add(job)
    await async_db.commit()
    
    # Get job IDs
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    jobs = result.scalars().all()
    
    service = BulkOperationsService(async_db)
    
    updates = [
        (jobs[0].id, JobUpdate(status="applied", notes="Applied today")),
        (jobs[1].id, JobUpdate(salary_min=100000, salary_max=150000)),
        (jobs[2].id, JobUpdate(location="Remote", remote_option="yes"))
    ]
    
    result = await service.bulk_update_jobs(updates, async_test_user.id)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.updated_ids) == 3
    assert len(result.errors) == 0
    
    # Verify updates
    await async_db.refresh(jobs[0])
    await async_db.refresh(jobs[1])
    await async_db.refresh(jobs[2])
    
    assert jobs[0].status == "applied"
    assert jobs[0].notes == "Applied today"
    assert jobs[0].date_applied is not None  # Should be set automatically
    assert jobs[1].salary_min == 100000
    assert jobs[2].remote_option == "yes"


@pytest.mark.asyncio
async def test_bulk_update_jobs_invalid_id(async_db: AsyncSession, async_test_user: User):
    """Test bulk job update with invalid job ID"""
    service = BulkOperationsService(async_db)
    
    updates = [
        (99999, JobUpdate(status="applied"))
    ]
    
    result = await service.bulk_update_jobs(updates, async_test_user.id)
    
    assert result.total == 1
    assert result.successful == 0
    assert result.failed == 1
    assert "not found" in result.errors[0].error.lower()


@pytest.mark.asyncio
async def test_bulk_update_applications_success(async_db: AsyncSession, async_test_user: User):
    """Test successful bulk update of applications"""
    # Create job and applications
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    apps = []
    for i in range(3):
        app = Application(
            user_id=async_test_user.id,
            job_id=job.id,
            status="interested"
        )
        async_db.add(app)
    await async_db.commit()
    
    # Get application IDs
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    apps = result.scalars().all()
    
    service = BulkOperationsService(async_db)
    
    updates = [
        (apps[0].id, ApplicationUpdate(status="applied", notes="Submitted application")),
        (apps[1].id, ApplicationUpdate(status="interview")),
        (apps[2].id, ApplicationUpdate(status="rejected", notes="Position filled"))
    ]
    
    result = await service.bulk_update_applications(updates, async_test_user.id)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.updated_ids) == 3
    
    # Verify updates
    await async_db.refresh(apps[0])
    await async_db.refresh(apps[1])
    await async_db.refresh(apps[2])
    
    assert apps[0].status == "applied"
    assert apps[1].status == "interview"
    assert apps[2].status == "rejected"


@pytest.mark.asyncio
async def test_bulk_update_applications_updates_job_status(async_db: AsyncSession, async_test_user: User):
    """Test that updating application to 'applied' also updates job status"""
    # Create job and application
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        status="not_applied",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    app = Application(
        user_id=async_test_user.id,
        job_id=job.id,
        status="interested"
    )
    async_db.add(app)
    await async_db.commit()
    await async_db.refresh(app)
    
    service = BulkOperationsService(async_db)
    
    updates = [
        (app.id, ApplicationUpdate(status="applied"))
    ]
    
    result = await service.bulk_update_applications(updates, async_test_user.id)
    
    assert result.successful == 1
    
    # Verify job status was updated
    await async_db.refresh(job)
    assert job.status == "applied"
    assert job.date_applied is not None


# ============================================================================
# BULK DELETE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_delete_jobs_hard_delete(async_db: AsyncSession, async_test_user: User):
    """Test hard delete of multiple jobs"""
    # Create test jobs
    jobs = []
    for i in range(3):
        job = Job(
            user_id=async_test_user.id,
            company=f"Company {i}",
            title=f"Position {i}",
            tech_stack=["Python"]
        )
        async_db.add(job)
    await async_db.commit()
    
    # Get job IDs
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    jobs = result.scalars().all()
    job_ids = [job.id for job in jobs]
    
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_delete_jobs(job_ids, async_test_user.id, soft_delete=False)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert len(result.deleted_ids) == 3
    assert result.soft_deleted is False
    
    # Verify jobs were deleted
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    remaining_jobs = db_result.scalars().all()
    
    assert len(remaining_jobs) == 0


@pytest.mark.asyncio
async def test_bulk_delete_jobs_soft_delete(async_db: AsyncSession, async_test_user: User):
    """Test soft delete of multiple jobs"""
    # Create test jobs
    jobs = []
    for i in range(3):
        job = Job(
            user_id=async_test_user.id,
            company=f"Company {i}",
            title=f"Position {i}",
            status="not_applied",
            tech_stack=["Python"]
        )
        async_db.add(job)
    await async_db.commit()
    
    # Get job IDs
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    jobs = result.scalars().all()
    job_ids = [job.id for job in jobs]
    
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_delete_jobs(job_ids, async_test_user.id, soft_delete=True)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert result.soft_deleted is True
    
    # Verify jobs still exist but are marked as deleted
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    jobs = db_result.scalars().all()
    
    assert len(jobs) == 3
    for job in jobs:
        assert job.status == "deleted"


@pytest.mark.asyncio
async def test_bulk_delete_jobs_cascade_deletes_applications(async_db: AsyncSession, async_test_user: User):
    """Test that hard deleting jobs also deletes associated applications"""
    # Create job with applications
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    # Create applications
    for i in range(3):
        app = Application(
            user_id=async_test_user.id,
            job_id=job.id,
            status="applied"
        )
        async_db.add(app)
    await async_db.commit()
    
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_delete_jobs([job.id], async_test_user.id, soft_delete=False)
    
    assert result.successful == 1
    
    # Verify applications were also deleted
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    apps = db_result.scalars().all()
    
    assert len(apps) == 0


@pytest.mark.asyncio
async def test_bulk_delete_applications_hard_delete(async_db: AsyncSession, async_test_user: User):
    """Test hard delete of multiple applications"""
    # Create job and applications
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    apps = []
    for i in range(3):
        app = Application(
            user_id=async_test_user.id,
            job_id=job.id,
            status="applied"
        )
        async_db.add(app)
    await async_db.commit()
    
    # Get application IDs
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    apps = result.scalars().all()
    app_ids = [app.id for app in apps]
    
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_delete_applications(app_ids, async_test_user.id, soft_delete=False)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert result.soft_deleted is False
    
    # Verify applications were deleted
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    remaining_apps = db_result.scalars().all()
    
    assert len(remaining_apps) == 0


@pytest.mark.asyncio
async def test_bulk_delete_applications_soft_delete(async_db: AsyncSession, async_test_user: User):
    """Test soft delete of multiple applications"""
    # Create job and applications
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    apps = []
    for i in range(3):
        app = Application(
            user_id=async_test_user.id,
            job_id=job.id,
            status="applied"
        )
        async_db.add(app)
    await async_db.commit()
    
    # Get application IDs
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    result = await async_db.execute(stmt)
    apps = result.scalars().all()
    app_ids = [app.id for app in apps]
    
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_delete_applications(app_ids, async_test_user.id, soft_delete=True)
    
    assert result.total == 3
    assert result.successful == 3
    assert result.failed == 0
    assert result.soft_deleted is True
    
    # Verify applications still exist but are marked as deleted
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    apps = db_result.scalars().all()
    
    assert len(apps) == 3
    for app in apps:
        assert app.status == "deleted"


@pytest.mark.asyncio
async def test_bulk_delete_invalid_ids(async_db: AsyncSession, async_test_user: User):
    """Test bulk delete with invalid IDs"""
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_delete_jobs([99999, 88888], async_test_user.id, soft_delete=False)
    
    assert result.total == 2
    assert result.successful == 0
    assert result.failed == 2
    assert len(result.errors) == 2


# ============================================================================
# TRANSACTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_operations_use_transactions(async_db: AsyncSession, async_test_user: User):
    """Test that bulk operations use transactions properly"""
    # Create a job
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    service = BulkOperationsService(async_db)
    
    # Try to create applications with one invalid (should all succeed or all fail)
    applications_data = [
        ApplicationCreate(job_id=job.id, status="applied"),
        ApplicationCreate(job_id=99999, status="applied"),  # Invalid job_id
    ]
    
    result = await service.bulk_create_applications(applications_data, async_test_user.id)
    
    # First should succeed, second should fail
    assert result.successful == 1
    assert result.failed == 1
    
    # Verify only valid application was created
    stmt = select(Application).where(Application.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    apps = db_result.scalars().all()
    
    assert len(apps) == 1


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_create_empty_list(async_db: AsyncSession, async_test_user: User):
    """Test bulk create with empty list"""
    service = BulkOperationsService(async_db)
    
    result = await service.bulk_create_jobs([], async_test_user.id)
    
    assert result.total == 0
    assert result.successful == 0
    assert result.failed == 0


@pytest.mark.asyncio
async def test_bulk_update_partial_success(async_db: AsyncSession, async_test_user: User):
    """Test bulk update with mix of valid and invalid IDs"""
    # Create one job
    job = Job(
        user_id=async_test_user.id,
        company="Test Corp",
        title="Developer",
        tech_stack=["Python"]
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)
    
    service = BulkOperationsService(async_db)
    
    updates = [
        (job.id, JobUpdate(status="applied")),
        (99999, JobUpdate(status="applied")),  # Invalid ID
        (88888, JobUpdate(status="applied"))   # Invalid ID
    ]
    
    result = await service.bulk_update_jobs(updates, async_test_user.id)
    
    assert result.total == 3
    assert result.successful == 1
    assert result.failed == 2
    assert len(result.updated_ids) == 1
    assert len(result.errors) == 2


@pytest.mark.asyncio
async def test_bulk_operations_large_batch(async_db: AsyncSession, async_test_user: User):
    """Test bulk operations with large batch (100 items)"""
    service = BulkOperationsService(async_db)
    
    # Create 100 jobs
    jobs_data = [
        JobCreate(
            company=f"Company {i}",
            title=f"Position {i}",
            tech_stack=["Python"]
        )
        for i in range(100)
    ]
    
    result = await service.bulk_create_jobs(jobs_data, async_test_user.id)
    
    assert result.total == 100
    assert result.successful == 100
    assert result.failed == 0
    assert len(result.created_ids) == 100
    
    # Verify all jobs were created
    stmt = select(Job).where(Job.user_id == async_test_user.id)
    db_result = await async_db.execute(stmt)
    jobs = db_result.scalars().all()
    
    assert len(jobs) == 100
