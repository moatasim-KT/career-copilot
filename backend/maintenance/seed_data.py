import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data(db: Session) -> None:
    """
    Seed the database with sample data for development and testing.
    - Creates a test user.
    - Creates sample jobs.
    - Creates sample applications.
    """
    logger.info("Seeding database with sample data...")

    try:
        # Create a test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
                skills=["Python", "FastAPI", "SQL"],
                preferred_locations=["Remote", "New York"],
                experience_level="senior"
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
                "company": "Tech Corp",
                "title": "Senior Python Developer",
                "location": "Remote",
                "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "responsibilities": "Lead backend development for enterprise applications.",
                "link": "https://example.com/job1",
                "source": "linkedin",
                "status": "not_applied"
            },
            {
                "company": "Data Solutions",
                "title": "Data Engineer",
                "location": "New York",
                "tech_stack": ["Python", "Spark", "Kafka", "Airflow"],
                "responsibilities": "Build and maintain data pipelines.",
                "link": "https://example.com/job2",
                "source": "indeed",
                "status": "applied",
                "date_applied": datetime.utcnow() - timedelta(days=5)
            },
            {
                "company": "Web Agency",
                "title": "Frontend Developer",
                "location": "San Francisco",
                "tech_stack": ["JavaScript", "React", "TypeScript", "CSS"],
                "responsibilities": "Develop user-facing features.",
                "link": "https://example.com/job3",
                "source": "manual",
                "status": "interview"
            }
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
            if job.status != "not_applied":
                existing_app = db.query(Application).filter(
                    Application.user_id == test_user.id,
                    Application.job_id == job.id
                ).first()
                if not existing_app:
                    application = Application(
                        user_id=test_user.id,
                        job_id=job.id,
                        status=job.status,
                        applied_date=job.date_applied.date() if job.date_applied else datetime.utcnow().date(),
                        notes=f"Submitted via {job.source} on {job.date_applied.strftime('%Y-%m-%d') if job.date_applied else 'N/A'}",
                        interview_date=datetime.utcnow() + timedelta(days=7) if job.title == "Data Scientist" else None,
                        offer_date=datetime.utcnow() + timedelta(days=14) if job.title == "Data Scientist" else None,
                        follow_up_date=datetime.utcnow() + timedelta(days=3) if job.title == "Data Scientist" else None,
                    )
                    db.add(application)
                    db.commit()
                    logger.info(f"Created sample application for job: {job.title}")
                else:
                    logger.info(f"Sample application for job {job.title} already exists.")

        logger.info("Database seeding completed.")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise

if __name__ == "__main__":
    db = SessionLocal()
    seed_data(db)

