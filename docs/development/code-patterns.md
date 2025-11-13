# Code Patterns & Best Practices

## Overview

This document outlines the common patterns and best practices used throughout the Career Copilot codebase.

## Architectural Patterns

### 1. Service Layer Pattern

**Purpose**: Separate business logic from API endpoints for better testability and maintainability.

**Implementation**:
```python
# ✅ CORRECT - Service handles business logic
class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_matching_jobs(self, user_id: int, filters: dict) -> List[Job]:
        # Complex business logic here
        return self.db.query(Job).filter(...).all()

# API endpoint only handles HTTP concerns
@router.get("/jobs/matches")
def get_jobs(filters: dict, db: Session = Depends(get_db)):
    service = JobService(db)
    return service.get_matching_jobs(current_user.id, filters)
```

**Location**: [[../../backend/app/services/|backend/app/services/]]

### 2. Repository Pattern

**Purpose**: Abstract data access operations for better testing and code organization.

**Implementation**:
```python
class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id: int) -> Job:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_filtered(self, filters: dict) -> List[Job]:
        query = self.db.query(Job)
        if filters.get('location'):
            query = query.filter(Job.location.ilike(f"%{filters['location']}%"))
        return query.all()
```

**Location**: [[../../backend/app/repositories/|backend/app/repositories/]]

### 3. Dependency Injection

**Purpose**: Make code more testable and modular by injecting dependencies.

**Implementation**:
```python
# FastAPI handles dependency injection
def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)

@router.get("/jobs")
def list_jobs(service: JobService = Depends(get_job_service)):
    return service.get_all_jobs()
```

**Location**: [[../../backend/app/dependencies.py|backend/app/dependencies.py]]

## Database Patterns

### 1. Async Database Operations

**Purpose**: Improve concurrency and performance with non-blocking database operations.

**Implementation**:
```python
# ✅ CORRECT - Async operations
async def get_jobs(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Job))
    return result.scalars().all()

# ❌ WRONG - Blocking operations
def get_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()  # Blocks the event loop
```

**Migration Guide**: [[../../backend/app/api/v1/jobs.py|Async Jobs API]]

### 2. Connection Management

**Purpose**: Properly manage database connections to prevent leaks and ensure performance.

**Implementation**:
```python
# Use context managers for transactions
async with db.begin():
    job = Job(title="Developer", company="TechCorp")
    db.add(job)
    await db.commit()

# Or use dependency injection
async def create_job(job_data: JobCreate, db: AsyncSession = Depends(get_async_db)):
    job = Job(**job_data.dict())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job
```

### 3. Query Optimization

**Purpose**: Ensure efficient database queries with proper indexing and loading strategies.

**Implementation**:
```python
# Use selectinload for eager loading
query = select(Job).options(selectinload(Job.applications))

# Use pagination for large datasets
def get_jobs_paginated(skip: int = 0, limit: int = 20):
    return db.query(Job).offset(skip).limit(limit).all()

# Use indexed fields in WHERE clauses
jobs = db.query(Job).filter(Job.user_id == user_id, Job.is_active == True)
```

## API Patterns

### 1. RESTful Resource Naming

**Purpose**: Consistent, predictable API endpoints following REST conventions.

**Implementation**:
```python
# ✅ CORRECT - RESTful naming
@router.get("/jobs")           # List resources
@router.get("/jobs/{id}")      # Get single resource
@router.post("/jobs")          # Create resource
@router.put("/jobs/{id}")      # Update resource
@router.delete("/jobs/{id}")   # Delete resource

# Resource relationships
@router.get("/jobs/{id}/applications")  # Nested resources
@router.post("/jobs/{id}/apply")        # Actions on resources
```

### 2. Error Handling

**Purpose**: Consistent error responses and proper HTTP status codes.

**Implementation**:
```python
@router.get("/jobs/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_async_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "type": "validation_error"}
    )
```

**Location**: [[../../backend/app/schemas/api_models.py|API Error Models]]

### 3. Request Validation

**Purpose**: Ensure data integrity with comprehensive input validation.

**Implementation**:
```python
from pydantic import BaseModel, Field, validator

class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    company: str = Field(..., min_length=1, max_length=255)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)

    @validator('salary_max')
    def salary_max_must_be_greater(cls, v, values):
        if v and values.get('salary_min') and v < values['salary_min']:
            raise ValueError('salary_max must be greater than salary_min')
        return v
```

**Location**: [[../../backend/app/schemas/|backend/app/schemas/]]

## Caching Patterns

### 1. Redis Caching

**Purpose**: Cache expensive operations to improve performance.

**Implementation**:
```python
from app.services.cache_service import cache_service

@cache_service.cached(ttl_seconds=300)  # Cache for 5 minutes
async def search_jobs(query: str, filters: dict):
    # Expensive search operation
    return await perform_complex_search(query, filters)

# Manual cache operations
await cache_service.set("key", value, ttl_seconds=3600)
cached_value = await cache_service.get("key")
```

**Location**: [[../../backend/app/services/cache_service.py|Cache Service]]

### 2. Application-Level Caching

**Purpose**: Cache frequently accessed data in memory.

**Implementation**:
```python
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=1000)
def get_job_categories():
    # Cache expensive category computation
    return compute_categories()

# Time-based invalidation
class CategoryCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str):
        if key in self._cache:
            if datetime.now() - self._timestamps[key] < timedelta(hours=1):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
```

## Testing Patterns

### 1. Service Layer Testing

**Purpose**: Test business logic independently of HTTP concerns.

**Implementation**:
```python
def test_job_service_create(db: Session):
    service = JobService(db)
    job_data = JobCreate(title="Test Job", company="TestCo")

    job = service.create_job(job_data, user_id=1)

    assert job.title == "Test Job"
    assert job.user_id == 1
    assert db.query(Job).filter(Job.id == job.id).first() is not None
```

**Location**: [[../../backend/tests/test_services/|Service Tests]]

### 2. API Integration Testing

**Purpose**: Test complete request/response cycles.

**Implementation**:
```python
def test_create_job_api(client: TestClient, db: Session):
    job_data = {"title": "API Test Job", "company": "APITestCo"}

    response = client.post("/api/v1/jobs", json=job_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "API Test Job"
    assert "id" in data
```

**Location**: [[../../backend/tests/test_api/|API Tests]]

### 3. Fixture Usage

**Purpose**: Reusable test data and setup.

**Implementation**:
```python
@pytest.fixture
def test_user(db: Session):
    user = User(email="test@example.com", hashed_password="hash")
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def client():
    return TestClient(app)

def test_user_creation(test_user, db: Session):
    assert test_user.email == "test@example.com"
    assert db.query(User).filter(User.id == test_user.id).first()
```

**Location**: [[../../backend/tests/conftest.py|Test Fixtures]]

## Configuration Patterns

### 1. Unified Configuration

**Purpose**: Centralized configuration management with validation.

**Implementation**:
```python
from app.core.unified_config import get_config

config = get_config()

# Access configuration
database_url = config.database_url
openai_key = config.openai_api_key
redis_url = config.redis_url

# Type-safe access
assert isinstance(config.api_port, int)
assert config.environment in ["development", "production", "testing"]
```

**Location**: [[../../backend/app/core/unified_config.py|Unified Config]]

### 2. Environment-Specific Settings

**Purpose**: Different configurations for different environments.

**Implementation**:
```python
class Settings(BaseSettings):
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    @validator('debug', pre=True, always=True)
    def set_debug_based_on_env(cls, v, values):
        if values.get('environment') == 'development':
            return True
        return v or False

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Error Handling Patterns

### 1. Custom Exceptions

**Purpose**: Meaningful error handling with proper error types.

**Implementation**:
```python
class JobNotFoundError(Exception):
    def __init__(self, job_id: int):
        self.job_id = job_id
        super().__init__(f"Job with id {job_id} not found")

class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error for {field}: {message}")

# Usage
try:
    job = service.get_job(job_id)
    if not job:
        raise JobNotFoundError(job_id)
except JobNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

### 2. Logging Patterns

**Purpose**: Comprehensive logging for debugging and monitoring.

**Implementation**:
```python
import structlog

logger = structlog.get_logger()

async def create_job(job_data: JobCreate):
    logger.info("Creating job", job_title=job_data.title, company=job_data.company)

    try:
        job = await service.create_job(job_data)
        logger.info("Job created successfully", job_id=job.id)
        return job
    except Exception as e:
        logger.error("Failed to create job", error=str(e), job_data=job_data.dict())
        raise
```

**Location**: [[../../backend/app/core/logging.py|Logging Configuration]]

## Performance Patterns

### 1. Background Task Processing

**Purpose**: Handle long-running operations without blocking requests.

**Implementation**:
```python
from app.celery import celery_app

@celery_app.task
def scrape_jobs_task(keywords: str, location: str):
    scraper = JobScraper()
    jobs = scraper.scrape_linkedin(keywords, location)

    # Save to database
    for job_data in jobs:
        save_job_to_db(job_data)

# Trigger from API
@router.post("/jobs/scrape")
async def scrape_jobs(keywords: str, location: str):
    task = scrape_jobs_task.delay(keywords, location)
    return {"task_id": task.id, "status": "processing"}
```

**Location**: [[../../backend/app/tasks/|Background Tasks]]

### 2. Pagination

**Purpose**: Handle large datasets efficiently.

**Implementation**:
```python
def get_jobs_paginated(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    total = db.query(Job).count()
    jobs = db.query(Job).offset(skip).limit(limit).all()

    return {
        "items": jobs,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total
    }
```

## Security Patterns

### 1. Input Validation

**Purpose**: Prevent injection attacks and ensure data integrity.

**Implementation**:
```python
from pydantic import BaseModel, validator
import bleach

class JobCreate(BaseModel):
    title: str
    description: str

    @validator('title', 'description')
    def sanitize_html(cls, v):
        if isinstance(v, str):
            return bleach.clean(v, strip=True)
        return v
```

### 2. Rate Limiting

**Purpose**: Prevent abuse and ensure fair resource usage.

**Implementation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
async def add_rate_limiting(request: Request, call_next):
    # Custom rate limiting logic
    pass

@router.get("/jobs/search")
@limiter.limit("10/minute")
async def search_jobs(query: str):
    # Rate limited endpoint
    pass
```

---

*See also: [[../architecture/ARCHITECTURE.md|Architecture Overview]], [[../decisions/adr-index.md|Architectural Decisions]]*"