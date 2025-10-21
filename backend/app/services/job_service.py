"""Job application service."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from app.models.job_database_models import JobApplication, Interview, Contact, ApplicationStatus
from app.models.job_models import (
    JobApplicationCreate, JobApplicationUpdate, JobApplicationResponse,
    InterviewCreate, InterviewResponse, ContactCreate, ContactResponse,
    ApplicationStats
)


class JobService:
    """Service for job application operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(self, application: JobApplicationCreate, user_id: Optional[int] = None) -> JobApplication:
        """Create new job application."""
        db_application = JobApplication(
            **application.model_dump(exclude_unset=True),
            user_id=user_id,
            applied_date=datetime.utcnow() if application.status == ApplicationStatus.APPLIED else None
        )
        self.db.add(db_application)
        await self.db.commit()
        await self.db.refresh(db_application)
        return db_application

    async def get_application(self, application_id: int) -> Optional[JobApplication]:
        """Get job application by ID."""
        result = await self.db.execute(
            select(JobApplication).where(JobApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    async def list_applications(
        self, 
        status: Optional[ApplicationStatus] = None,
        company: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobApplication]:
        """List job applications with filters."""
        query = select(JobApplication)
        
        if status:
            query = query.where(JobApplication.status == status)
        if company:
            query = query.where(JobApplication.company.ilike(f"%{company}%"))
        
        query = query.offset(skip).limit(limit).order_by(JobApplication.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_application(
        self, 
        application_id: int, 
        application_update: JobApplicationUpdate
    ) -> Optional[JobApplication]:
        """Update job application."""
        db_application = await self.get_application(application_id)
        if not db_application:
            return None

        update_data = application_update.model_dump(exclude_unset=True)
        
        # Set applied_date when status changes to APPLIED
        if "status" in update_data and update_data["status"] == ApplicationStatus.APPLIED:
            if not db_application.applied_date:
                update_data["applied_date"] = datetime.utcnow()

        for field, value in update_data.items():
            setattr(db_application, field, value)

        await self.db.commit()
        await self.db.refresh(db_application)
        return db_application

    async def delete_application(self, application_id: int) -> bool:
        """Delete job application."""
        db_application = await self.get_application(application_id)
        if not db_application:
            return False

        await self.db.delete(db_application)
        await self.db.commit()
        return True

    async def create_interview(self, interview: InterviewCreate) -> Interview:
        """Create interview."""
        db_interview = Interview(**interview.model_dump())
        self.db.add(db_interview)
        await self.db.commit()
        await self.db.refresh(db_interview)
        return db_interview

    async def list_interviews(self, application_id: int) -> List[Interview]:
        """List interviews for application."""
        result = await self.db.execute(
            select(Interview)
            .where(Interview.application_id == application_id)
            .order_by(Interview.scheduled_at)
        )
        return result.scalars().all()

    async def create_contact(self, contact: ContactCreate) -> Contact:
        """Create contact."""
        db_contact = Contact(**contact.model_dump())
        self.db.add(db_contact)
        await self.db.commit()
        await self.db.refresh(db_contact)
        return db_contact

    async def list_contacts(self, application_id: int) -> List[Contact]:
        """List contacts for application."""
        result = await self.db.execute(
            select(Contact)
            .where(Contact.application_id == application_id)
            .order_by(Contact.created_at)
        )
        return result.scalars().all()

    async def get_statistics(self) -> ApplicationStats:
        """Get application statistics."""
        # Total count
        total_result = await self.db.execute(select(func.count(JobApplication.id)))
        total = total_result.scalar()

        # By status
        status_result = await self.db.execute(
            select(JobApplication.status, func.count(JobApplication.id))
            .group_by(JobApplication.status)
        )
        by_status = {status: count for status, count in status_result.all()}

        # By month
        month_result = await self.db.execute(
            select(
                extract('year', JobApplication.created_at).label('year'),
                extract('month', JobApplication.created_at).label('month'),
                func.count(JobApplication.id)
            )
            .group_by('year', 'month')
            .order_by('year', 'month')
        )
        by_month = {f"{int(year)}-{int(month):02d}": count for year, month, count in month_result.all()}

        # Response rate (applications that moved past applied status)
        responded_result = await self.db.execute(
            select(func.count(JobApplication.id))
            .where(JobApplication.status.notin_([ApplicationStatus.WISHLIST, ApplicationStatus.APPLIED]))
        )
        responded = responded_result.scalar()
        response_rate = (responded / total * 100) if total > 0 else 0

        return ApplicationStats(
            total=total,
            by_status=by_status,
            by_month=by_month,
            response_rate=response_rate
        )


async def get_job_service(db: AsyncSession) -> JobService:
    """Get job service instance."""
    return JobService(db)
