import os
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.security import get_password_hash
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

def create_initial_data(db: Session):
    logger.info("Creating initial data...")

    # Create a test user
    test_user = db.query(User).filter(User.email == "test@example.com").first()
    if not test_user:
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            skills=["Python", "FastAPI", "SQLAlchemy", "Docker", "AWS"],
            preferred_locations=["Remote", "New York"],
            experience_level="mid",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        logger.info(f"Created test user: {test_user.username}")
    else:
        logger.info(f"Test user {test_user.username} already exists.")

    # Create sample jobs
    sample_jobs_data = [
        {
            "company": "Tech Solutions Inc.",
            "title": "Senior Python Developer",
            "location": "New York, NY",
            "tech_stack": ["Python", "Django", "PostgreSQL", "AWS"],
            "responsibilities": "Lead backend development for enterprise applications.",
            "link": "https://example.com/job1",
            "source": "LinkedIn",
            "status": "not_applied",
            "documents_required": ["resume", "cover_letter"]
        },
        {
            "company": "Innovate Corp.",
            "title": "Mid-level FastAPI Engineer",
            "location": "Remote",
            "tech_stack": ["Python", "FastAPI", "MongoDB", "Docker"],
            "responsibilities": "Develop and maintain high-performance APIs.",
            "link": "https://example.com/job2",
            "source": "Indeed",
            "status": "not_applied",
            "documents_required": ["resume"]
        },
        {
            "company": "Data Insights LLC",
            "title": "Data Scientist",
            "location": "San Francisco, CA",
            "tech_stack": ["Python", "Pandas", "Scikit-learn", "SQL"],
            "responsibilities": "Analyze large datasets and build predictive models.",
            "link": "https://example.com/job3",
            "source": "Glassdoor",
            "status": "applied",
            "date_applied": datetime.utcnow() - timedelta(days=5),
            "documents_required": ["resume", "portfolio"]
        },
    ]

    for job_data in sample_jobs_data:
        existing_job = db.query(Job).filter(
            Job.user_id == test_user.id,
            Job.company == job_data["company"],
            Job.title == job_data["title"]
        ).first()
        if not existing_job:
            job = Job(**job_data, user_id=test_user.id)
            db.add(job)
            db.commit()
            db.refresh(job)
            logger.info(f"Created sample job: {job.title} at {job.company}")
        else:
            logger.info(f"Sample job {existing_job.title} at {existing_job.company} already exists.")

    # Create sample applications
    sample_jobs = db.query(Job).filter(Job.user_id == test_user.id).all()
    for job in sample_jobs:
        if job.status == "applied":
            existing_app = db.query(Application).filter(
                Application.user_id == test_user.id,
                Application.job_id == job.id
            ).first()
            if not existing_app:
                application = Application(
                    user_id=test_user.id,
                    job_id=job.id,
                    status="applied",
                    applied_date=job.date_applied.date() if job.date_applied else datetime.utcnow().date(),
                    notes=f"Submitted via {job.source} on {job.date_applied.strftime('%Y-%m-%d') if job.date_applied else 'N/A'}",
                    interview_date=datetime.utcnow() + timedelta(days=7) if job.title == "Data Scientist" else None,
                    offer_date=datetime.utcnow() + timedelta(days=14) if job.title == "Data Scientist" else None,
                    follow_up_date=datetime.utcnow() + timedelta(days=3) if job.title == "Data Scientist" else None,
                )
                db.add(application)
                db.commit()
                db.refresh(application)
                logger.info(f"Created sample application for job: {job.title}")
            else:
                logger.info(f"Sample application for job {job.title} already exists.")

    logger.info("Initial data creation complete.")

if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        create_initial_data(db)
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
    finally:
        db.close()