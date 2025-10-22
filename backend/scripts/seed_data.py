"""
Database Seeding Script
Creates test user with sample profile, jobs, and applications for development and testing.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.core.logging import get_logger
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

logger = get_logger(__name__)


def clear_existing_data(db: Session):
    """Clear all existing data from tables"""
    logger.info("Clearing existing data...")
    
    try:
        db.query(Application).delete()
        db.query(Job).delete()
        db.query(User).delete()
        db.commit()
        logger.info("✅ Existing data cleared")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error clearing data: {e}")
        raise


def create_test_user(db: Session) -> User:
    """Create a test user with sample profile"""
    logger.info("Creating test user...")
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        skills=["Python", "JavaScript", "React", "FastAPI", "PostgreSQL", "Docker"],
        preferred_locations=["San Francisco, CA", "New York, NY", "Remote"],
        experience_level="mid"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ Created user: {user.username} (ID: {user.id})")
    return user


def create_sample_jobs(db: Session, user: User) -> list[Job]:
    """Create sample jobs with tech_stack"""
    logger.info("Creating sample jobs...")
    
    jobs_data = [
        {
            "company": "TechCorp",
            "title": "Senior Python Developer",
            "location": "San Francisco, CA",
            "description": "We're looking for an experienced Python developer to join our backend team.",
            "requirements": "5+ years Python experience, FastAPI, PostgreSQL, Docker",
            "salary_range": "$120,000 - $160,000",
            "job_type": "full-time",
            "remote_option": "hybrid",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            "responsibilities": "Design and implement backend services, mentor junior developers, optimize database queries",
            "link": "https://example.com/jobs/1",
            "source": "manual",
            "status": "not_applied"
        },
        {
            "company": "StartupXYZ",
            "title": "Full Stack Engineer",
            "location": "Remote",
            "description": "Join our fast-growing startup as a full stack engineer.",
            "requirements": "3+ years experience with React and Node.js",
            "salary_range": "$100,000 - $140,000",
            "job_type": "full-time",
            "remote_option": "remote",
            "tech_stack": ["JavaScript", "React", "Node.js", "MongoDB", "TypeScript"],
            "responsibilities": "Build features end-to-end, collaborate with design team, participate in code reviews",
            "link": "https://example.com/jobs/2",
            "source": "scraped",
            "status": "not_applied"
        },
        {
            "company": "DataCo",
            "title": "Backend Engineer",
            "location": "New York, NY",
            "description": "Work on our data processing pipeline and APIs.",
            "requirements": "Strong Python skills, experience with data processing",
            "salary_range": "$110,000 - $150,000",
            "job_type": "full-time",
            "remote_option": "onsite",
            "tech_stack": ["Python", "Django", "PostgreSQL", "Redis", "Celery"],
            "responsibilities": "Develop data processing pipelines, optimize API performance, maintain database schemas",
            "link": "https://example.com/jobs/3",
            "source": "manual",
            "status": "applied",
            "date_applied": datetime.now(timezone.utc) - timedelta(days=5)
        },
        {
            "company": "CloudSystems",
            "title": "DevOps Engineer",
            "location": "Remote",
            "description": "Help us build and maintain our cloud infrastructure.",
            "requirements": "Experience with AWS, Docker, Kubernetes",
            "salary_range": "$130,000 - $170,000",
            "job_type": "full-time",
            "remote_option": "remote",
            "tech_stack": ["AWS", "Docker", "Kubernetes", "Terraform", "Python"],
            "responsibilities": "Manage cloud infrastructure, implement CI/CD pipelines, monitor system performance",
            "link": "https://example.com/jobs/4",
            "source": "scraped",
            "status": "not_applied"
        },
        {
            "company": "FinTech Inc",
            "title": "Software Engineer",
            "location": "San Francisco, CA",
            "description": "Build financial technology solutions.",
            "requirements": "Strong programming skills, experience with financial systems",
            "salary_range": "$140,000 - $180,000",
            "job_type": "full-time",
            "remote_option": "hybrid",
            "tech_stack": ["Python", "Java", "PostgreSQL", "Kafka", "Microservices"],
            "responsibilities": "Develop financial APIs, ensure system security, collaborate with product team",
            "link": "https://example.com/jobs/5",
            "source": "manual",
            "status": "not_applied"
        }
    ]
    
    jobs = []
    for job_data in jobs_data:
        job = Job(user_id=user.id, **job_data)
        db.add(job)
        jobs.append(job)
    
    db.commit()
    
    for job in jobs:
        db.refresh(job)
    
    logger.info(f"✅ Created {len(jobs)} sample jobs")
    return jobs


def create_sample_applications(db: Session, user: User, jobs: list[Job]) -> list[Application]:
    """Create sample applications"""
    logger.info("Creating sample applications...")
    
    # Create applications for some jobs
    applications_data = [
        {
            "job_id": jobs[2].id,  # DataCo - Backend Engineer
            "status": "applied",
            "applied_date": (datetime.now(timezone.utc) - timedelta(days=5)).date(),
            "notes": "Applied through company website. Waiting for response."
        },
        {
            "job_id": jobs[0].id,  # TechCorp - Senior Python Developer
            "status": "interview",
            "applied_date": (datetime.now(timezone.utc) - timedelta(days=10)).date(),
            "interview_date": datetime.now(timezone.utc) + timedelta(days=2),
            "notes": "Phone screen scheduled for next week. Prepare system design questions."
        },
        {
            "job_id": jobs[1].id,  # StartupXYZ - Full Stack Engineer
            "status": "interested",
            "notes": "Looks like a great opportunity. Need to update resume before applying."
        }
    ]
    
    applications = []
    for app_data in applications_data:
        application = Application(user_id=user.id, **app_data)
        db.add(application)
        applications.append(application)
    
    db.commit()
    
    for app in applications:
        db.refresh(app)
    
    logger.info(f"✅ Created {len(applications)} sample applications")
    return applications


def display_seed_summary(user: User, jobs: list[Job], applications: list[Application]):
    """Display summary of seeded data"""
    logger.info("\n" + "="*60)
    logger.info("SEED DATA SUMMARY")
    logger.info("="*60)
    logger.info(f"\nTest User:")
    logger.info(f"  Username: {user.username}")
    logger.info(f"  Email: {user.email}")
    logger.info(f"  Password: password123")
    logger.info(f"  Skills: {', '.join(user.skills)}")
    logger.info(f"  Locations: {', '.join(user.preferred_locations)}")
    logger.info(f"  Experience: {user.experience_level}")
    
    logger.info(f"\nJobs Created: {len(jobs)}")
    for job in jobs:
        logger.info(f"  - {job.title} at {job.company} ({job.status})")
    
    logger.info(f"\nApplications Created: {len(applications)}")
    for app in applications:
        job = next(j for j in jobs if j.id == app.job_id)
        logger.info(f"  - {job.title} at {job.company} - Status: {app.status}")
    
    logger.info("\n" + "="*60)


def main():
    """Main seeding function"""
    logger.info("="*60)
    logger.info("DATABASE SEEDING SCRIPT")
    logger.info("="*60)
    
    db = SessionLocal()
    
    try:
        # Ask for confirmation
        response = input("\n⚠️  This will clear existing data and create test data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Seeding cancelled")
            return
        
        # Clear existing data
        clear_existing_data(db)
        
        # Create test data
        user = create_test_user(db)
        jobs = create_sample_jobs(db, user)
        applications = create_sample_applications(db, user, jobs)
        
        # Display summary
        display_seed_summary(user, jobs, applications)
        
        logger.info("\n✅ DATABASE SEEDING COMPLETE")
        logger.info("="*60)
        logger.info("\nYou can now login with:")
        logger.info("  Username: testuser")
        logger.info("  Password: password123")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
