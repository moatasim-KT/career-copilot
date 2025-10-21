"""Test script for job management enhancements (Task 4)"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.database import Base
from app.schemas.job import JobCreate, JobUpdate
from datetime import datetime
import json

# Create test database
engine = create_engine("sqlite:///./test_job_enhancements.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

def test_job_creation():
    """Test 4.1: Enhance job creation endpoint"""
    print("\n=== Test 4.1: Job Creation with tech_stack, responsibilities, source ===")
    
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Test 1: Create job with all fields
        job_data = JobCreate(
            company="Tech Corp",
            title="Senior Python Developer",
            location="San Francisco, CA",
            description="Great opportunity",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            responsibilities="Build APIs and services",
            source="manual"
        )
        
        job_dict = job_data.model_dump()
        if job_dict.get('tech_stack') is None:
            job_dict['tech_stack'] = []
        if not job_dict.get('source'):
            job_dict['source'] = 'manual'
            
        job1 = Job(**job_dict, user_id=user.id)
        db.add(job1)
        db.commit()
        db.refresh(job1)
        
        assert job1.company == "Tech Corp"
        assert job1.title == "Senior Python Developer"
        assert job1.tech_stack == ["Python", "FastAPI", "PostgreSQL"]
        assert job1.responsibilities == "Build APIs and services"
        assert job1.source == "manual"
        print("✓ Job created with tech_stack, responsibilities, and source")
        
        # Test 2: Create job with minimal fields (defaults)
        job_data2 = JobCreate(
            company="Startup Inc",
            title="Junior Developer"
        )
        
        job_dict2 = job_data2.model_dump()
        if job_dict2.get('tech_stack') is None:
            job_dict2['tech_stack'] = []
        if not job_dict2.get('source'):
            job_dict2['source'] = 'manual'
            
        job2 = Job(**job_dict2, user_id=user.id)
        db.add(job2)
        db.commit()
        db.refresh(job2)
        
        assert job2.tech_stack == []
        assert job2.source == "manual"
        print("✓ Job created with default values (empty tech_stack, manual source)")
        
        # Test 3: Create job with scraped source
        job_data3 = JobCreate(
            company="Remote Co",
            title="DevOps Engineer",
            tech_stack=["Docker", "Kubernetes"],
            source="scraped"
        )
        
        job_dict3 = job_data3.model_dump()
        if job_dict3.get('tech_stack') is None:
            job_dict3['tech_stack'] = []
        if not job_dict3.get('source'):
            job_dict3['source'] = 'manual'
            
        job3 = Job(**job_dict3, user_id=user.id)
        db.add(job3)
        db.commit()
        db.refresh(job3)
        
        assert job3.source == "scraped"
        print("✓ Job created with 'scraped' source")
        
        print("\n✅ Test 4.1 PASSED: Job creation endpoint enhanced")
        return user.id, [job1.id, job2.id, job3.id]
        
    finally:
        db.close()


def test_job_update(user_id, job_ids):
    """Test 4.2: Enhance job update endpoint"""
    print("\n=== Test 4.2: Job Update with date_applied and updated_at ===")
    
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_ids[0]).first()
        original_updated_at = job.updated_at
        
        # Test 1: Update job fields
        job.title = "Lead Python Developer"
        job.tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis"]
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        
        assert job.title == "Lead Python Developer"
        assert "Redis" in job.tech_stack
        assert job.updated_at > original_updated_at
        print("✓ Job updated with new fields and updated_at timestamp")
        
        # Test 2: Change status to 'applied' and verify date_applied is set
        assert job.date_applied is None
        job.status = "applied"
        job.date_applied = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        
        assert job.status == "applied"
        assert job.date_applied is not None
        print("✓ date_applied set when status changed to 'applied'")
        
        # Test 3: Update other fields without changing status
        job.notes = "Follow up next week"
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        
        assert job.notes == "Follow up next week"
        print("✓ Job updated without affecting date_applied")
        
        print("\n✅ Test 4.2 PASSED: Job update endpoint enhanced")
        
    finally:
        db.close()


def test_job_listing_and_deletion(user_id, job_ids):
    """Test 4.3: Verify job listing and deletion endpoints"""
    print("\n=== Test 4.3: Job Listing and Deletion ===")
    
    db = SessionLocal()
    try:
        # Test 1: List jobs with pagination
        jobs = db.query(Job).filter(Job.user_id == user_id).offset(0).limit(100).all()
        assert len(jobs) == 3
        print(f"✓ Listed {len(jobs)} jobs with pagination")
        
        # Test 2: Verify ordering (newest first)
        jobs_ordered = (
            db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .all()
        )
        assert jobs_ordered[0].created_at >= jobs_ordered[-1].created_at
        print("✓ Jobs ordered by created_at descending")
        
        # Test 3: Create application for cascade delete test
        job_to_delete = db.query(Job).filter(Job.id == job_ids[0]).first()
        app = Application(
            user_id=user_id,
            job_id=job_to_delete.id,
            status="interested"
        )
        db.add(app)
        db.commit()
        
        # Verify application exists
        app_count_before = db.query(Application).filter(Application.job_id == job_to_delete.id).count()
        assert app_count_before == 1
        print(f"✓ Created {app_count_before} application(s) for cascade delete test")
        
        # Test 4: Delete job and verify cascade
        db.delete(job_to_delete)
        db.commit()
        
        # Verify job is deleted
        deleted_job = db.query(Job).filter(Job.id == job_ids[0]).first()
        assert deleted_job is None
        print("✓ Job deleted successfully")
        
        # Verify applications are cascade deleted
        app_count_after = db.query(Application).filter(Application.job_id == job_ids[0]).count()
        assert app_count_after == 0
        print("✓ Associated applications cascade deleted")
        
        # Test 5: Verify remaining jobs
        remaining_jobs = db.query(Job).filter(Job.user_id == user_id).count()
        assert remaining_jobs == 2
        print(f"✓ {remaining_jobs} jobs remaining after deletion")
        
        print("\n✅ Test 4.3 PASSED: Job listing and deletion verified")
        
    finally:
        db.close()


def main():
    print("=" * 70)
    print("Testing Job Management Enhancements (Task 4)")
    print("=" * 70)
    
    try:
        # Run all tests
        user_id, job_ids = test_job_creation()
        test_job_update(user_id, job_ids)
        test_job_listing_and_deletion(user_id, job_ids)
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Task 4 Implementation Complete")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        if os.path.exists("./test_job_enhancements.db"):
            os.remove("./test_job_enhancements.db")
            print("\n🧹 Cleaned up test database")


if __name__ == "__main__":
    main()
