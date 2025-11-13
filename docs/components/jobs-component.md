# Jobs Component Reference

## Overview

The Jobs component handles all job-related functionality including job scraping, storage, search, and management.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer   │    │  Data Layer     │
│                 │    │                  │    │                 │
│ • jobs.py       │◄──►│ • job_service.py │◄──►│ • job.py        │
│ • endpoints/    │    │ • scraping/      │    │ • user.py       │
│                 │    │ • deduplication  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              ▲
                              │
                       ┌─────────────────┐
                       │  Background     │
                       │  Tasks          │
                       │                 │
                       │ • job_ingestion │
                       │ • scraping      │
                       └─────────────────┘
```

## Core Files

### API Layer
- **Main API**: [[../../backend/app/api/v1/jobs.py|jobs.py]] - REST endpoints for job operations
- **Search Endpoint**: [[../../backend/app/api/v1/jobs.py#search_jobs|search_jobs()]] - Advanced job search
- **CRUD Operations**: [[../../backend/app/api/v1/jobs.py#list_jobs|list_jobs()]], [[../../backend/app/api/v1/jobs.py#create_job|create_job()]], etc.

### Service Layer
- **Job Service**: [[../../backend/app/services/job_service.py|job_service.py]] - Business logic for job operations
- **Scraping Services**: [[../../backend/app/services/scraping/|scraping/]] - Job board scrapers
- **Deduplication**: [[../../backend/app/services/job_deduplication_service.py|job_deduplication_service.py]] - Duplicate detection

### Data Layer
- **Job Model**: [[../../backend/app/models/job.py|job.py]] - Database model
- **Schemas**: [[../../backend/app/schemas/job.py|job.py]] - Pydantic schemas
- **Migrations**: [[../../backend/alembic/versions/|alembic/versions/]] - Database schema changes

### Background Tasks
- **Job Ingestion**: [[../../backend/app/tasks/job_ingestion_tasks.py|job_ingestion_tasks.py]] - Scheduled scraping
- **Scraping Tasks**: [[../../backend/app/tasks/scraping_tasks.py|scraping_tasks.py]] - Individual scraper tasks

## Key Functions

### Job Search & Filtering
```python
# From jobs.py
@router.get("/api/v1/jobs/search")
async def search_jobs(
    query: str = "",
    location: str = "",
    tech_stack: List[str] = Query(default=[]),
    # ... other filters
)
```

### Job Creation
```python
# From job_service.py
def create_job(self, db: Session, job_data: JobCreate, user_id: int) -> Job:
    # Business logic for job creation
    pass
```

### Scraping Integration
```python
# From scraping services
class LinkedInScraper:
    def scrape_jobs(self, keywords: str, location: str) -> List[JobData]:
        # Scraping logic
        pass
```

## Database Schema

```sql
-- From job.py model
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    location VARCHAR,
    description TEXT,
    tech_stack JSONB,
    salary_min INTEGER,
    salary_max INTEGER,
    source VARCHAR,
    url VARCHAR UNIQUE,
    scraped_at TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT true
);
```

## API Endpoints

| Method | Endpoint | Description | Implementation |
|--------|----------|-------------|----------------|
| GET | `/api/v1/jobs` | List jobs | [[../../backend/app/api/v1/jobs.py#list_jobs\|list_jobs()]] |
| GET | `/api/v1/jobs/search` | Search jobs | [[../../backend/app/api/v1/jobs.py#search_jobs\|search_jobs()]] |
| GET | `/api/v1/jobs/{id}` | Get job details | [[../../backend/app/api/v1/jobs.py#get_job\|get_job()]] |
| POST | `/api/v1/jobs` | Create job | [[../../backend/app/api/v1/jobs.py#create_job\|create_job()]] |
| PUT | `/api/v1/jobs/{id}` | Update job | [[../../backend/app/api/v1/jobs.py#update_job\|update_job()]] |
| DELETE | `/api/v1/jobs/{id}` | Delete job | [[../../backend/app/api/v1/jobs.py#delete_job\|delete_job()]] |

## Testing

- **Unit Tests**: [[../../backend/tests/test_job_service.py|test_job_service.py]]
- **API Tests**: [[../../backend/tests/test_jobs_api.py|test_jobs_api.py]]
- **Integration Tests**: [[../../backend/tests/test_job_scraping.py|test_job_scraping.py]]

## Related Components

- **Applications**: [[applications-component|Applications Component]] - Job applications tracking
- **Analytics**: [[analytics-component|Analytics Component]] - Job market insights
- **Recommendations**: [[recommendations-component|Recommendations Component]] - Job matching

## Common Patterns

### Service Layer Pattern
```python
# Always use service layer for business logic
@router.post("/jobs")
def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    service = JobService(db)
    return service.create_job(job_data, current_user.id)
```

### Async Database Operations
```python
# Use async for database operations
async def get_jobs(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Job))
    return result.scalars().all()
```

### Caching Strategy
```python
# Cache expensive operations
@cache_service.cached(ttl_seconds=300)
async def search_jobs(query: str, filters: dict):
    # Expensive search logic
    pass
```

## Performance Considerations

- **Database Indexing**: Composite indexes on frequently queried fields
- **Caching**: Redis caching for search results (5-minute TTL)
- **Pagination**: Default 20 items per page, max 100
- **Async Operations**: All database operations use async/await

## Monitoring & Metrics

- **Response Times**: Tracked via middleware
- **Error Rates**: Logged and monitored
- **Cache Hit Rates**: Monitored for optimization
- **Scraping Success Rates**: Dashboard metrics

---

*See also: [[../api/API.md|API Documentation]], [[../architecture/ARCHITECTURE.md#data-layer|Architecture Overview]]*"