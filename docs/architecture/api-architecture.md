# API Architecture

```mermaid
graph TB
    %% External Clients
    subgraph "External Clients"
        WEB[Web Browser<br/>Next.js Frontend]
        MOBILE[Mobile App<br/>React Native]
        API_CLI[API Client<br/>Python/JavaScript SDK]
        THIRD_PARTY[Third Party<br/>Integrations]
    end

    %% API Gateway / Load Balancer
    subgraph "API Gateway"
        NGINX[Nginx Reverse Proxy<br/>Rate Limiting<br/>SSL Termination<br/>Load Balancing]
    end

    %% Authentication Layer
    subgraph "Authentication Layer"
        AUTH_MIDDLEWARE[Authentication Middleware<br/>JWT Validation<br/>OAuth Token Refresh]
        PERMISSION_MIDDLEWARE[Permission Middleware<br/>RBAC<br/>Feature Flags]
    end

    %% API Routes
    subgraph "API Routes v1"
        subgraph "Core Routes"
            AUTH[POST /auth/*<br/>Login/Logout/OAuth]
            USERS[GET/PUT /users/*<br/>Profile Management]
            HEALTH[GET /health<br/>System Health]
        end

        subgraph "Job Management"
            JOBS[GET /jobs/*<br/>Job Search & Details]
            APPLICATIONS[CRUD /applications/*<br/>Application Tracking]
            SAVED_JOBS[GET/POST /saved-jobs/*<br/>Job Bookmarks]
        end

        subgraph "Analytics & Insights"
            ANALYTICS[GET /analytics/*<br/>Metrics & Reports]
            DASHBOARD[GET /dashboard/*<br/>Dashboard Data]
            GOALS[CRUD /goals/*<br/>Goal Setting]
            MILESTONES[CRUD /milestones/*<br/>Progress Tracking]
        end

        subgraph "Content & AI"
            GENERATE[POST /generate/*<br/>AI Content Generation]
            DOCUMENTS[CRUD /documents/*<br/>File Management]
            RESUMES[CRUD /resumes/*<br/>Resume Processing]
        end

        subgraph "Communication"
            NOTIFICATIONS[CRUD /notifications/*<br/>Alert Management]
            WEBSOCKET[/ws/notifications<br/>Real-time Updates]
            EMAIL[POST /email/*<br/>Email Delivery]
        end

        subgraph "Bulk Operations"
            BULK_IMPORT[POST /bulk/import<br/>Data Import]
            BULK_EXPORT[POST /bulk/export<br/>Data Export]
            BULK_UPDATE[POST /bulk/update<br/>Batch Updates]
        end
    end

    %% Service Layer
    subgraph "Service Layer"
        AUTH_SERVICE[AuthService<br/>OAuth/JWT/Token Mgmt]
        JOB_SERVICE[JobService<br/>Search/Deduplication]
        APPLICATION_SERVICE[ApplicationService<br/>Status/Workflow Mgmt]
        ANALYTICS_SERVICE[AnalyticsService<br/>Metrics/Aggregation]
        NOTIFICATION_SERVICE[NotificationService<br/>Multi-channel Delivery]
        LLM_SERVICE[LLMService<br/>AI Content Generation]
        CACHE_SERVICE[CacheService<br/>Redis Management]
        VECTOR_SERVICE[VectorService<br/>ChromaDB Embeddings]
    end

    %% Data Access Layer
    subgraph "Data Access Layer"
        USER_REPO[UserRepository<br/>SQLAlchemy ORM]
        JOB_REPO[JobRepository<br/>Job CRUD Operations]
        APPLICATION_REPO[ApplicationRepository<br/>Application Tracking]
        ANALYTICS_REPO[AnalyticsRepository<br/>Metrics Storage]
        NOTIFICATION_REPO[NotificationRepository<br/>Notification Queue]
        DOCUMENT_REPO[DocumentRepository<br/>File Storage]
    end

    %% External Services
    subgraph "External Services"
        POSTGRES[(PostgreSQL<br/>Primary Database)]
        REDIS[(Redis<br/>Cache & Sessions)]
        CHROMA[(ChromaDB<br/>Vector Embeddings)]
        CELERY_BROKER[(Redis<br/>Celery Message Broker)]
        CELERY_BACKEND[(Redis<br/>Celery Results)]
        SMTP[SMTP Server<br/>Email Delivery]
        OAUTH[OAuth Providers<br/>Google/GitHub]
    end

    %% Background Workers
    subgraph "Background Workers"
        JOB_SCRAPER[Job Scraper Worker<br/>Daily Job Ingestion]
        EMAIL_WORKER[Email Worker<br/>Notification Delivery]
        ANALYTICS_WORKER[Analytics Worker<br/>Metrics Processing]
        CLEANUP_WORKER[Cleanup Worker<br/>Data Maintenance]
    end

    %% Flow Connections
    WEB --> NGINX
    MOBILE --> NGINX
    API_CLI --> NGINX
    THIRD_PARTY --> NGINX

    NGINX --> AUTH_MIDDLEWARE
    AUTH_MIDDLEWARE --> PERMISSION_MIDDLEWARE

    PERMISSION_MIDDLEWARE --> AUTH
    PERMISSION_MIDDLEWARE --> USERS
    PERMISSION_MIDDLEWARE --> HEALTH
    PERMISSION_MIDDLEWARE --> JOBS
    PERMISSION_MIDDLEWARE --> APPLICATIONS
    PERMISSION_MIDDLEWARE --> SAVED_JOBS
    PERMISSION_MIDDLEWARE --> ANALYTICS
    PERMISSION_MIDDLEWARE --> DASHBOARD
    PERMISSION_MIDDLEWARE --> GOALS
    PERMISSION_MIDDLEWARE --> MILESTONES
    PERMISSION_MIDDLEWARE --> GENERATE
    PERMISSION_MIDDLEWARE --> DOCUMENTS
    PERMISSION_MIDDLEWARE --> RESUMES
    PERMISSION_MIDDLEWARE --> NOTIFICATIONS
    PERMISSION_MIDDLEWARE --> WEBSOCKET
    PERMISSION_MIDDLEWARE --> EMAIL
    PERMISSION_MIDDLEWARE --> BULK_IMPORT
    PERMISSION_MIDDLEWARE --> BULK_EXPORT
    PERMISSION_MIDDLEWARE --> BULK_UPDATE

    AUTH --> AUTH_SERVICE
    USERS --> AUTH_SERVICE
    JOBS --> JOB_SERVICE
    APPLICATIONS --> APPLICATION_SERVICE
    SAVED_JOBS --> JOB_SERVICE
    ANALYTICS --> ANALYTICS_SERVICE
    DASHBOARD --> ANALYTICS_SERVICE
    GOALS --> ANALYTICS_SERVICE
    MILESTONES --> ANALYTICS_SERVICE
    GENERATE --> LLM_SERVICE
    DOCUMENTS --> LLM_SERVICE
    RESUMES --> LLM_SERVICE
    NOTIFICATIONS --> NOTIFICATION_SERVICE
    WEBSOCKET --> NOTIFICATION_SERVICE
    EMAIL --> NOTIFICATION_SERVICE
    BULK_IMPORT --> JOB_SERVICE
    BULK_EXPORT --> ANALYTICS_SERVICE
    BULK_UPDATE --> APPLICATION_SERVICE

    AUTH_SERVICE --> USER_REPO
    JOB_SERVICE --> JOB_REPO
    APPLICATION_SERVICE --> APPLICATION_REPO
    ANALYTICS_SERVICE --> ANALYTICS_REPO
    NOTIFICATION_SERVICE --> NOTIFICATION_REPO
    LLM_SERVICE --> DOCUMENT_REPO

    USER_REPO --> POSTGRES
    JOB_REPO --> POSTGRES
    APPLICATION_REPO --> POSTGRES
    ANALYTICS_REPO --> POSTGRES
    NOTIFICATION_REPO --> POSTGRES
    DOCUMENT_REPO --> POSTGRES

    CACHE_SERVICE --> REDIS
    VECTOR_SERVICE --> CHROMA

    JOB_SCRAPER --> CELERY_BROKER
    EMAIL_WORKER --> CELERY_BROKER
    ANALYTICS_WORKER --> CELERY_BROKER
    CLEANUP_WORKER --> CELERY_BROKER

    CELERY_BROKER --> CELERY_BACKEND

    NOTIFICATION_SERVICE --> SMTP
    AUTH_SERVICE --> OAUTH

    %% Styling
    classDef clientClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef gatewayClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef middlewareClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef routeClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef serviceClass fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    classDef repoClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef externalClass fill:#f5f5f5,stroke:#424242,stroke-width:2px
    classDef workerClass fill:#e0f2f1,stroke:#00695c,stroke-width:2px

    class WEB,MOBILE,API_CLI,THIRD_PARTY clientClass
    class NGINX gatewayClass
    class AUTH_MIDDLEWARE,PERMISSION_MIDDLEWARE middlewareClass
    class AUTH,USERS,HEALTH,JOBS,APPLICATIONS,SAVED_JOBS,ANALYTICS,DASHBOARD,GOALS,MILESTONES,GENERATE,DOCUMENTS,RESUMES,NOTIFICATIONS,WEBSOCKET,EMAIL,BULK_IMPORT,BULK_EXPORT,BULK_UPDATE routeClass
    class AUTH_SERVICE,JOB_SERVICE,APPLICATION_SERVICE,ANALYTICS_SERVICE,NOTIFICATION_SERVICE,LLM_SERVICE,CACHE_SERVICE,VECTOR_SERVICE serviceClass
    class USER_REPO,JOB_REPO,APPLICATION_REPO,ANALYTICS_REPO,NOTIFICATION_REPO,DOCUMENT_REPO repoClass
    class POSTGRES,REDIS,CHROMA,CELERY_BROKER,CELERY_BACKEND,SMTP,OAUTH externalClass
    class JOB_SCRAPER,EMAIL_WORKER,ANALYTICS_WORKER,CLEANUP_WORKER workerClass
```

## API Architecture Overview

This diagram illustrates the complete API architecture for the Career Copilot system, showing the flow from external clients through the API layers to data persistence and background processing.

### API Layer Structure

#### 1. Client Layer
- **Web Browser**: Next.js frontend with React components
- **Mobile App**: React Native application (future)
- **API Client**: Python/JavaScript SDKs for programmatic access
- **Third Party**: External integrations and webhooks

#### 2. Gateway Layer
- **Nginx Reverse Proxy**: Load balancing, SSL termination, rate limiting
- Routes traffic to FastAPI backend with health checks and monitoring

#### 3. Authentication Layer
- **Authentication Middleware**: JWT token validation and OAuth token refresh
- **Permission Middleware**: Role-based access control (RBAC) and feature flags

#### 4. Route Layer (API v1)
Organized by functional domains:

**Core Routes**
- `POST /auth/*`: Authentication endpoints (login, logout, OAuth)
- `GET/PUT /users/*`: User profile management
- `GET /health`: System health checks

**Job Management**
- `GET /jobs/*`: Job search, filtering, and details
- `CRUD /applications/*`: Application lifecycle management
- `GET/POST /saved-jobs/*`: Job bookmarking system

**Analytics & Insights**
- `GET /analytics/*`: Metrics, reports, and trend analysis
- `GET /dashboard/*`: Aggregated dashboard data
- `CRUD /goals/*`: Goal setting and tracking
- `CRUD /milestones/*`: Progress milestone management

**Content & AI**
- `POST /generate/*`: AI-powered content generation
- `CRUD /documents/*`: File upload and management
- `CRUD /resumes/*`: Resume parsing and storage

**Communication**
- `CRUD /notifications/*`: Notification management
- `/ws/notifications`: WebSocket real-time updates
- `POST /email/*`: Email delivery and templates

**Bulk Operations**
- `POST /bulk/import`: Data import operations
- `POST /bulk/export`: Data export functionality
- `POST /bulk/update`: Batch update operations

### Service Layer Architecture

#### Service Pattern Implementation
All business logic resides in service classes following the Service Layer pattern:

```python
# backend/app/services/job_service.py
class JobService:
    def __init__(self, db: Session, cache: Redis, vector_store: ChromaDB):
        self.db = db
        self.cache = cache
        self.vector_store = vector_store

    async def search_jobs(self, user_id: int, filters: dict) -> List[Job]:
        # Complex search logic with caching and deduplication
        pass

    async def get_job_details(self, job_id: int, user_id: int) -> JobDetails:
        # Job detail retrieval with user-specific data
        pass
```

#### Service Dependencies
- **AuthService**: OAuth integration, JWT management, user authentication
- **JobService**: Job search, deduplication, bookmarking
- **ApplicationService**: Application workflow, status transitions
- **AnalyticsService**: Metrics calculation, dashboard aggregation
- **NotificationService**: Multi-channel delivery, WebSocket management
- **LLMService**: AI content generation with provider fallback
- **CacheService**: Redis operations for performance optimization
- **VectorService**: ChromaDB embeddings for job similarity

### Data Access Layer

#### Repository Pattern
Data access through repository classes providing clean separation:

```python
# backend/app/repositories/job_repository.py
class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_jobs_by_filters(self, filters: dict) -> List[Job]:
        query = select(Job).where(...)
        # Apply filters, sorting, pagination
        return await self.db.execute(query)

    async def create_job(self, job_data: dict) -> Job:
        job = Job(**job_data)
        self.db.add(job)
        await self.db.commit()
        return job
```

#### Connection Management
- **PostgreSQL**: Primary data storage with async connections
- **Redis**: Caching, sessions, and Celery message broker
- **ChromaDB**: Vector embeddings for job similarity matching

### Background Processing

#### Celery Workers
Asynchronous task processing for performance and reliability:

```python
# backend/app/tasks/job_ingestion_tasks.py
@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.ingest_jobs")
def ingest_jobs(self, user_ids: List[int] = None):
    """Daily job scraping and ingestion"""
    try:
        scraper = JobScraper()
        jobs = scraper.scrape_all_platforms()

        deduplicator = JobDeduplicationService()
        unique_jobs = deduplicator.deduplicate(jobs)

        # Bulk insert with conflict resolution
        db.bulk_insert_mappings(Job, unique_jobs)
    except Exception as e:
        logger.error(f"Job ingestion failed: {e}")
        raise self.retry(countdown=300)  # Retry after 5 minutes
```

**Worker Types:**
- **Job Scraper Worker**: Daily job ingestion from multiple platforms
- **Email Worker**: Notification delivery and template processing
- **Analytics Worker**: Metrics calculation and report generation
- **Cleanup Worker**: Data maintenance and archive operations

### API Design Patterns

#### RESTful Design
```python
# Consistent REST patterns
GET    /jobs                    # List jobs with filtering
GET    /jobs/{id}              # Get specific job
POST   /jobs/{id}/save         # Save job to user's list
PUT    /applications/{id}      # Update application status
DELETE /applications/{id}      # Delete application
```

#### Pagination and Filtering
```python
# Standardized pagination
GET /jobs?page=1&limit=20&sort=-posted_date&company=google&location=remote

# Response format
{
    "data": [...],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 150,
        "total_pages": 8
    },
    "filters": {
        "company": "google",
        "location": "remote"
    }
}
```

#### Error Handling
```python
# Consistent error responses
HTTP 400 Bad Request
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {
            "field": "email",
            "reason": "Invalid email format"
        }
    }
}

HTTP 404 Not Found
{
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Job not found",
        "details": {
            "resource": "job",
            "id": "123"
        }
    }
}
```

### Performance Optimization

#### Caching Strategy
```python
# Multi-level caching
@cache(expire=300)  # 5 minutes
async def get_job_search_results(query: str, filters: dict):
    # Database query with complex joins
    pass

@cache(expire=3600)  # 1 hour
async def get_user_dashboard_data(user_id: int):
    # Aggregated analytics data
    pass
```

#### Database Optimization
```sql
-- Optimized queries with proper indexing
CREATE INDEX CONCURRENTLY idx_jobs_user_location ON jobs(user_id, location);
CREATE INDEX CONCURRENTLY idx_applications_status_date ON applications(status, applied_date);
CREATE INDEX CONCURRENTLY idx_analytics_user_type_date ON analytics(user_id, type, generated_at);
```

#### Connection Pooling
```python
# Database connection configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False
}
```

### Security Implementation

#### Authentication Flow
```python
# JWT-based authentication
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.state.user = payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    return await call_next()
```

#### Rate Limiting
```python
# Rate limiting by endpoint and user
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    endpoint = request.url.path

    # Check rate limits in Redis
    if await is_rate_limited(client_ip, endpoint):
        raise HTTPException(status_code=429, detail="Too many requests")

    return await call_next()
```

### Monitoring and Observability

#### API Metrics
- **Request Count**: Total requests by endpoint
- **Response Times**: P95 response time by endpoint
- **Error Rates**: 4xx/5xx error rates by endpoint
- **Throughput**: Requests per second

#### Health Checks
```python
# Comprehensive health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "celery": await check_celery_health(),
        "external_services": await check_external_services()
    }
```

## Related Diagrams

- [[system-architecture|System Architecture]] - Overall system structure
- [[data-architecture|Data Architecture]] - Database relationships
- [[authentication-architecture|Authentication Architecture]] - Auth flow details
- [[deployment-architecture|Deployment Architecture]] - Infrastructure setup

## Component References

- [[auth-component|Authentication Component]] - Auth implementation
- [[applications-component|Applications Component]] - Job tracking API
- [[analytics-component|Analytics Component]] - Metrics API
- [[notifications-component|Notifications Component]] - Communication API

---

*See also: [[api-endpoints|API Endpoint Reference]], [[rate-limiting|Rate Limiting Guide]], [[error-handling|Error Handling Patterns]]*"