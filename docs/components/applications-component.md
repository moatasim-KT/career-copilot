# Applications Component Reference

## Overview

The Applications component manages job application tracking, status management, and timeline progression. It provides comprehensive CRUD operations, advanced search/filtering, and analytics integration for career management.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer   │    │  Data Layer     │
│                 │    │                  │    │                 │
│ • applications.py│◄──►│ • application_   │◄──►│ • application.py│
│ • bulk_ops.py    │    │   service.py     │    │ • job.py        │
│ • search.py      │    │ • bulk_ops_      │    │ • user.py       │
│                 │    │   service.py      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              ▲
                              │
                       ┌─────────────────┐
                       │   Status Flow   │
                       │                 │
                       │ interested → applied → interview → offer → accepted
                       │     ↓         ↓         ↓         ↓         ↓
                       │   rejected  declined  rejected  rejected  declined
                       └─────────────────┘
```

## Core Files

### API Layer
- **Applications API**: [[../../backend/app/api/v1/applications.py|applications.py]] - Main application management endpoints
- **Bulk Operations**: [[../../backend/app/api/v1/bulk_operations.py|bulk_operations.py]] - Bulk application operations
- **Search API**: [[../../backend/app/api/v1/applications.py#search_applications|search_applications()]] - Advanced search functionality

### Service Layer
- **Application Service**: [[../../backend/app/services/application_service.py|application_service.py]] - Core application business logic
- **Bulk Operations Service**: [[../../backend/app/services/bulk_operations_service.py|bulk_operations_service.py]] - Bulk operation handling

### Data Layer
- **Application Model**: [[../../backend/app/models/application.py|application.py]] - Application database model
- **Job Model**: [[../../backend/app/models/job.py|job.py]] - Related job data
- **User Model**: [[../../backend/app/models/user.py|user.py]] - User ownership

## Database Schema

### Applications Table
```sql
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    status VARCHAR DEFAULT 'interested',  -- Status progression tracking
    applied_date DATE DEFAULT CURRENT_DATE,
    response_date DATE NULL,              -- When company responded
    interview_date TIMESTAMP NULL,        -- Interview scheduling
    offer_date DATE NULL,                 -- Offer received date
    notes TEXT NULL,                      -- User notes and feedback
    interview_feedback JSONB NULL,        -- Structured interview feedback
    follow_up_date DATE NULL,             -- Follow-up reminders
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for performance
    INDEX idx_applications_user_id (user_id),
    INDEX idx_applications_job_id (job_id),
    INDEX idx_applications_status (status),
    INDEX idx_applications_created_at (created_at),
    INDEX idx_applications_applied_date (applied_date),

    -- Constraints
    CHECK (status IN ('interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined'))
);
```

### Status Flow
```python
# From application.py
APPLICATION_STATUSES = [
    "interested",  # Initial interest in job
    "applied",     # Application submitted
    "interview",   # Interview scheduled/completed
    "offer",       # Job offer received
    "rejected",    # Application rejected
    "accepted",    # Offer accepted
    "declined"     # Offer declined
]
```

## Key Services

### Application Service
```python
# From application_service.py
class ApplicationService:
    def __init__(self, db: Session):
        self.db = db

    def get_application(self, application_id: int, user_id: int) -> Optional[Application]:
        """Get application with user ownership validation"""
        return self.db.query(Application).filter(
            and_(Application.id == application_id, Application.user_id == user_id)
        ).first()

    def get_application_documents(self, application_id: int, user_id: int) -> List[DocumentAssociation]:
        """Get documents associated with application"""
        application = self.get_application(application_id, user_id)
        if not application:
            return []

        return [
            DocumentAssociation(**doc_data)
            for doc_data in application.documents
        ]
```

### Bulk Operations Service
```python
# From bulk_operations_service.py
class BulkOperationsService:
    def __init__(self, db: Session):
        self.db = db

    async def bulk_update_status(self, application_ids: List[int], new_status: str, user_id: int) -> dict:
        """Update status for multiple applications"""
        # Validate status transition
        if new_status not in APPLICATION_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        # Update applications
        updated = await self.db.execute(
            update(Application)
            .where(
                and_(
                    Application.id.in_(application_ids),
                    Application.user_id == user_id
                )
            )
            .values(status=new_status, updated_at=datetime.utcnow())
        )

        await self.db.commit()
        return {"updated_count": updated.rowcount}
```

## API Endpoints

| Method | Endpoint | Description | Implementation |
|--------|----------|-------------|----------------|
| GET | `/api/v1/applications` | List user applications | [[../../backend/app/api/v1/applications.py#get_applications\|get_applications()]] |
| POST | `/api/v1/applications` | Create new application | [[../../backend/app/api/v1/applications.py#create_application\|create_application()]] |
| GET | `/api/v1/applications/{id}` | Get specific application | [[../../backend/app/api/v1/applications.py#get_application\|get_application()]] |
| PUT | `/api/v1/applications/{id}` | Update application | [[../../backend/app/api/v1/applications.py#update_application\|update_application()]] |
| DELETE | `/api/v1/applications/{id}` | Delete application | [[../../backend/app/api/v1/applications.py#delete_application\|delete_application()]] |
| GET | `/api/v1/applications/search` | Advanced search | [[../../backend/app/api/v1/applications.py#search_applications\|search_applications()]] |
| GET | `/api/v1/applications/summary` | Applications summary | [[../../backend/app/api/v1/applications.py#get_applications_summary\|get_applications_summary()]] |
| GET | `/api/v1/applications/stats` | Detailed statistics | [[../../backend/app/api/v1/applications.py#get_applications_stats\|get_applications_stats()]] |

## Application Lifecycle

### Status Progression
```python
# Typical application flow
{
    "interested": "User shows interest in job posting",
    "applied": "Application submitted to company",
    "interview": "Interview process initiated",
    "offer": "Job offer received",
    "accepted": "Offer accepted - job secured",
    "rejected": "Application rejected at any stage",
    "declined": "Offer received but declined"
}
```

### Timeline Tracking
```python
# Key dates tracked
class ApplicationTimeline:
    applied_date: date      # When application was submitted
    response_date: date     # When company responded
    interview_date: datetime # Interview scheduling
    offer_date: date        # Offer received
    follow_up_date: date    # Reminder for follow-up
    created_at: datetime    # Record creation
    updated_at: datetime    # Last modification
```

### Response Time Analysis
```python
# Calculate response times for analytics
def calculate_response_metrics(applications: List[Application]) -> dict:
    response_times = []
    for app in applications:
        if app.response_date and app.applied_date:
            days = (app.response_date - app.applied_date).days
            response_times.append(days)

    if response_times:
        return {
            "average_response_days": sum(response_times) / len(response_times),
            "min_response_days": min(response_times),
            "max_response_days": max(response_times),
            "total_responses": len(response_times)
        }
    return {"average_response_days": 0, "total_responses": 0}
```

## Advanced Search & Filtering

### Search Parameters
```python
# From search_applications endpoint
async def search_applications(
    query: str = "",                    # Text search across job details
    status: str | None = None,          # Filter by status
    start_date: str | None = None,      # Date range filtering
    end_date: str | None = None,
    sort_by: str = "created_at",        # created_at, updated_at, applied_date, status
    sort_order: str = "desc",           # asc, desc
    skip: int = 0,                      # Pagination
    limit: int = 100,
    use_cache: bool = True,             # Caching enabled
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
```

### Search Implementation
```python
# Advanced search with multiple filters
def build_search_query(db: AsyncSession, user_id: int, filters: dict) -> Select:
    query = select(Application).where(Application.user_id == user_id)

    # Text search across job relationships
    if filters.get("query"):
        search_term = f"%{filters['query']}%"
        query = query.join(Job).where(
            or_(
                Job.title.ilike(search_term),
                Job.company.ilike(search_term),
                Job.description.ilike(search_term),
                Application.notes.ilike(search_term)
            )
        )

    # Status filtering
    if filters.get("status"):
        query = query.where(Application.status == filters["status"])

    # Date range filtering
    if filters.get("start_date"):
        start = datetime.fromisoformat(filters["start_date"])
        query = query.where(Application.created_at >= start)

    if filters.get("end_date"):
        end = datetime.fromisoformat(filters["end_date"])
        query = query.where(Application.created_at <= end)

    # Sorting
    sort_column = getattr(Application, filters.get("sort_by", "created_at"))
    if filters.get("sort_order") == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    return query
```

## Bulk Operations

### Bulk Status Updates
```python
# Bulk update application statuses
@router.post("/api/v1/applications/bulk/status")
async def bulk_update_status(
    request: BulkStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = BulkOperationsService(db)
    result = await service.bulk_update_status(
        application_ids=request.application_ids,
        new_status=request.new_status,
        user_id=current_user.id
    )
    return result
```

### Bulk Deletion
```python
# Bulk delete applications
@router.delete("/api/v1/applications/bulk")
async def bulk_delete_applications(
    application_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate ownership
    applications = await db.execute(
        select(Application).where(
            and_(
                Application.id.in_(application_ids),
                Application.user_id == current_user.id
            )
        )
    )

    # Delete applications
    for app in applications.scalars():
        await db.delete(app)

    await db.commit()
    return {"deleted_count": len(application_ids)}
```

## Analytics Integration

### Application Metrics
```python
# Integration with analytics service
async def track_application_event(application: Application, event_type: str):
    analytics_data = {
        "application_id": application.id,
        "job_id": application.job_id,
        "previous_status": application.status,
        "event_type": event_type,
        "timestamp": datetime.now(UTC).isoformat()
    }

    await analytics_service.collect_event(
        event_type=f"application_{event_type}",
        data=analytics_data,
        user_id=application.user_id
    )
```

### Success Rate Calculations
```python
# Calculate application success metrics
def calculate_success_rates(applications: List[Application]) -> dict:
    total = len(applications)
    if total == 0:
        return {"success_rate": 0, "interview_rate": 0, "offer_rate": 0}

    interviewed = sum(1 for app in applications if app.status in ["interview", "offer", "accepted"])
    offers = sum(1 for app in applications if app.status in ["offer", "accepted"])
    accepted = sum(1 for app in applications if app.status == "accepted")

    return {
        "application_to_interview_rate": (interviewed / total) * 100,
        "interview_to_offer_rate": (offers / interviewed) * 100 if interviewed > 0 else 0,
        "offer_to_acceptance_rate": (accepted / offers) * 100 if offers > 0 else 0,
        "overall_success_rate": (accepted / total) * 100
    }
```

## Document Management

### Application Documents
```python
# Document association with applications
class ApplicationDocument:
    document_id: int
    document_type: str  # 'resume', 'cover_letter', 'portfolio'
    filename: str
    uploaded_at: datetime

# Store documents as JSON in application record
application.documents = [
    {
        "document_id": 123,
        "type": "resume",
        "filename": "john_doe_resume.pdf",
        "uploaded_at": "2024-01-15T10:30:00Z"
    }
]
```

### Document Operations
```python
# Add document to application
async def add_document_to_application(
    application_id: int,
    document_id: int,
    document_type: str,
    user_id: int
):
    application = await get_application(application_id, user_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Add to documents array
    doc_entry = {
        "document_id": document_id,
        "type": document_type,
        "filename": f"document_{document_id}",
        "uploaded_at": datetime.now(UTC).isoformat()
    }

    if not application.documents:
        application.documents = []
    application.documents.append(doc_entry)

    db.add(application)
    await db.commit()
```

## Interview Tracking

### Interview Feedback Structure
```python
# Structured interview feedback
interview_feedback = {
    "interview_type": "technical" | "behavioral" | "system_design" | "final",
    "interviewer_names": ["John Smith", "Jane Doe"],
    "rating": 4,  # 1-5 scale
    "technical_skills": {
        "python": 4,
        "algorithms": 3,
        "system_design": 4
    },
    "feedback": {
        "strengths": ["Good problem solving", "Clean code"],
        "weaknesses": ["Could improve communication"],
        "recommendations": ["Practice more system design questions"]
    },
    "next_steps": "Second interview scheduled for next week",
    "overall_assessment": "Strong candidate, recommend proceeding"
}
```

### Interview Scheduling
```python
# Interview date and time tracking
class InterviewSchedule:
    interview_date: datetime    # Exact date and time
    interview_type: str         # phone, video, onsite
    interviewer: str           # Interviewer name/contact
    location: str              # For onsite interviews
    preparation_notes: str     # What to prepare
    follow_up_required: bool   # Need to follow up
```

## Follow-up Management

### Automated Reminders
```python
# Follow-up date tracking
async def schedule_follow_up(application: Application, days_delay: int = 7):
    """Schedule follow-up reminder"""
    follow_up_date = datetime.now() + timedelta(days=days_delay)
    application.follow_up_date = follow_up_date.date()

    # Create notification
    await notification_service.create_notification(
        user_id=application.user_id,
        type="follow_up_reminder",
        title=f"Follow up on {application.job.title} application",
        message=f"Don't forget to follow up on your application to {application.job.company}",
        scheduled_date=follow_up_date
    )
```

### Follow-up Status Tracking
```python
# Track follow-up attempts
follow_up_history = [
    {
        "date": "2024-01-20",
        "method": "email",
        "contact": "recruiter@company.com",
        "notes": "Sent polite follow-up email",
        "response_received": False
    },
    {
        "date": "2024-01-27",
        "method": "phone",
        "contact": "555-0123",
        "notes": "Spoke with HR, they said decision in 2 weeks",
        "response_received": True
    }
]
```

## Configuration

### Status Configuration
```python
# Application status configuration
APPLICATION_STATUS_CONFIG = {
    "interested": {
        "color": "#6B7280",  # Gray
        "description": "Showing interest in job",
        "next_statuses": ["applied", "rejected"]
    },
    "applied": {
        "color": "#3B82F6",  # Blue
        "description": "Application submitted",
        "next_statuses": ["interview", "rejected"],
        "auto_follow_up_days": 7
    },
    "interview": {
        "color": "#F59E0B",  # Yellow
        "description": "Interview process",
        "next_statuses": ["offer", "rejected"],
        "requires_interview_date": True
    },
    "offer": {
        "color": "#10B981",  # Green
        "description": "Job offer received",
        "next_statuses": ["accepted", "declined"],
        "requires_offer_date": True
    },
    "accepted": {
        "color": "#059669",  # Dark green
        "description": "Offer accepted",
        "next_statuses": [],
        "terminal": True
    },
    "rejected": {
        "color": "#EF4444",  # Red
        "description": "Application rejected",
        "next_statuses": [],
        "terminal": True
    },
    "declined": {
        "color": "#7C3AED",  # Purple
        "description": "Offer declined",
        "next_statuses": [],
        "terminal": True
    }
}
```

## Testing

### Unit Tests
```python
# Test application service
def test_get_application(db: Session):
    service = ApplicationService(db)

    # Create test application
    application = Application(user_id=1, job_id=1, status="applied")
    db.add(application)
    db.commit()

    # Test retrieval
    retrieved = service.get_application(application.id, 1)
    assert retrieved is not None
    assert retrieved.status == "applied"

    # Test wrong user
    retrieved_wrong_user = service.get_application(application.id, 2)
    assert retrieved_wrong_user is None
```

### Integration Tests
```python
# Test full application lifecycle
async def test_application_lifecycle(db: AsyncSession):
    # Create application
    app_data = ApplicationCreate(job_id=1, status="interested")
    application = Application(**app_data.model_dump(), user_id=1)
    db.add(application)
    await db.commit()

    # Update status progression
    await update_application_status(application.id, "applied", 1)
    await update_application_status(application.id, "interview", 1)
    await update_application_status(application.id, "offer", 1)
    await update_application_status(application.id, "accepted", 1)

    # Verify final state
    final_app = await get_application(application.id, 1)
    assert final_app.status == "accepted"
```

### Status Transition Tests
```python
# Test status validation
def test_status_transitions():
    valid_transitions = {
        "interested": ["applied", "rejected"],
        "applied": ["interview", "rejected"],
        "interview": ["offer", "rejected"],
        "offer": ["accepted", "declined"],
        "accepted": [],
        "rejected": [],
        "declined": []
    }

    for current_status, allowed_next in valid_transitions.items():
        for next_status in APPLICATION_STATUSES:
            if next_status in allowed_next:
                assert is_valid_transition(current_status, next_status)
            else:
                assert not is_valid_transition(current_status, next_status)
```

**Test Files:**
- [[../../backend/tests/test_applications.py|test_applications.py]] - Application CRUD tests
- [[../../backend/tests/test_application_status.py|test_application_status.py]] - Status transition tests
- [[../../backend/tests/test_bulk_operations.py|test_bulk_operations.py]] - Bulk operation tests

## Performance Considerations

### Database Optimization
- **Indexes**: Composite indexes on `(user_id, status)`, `(user_id, created_at)`
- **Partitioning**: Partition by month for large datasets
- **Archiving**: Move old applications to archive tables

### Caching Strategy
- **Application Lists**: Cache for 5 minutes
- **Search Results**: Cache based on query hash
- **Statistics**: Cache aggregated metrics

### Query Optimization
```python
# Optimized queries with selectinload
applications = await db.execute(
    select(Application)
    .options(selectinload(Application.job), selectinload(Application.user))
    .where(Application.user_id == user_id)
    .order_by(desc(Application.created_at))
    .limit(100)
)
```

## Related Components

- **Jobs**: [[jobs-component|Jobs Component]] - Job data source for applications
- **Analytics**: [[analytics-component|Analytics Component]] - Application metrics and reporting
- **Notifications**: [[notifications-component|Notifications Component]] - Follow-up reminders
- **Documents**: [[../../backend/app/services/file_storage_service.py|File Storage Service]] - Document management

## Common Patterns

### Status Update with Validation
```python
async def update_application_status(application_id: int, new_status: str, user_id: int):
    # Validate status transition
    application = await get_application(application_id, user_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check if transition is valid
    if not is_valid_status_transition(application.status, new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {application.status} to {new_status}"
        )

    # Update status and related dates
    application.status = new_status
    application.updated_at = datetime.utcnow()

    # Set related dates based on status
    if new_status == "applied" and not application.applied_date:
        application.applied_date = date.today()
    elif new_status == "interview" and not application.interview_date:
        # Schedule interview (would be set via separate endpoint)
        pass
    elif new_status == "offer" and not application.offer_date:
        application.offer_date = date.today()

    # Track analytics event
    await track_application_event(application, "status_changed")

    db.add(application)
    await db.commit()

    return application
```

### Search with Pagination
```python
async def search_applications_paginated(filters: dict, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page

    query = build_search_query(db, filters["user_id"], filters)
    total_count = await db.execute(
        select(func.count()).select_from(query.subquery())
    )

    applications = await db.execute(
        query.offset(offset).limit(per_page)
    )

    return {
        "applications": applications.scalars().all(),
        "total_count": total_count.scalar(),
        "page": page,
        "per_page": per_page,
        "total_pages": ceil(total_count.scalar() / per_page)
    }
```

### Bulk Operations with Rollback
```python
async def bulk_operation_with_rollback(operations: List[dict]):
    # Start transaction
    async with db.begin():
        try:
            results = []
            for operation in operations:
                result = await perform_operation(operation)
                results.append(result)

            # Commit all at once
            await db.commit()
            return {"success": True, "results": results}

        except Exception as e:
            # Rollback on any failure
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Bulk operation failed: {str(e)}"
            )
```

---

*See also: [[../api/API.md#applications|Applications API Docs]], [[../../backend/app/models/application.py|Application Data Model]], [[../../backend/app/services/bulk_operations_service.py|Bulk Operations Service]]*"