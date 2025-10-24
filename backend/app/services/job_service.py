from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.job import Job
from app.schemas.job import JobCreate
from typing import Optional, List

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, user_id: int, job_data: JobCreate) -> Job:
        job = Job(**job_data.model_dump(), user_id=user_id)
        self.db.add(job)
        self.db.flush() # Use flush to get ID before commit if needed elsewhere
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_job_by_unique_fields(
        self, user_id: int, title: str, company: str, location: Optional[str]
    ) -> Optional[Job]:
        query = self.db.query(Job).filter(
            Job.user_id == user_id,
            Job.title == title,
            Job.company == company,
        )
        if location:
            query = query.filter(Job.location == location)
        return query.first()

    def get_latest_jobs_for_user(self, user_id: int, limit: int = 10) -> List[Job]:
        return (
            self.db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(desc(Job.created_at))
            .limit(limit)
            .all()
        )
