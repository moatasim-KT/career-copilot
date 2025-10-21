from sqlalchemy.orm import Session
from app.models.job import Job
from app.schemas.job import JobCreate

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_data: JobCreate, user_id: int) -> Job:
        job = Job(**job_data.model_dump(), user_id=user_id)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
