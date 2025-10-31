"""
Application seeder
"""
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from datetime import datetime, timezone, timedelta

logger = get_logger(__name__)

def seed_applications(db: Session, user: User, jobs: list[Job]) -> list[Application]:
    """Create sample applications"""
    logger.info("Creating sample applications...")

    # Create applications for some jobs
    applications_data = [
        {
            "job_id": jobs[2].id,  # DataCo - Backend Engineer
            "status": "applied",
            "applied_date": (datetime.now(timezone.utc) - timedelta(days=5)).date(),
            "notes": "Applied through company website. Waiting for response.",
        },
        {
            "job_id": jobs[0].id,  # TechCorp - Senior Python Developer
            "status": "interview",
            "applied_date": (datetime.now(timezone.utc) - timedelta(days=10)).date(),
            "interview_date": datetime.now(timezone.utc) + timedelta(days=2),
            "notes": "Phone screen scheduled for next week. Prepare system design questions.",
        },
        {
            "job_id": jobs[1].id,  # StartupXYZ - Full Stack Engineer
            "status": "interested",
            "notes": "Looks like a great opportunity. Need to update resume before applying.",
        },
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
