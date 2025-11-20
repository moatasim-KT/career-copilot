"""
Job seeder
"""
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.user import User
from app.models.job import Job
from datetime import datetime, timezone, timedelta

logger = get_logger(__name__)

def seed_jobs(db: Session, user: User) -> list[Job]:
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
            "status": "not_applied",
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
            "status": "not_applied",
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
            "date_applied": datetime.now(timezone.utc) - timedelta(days=5),
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
            "status": "not_applied",
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
            "status": "not_applied",
        },
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
