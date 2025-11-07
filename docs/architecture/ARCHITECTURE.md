# System Architecture

## High-Level Architecture

Career Copilot follows a modern microservices-inspired architecture with clear separation of concerns:

```
┌─────────────────┐
│   Frontend      │
│   (Next.js)     │
│   Port: 3000    │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   Backend API   │
│   (FastAPI)     │
│   Port: 8000    │
└────┬────────┬───┘
     │        │
     │        └─────────┐
     │                  │
     ▼                  ▼
┌─────────┐      ┌──────────┐
│  Celery │      │  Redis   │
│ Workers │◄─────┤  Broker  │
└────┬────┘      └──────────┘
     │
     ▼
┌─────────────┐
│ PostgreSQL  │
│  Database   │
└─────────────┘
```

## Technology Stack

### Backend

- **Framework**: FastAPI 0.109+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **Migration**: Alembic
- **Task Queue**: Celery 5.3+
- **Message Broker**: Redis 7+
- **Database**: PostgreSQL 14+
- **Validation**: Pydantic 2.0+

### Frontend

- **Framework**: Next.js 15.5
- **UI Library**: React 19.2
- **Language**: TypeScript 5.0+
- **Styling**: TailwindCSS 3.4+
- **UI Components**: shadcn/ui
- **State Management**: React Context + Hooks
- **HTTP Client**: Fetch API

### Infrastructure

- **Containerization**: Docker & Docker Compose
- **Web Server**: Uvicorn (dev), Gunicorn (prod)
- **Reverse Proxy**: Nginx (production)
- **Process Manager**: Systemd (production)

### AI/ML Services

- **LLM Provider**: OpenAI GPT-4o-mini
- **Alternative Provider**: Anthropic Claude 3.5 Sonnet
- **Vector Store**: ChromaDB
- **Embeddings**: OpenAI text-embedding-3-small

## Component Architecture

### Backend Structure

```
backend/
├── app/
│   ├── api/              # API routes & endpoints
│   │   └── v1/           # API version 1
│   │       ├── auth/     # Authentication
│   │       ├── jobs/     # Job management
│   │       ├── users/    # User management
│   │       ├── applications/
│   │       └── ...
│   │
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration
│   │   ├── security.py   # Security utilities
│   │   ├── database.py   # Database connection
│   │   └── celery_app.py # Celery configuration
│   │
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── application.py
│   │   └── ...
│   │
│   ├── schemas/          # Pydantic schemas
│   │   ├── user.py
│   │   ├── job.py
│   │   └── ...
│   │
│   ├── services/         # Business logic
│   │   ├── job_service.py
│   │   ├── ai_service.py
│   │   ├── scraping_service.py
│   │   └── ...
│   │
│   └── utils/            # Helper functions
│       ├── validators.py
│       ├── formatters.py
│       └── ...
│
└── tests/                # Test suite
```

### Frontend Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── (auth)/       # Auth routes
│   │   ├── (dashboard)/  # Dashboard routes
│   │   ├── jobs/         # Job routes
│   │   ├── applications/ # Application routes
│   │   └── layout.tsx    # Root layout
│   │
│   ├── components/       # React components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── forms/        # Form components
│   │   ├── tables/       # Table components
│   │   └── ...
│   │
│   ├── lib/              # Utilities
│   │   ├── api.ts        # API client
│   │   ├── utils.ts      # Helper functions
│   │   └── hooks.ts      # Custom hooks
│   │
│   ├── types/            # TypeScript types
│   │   ├── job.ts
│   │   ├── user.ts
│   │   └── ...
│   │
│   └── styles/           # Global styles
│       └── globals.css
│
└── public/               # Static assets
```

## Data Flow

### Job Discovery Flow

```
1. Celery Beat Scheduler
   ↓ (triggers periodic task)
2. Job Scraping Service
   ↓ (fetches from multiple sources)
3. Data Validation & Normalization
   ↓ (validates and cleans data)
4. Database Storage (PostgreSQL)
   ↓ (stores job listings)
5. Vector Embedding (ChromaDB)
   ↓ (creates semantic search index)
6. API Endpoint
   ↓ (exposes to frontend)
7. Frontend Display
```

### Application Submission Flow

```
1. User Input (Frontend)
   ↓
2. API Request
   ↓
3. Validation (Pydantic)
   ↓
4. AI Resume Generation (OpenAI)
   ↓
5. Application Creation (Database)
   ↓
6. Background Tasks (Celery)
   │   ├── Email Notification
   │   ├── Analytics Update
   │   └── Status Tracking
   ↓
7. Response to Frontend
```

### AI Content Generation Flow

```
1. User Request
   ↓
2. Context Gathering
   │   ├── User Profile
   │   ├── Job Description
   │   └── Past Applications
   ↓
3. Prompt Engineering
   ↓
4. LLM API Call (OpenAI/Anthropic)
   ↓
5. Response Processing
   ↓
6. Content Validation
   ↓
7. Storage & Delivery
```

## Design Patterns

### Repository Pattern

Separates data access logic from business logic:

```python
# models/job.py - Data model
class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    
# services/job_service.py - Business logic
class JobService:
    def get_jobs(self, filters):
        # Business logic here
        pass
```

### Dependency Injection

Used extensively in FastAPI:

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/jobs")
def get_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()
```

### Factory Pattern

For creating service instances:

```python
class AIServiceFactory:
    @staticmethod
    def create_service(provider: str):
        if provider == "openai":
            return OpenAIService()
        elif provider == "anthropic":
            return AnthropicService()
```

### Observer Pattern

For event-driven notifications:

```python
class EventManager:
    def __init__(self):
        self.subscribers = []
    
    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)
    
    def notify(self, event):
        for subscriber in self.subscribers:
            subscriber.update(event)
```

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    source VARCHAR(50),
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Applications table
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_id INTEGER REFERENCES jobs(id),
    status VARCHAR(50),
    applied_at TIMESTAMP DEFAULT NOW()
);
```

### Relationships

- **One-to-Many**: User → Applications
- **One-to-Many**: Job → Applications
- **Many-to-Many**: User ↔ Skills (via user_skills)
- **Many-to-Many**: Job ↔ Skills (via job_skills)

## API Architecture

### RESTful Design

```
GET    /api/v1/jobs              # List jobs
GET    /api/v1/jobs/{id}         # Get job
POST   /api/v1/jobs              # Create job
PUT    /api/v1/jobs/{id}         # Update job
DELETE /api/v1/jobs/{id}         # Delete job

GET    /api/v1/applications      # List applications
POST   /api/v1/applications      # Create application
GET    /api/v1/applications/{id} # Get application
PUT    /api/v1/applications/{id} # Update application
```

### Response Format

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Senior Data Scientist"
  },
  "message": "Job retrieved successfully",
  "timestamp": "2025-11-07T10:00:00Z"
}
```

### Error Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid job data",
    "details": ["Title is required"]
  },
  "timestamp": "2025-11-07T10:00:00Z"
}
```

## Security Architecture

### Authentication

- JWT-based authentication
- Access tokens (short-lived)
- Refresh tokens (long-lived)
- Token blacklisting for logout

### Authorization

- Role-Based Access Control (RBAC)
- Single-user mode (User ID: 1)
- Future: Multi-tenant support

### Data Protection

- Password hashing (bcrypt)
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (content sanitization)
- CSRF protection (SameSite cookies)

## Performance Optimizations

### Caching Strategy

```python
# Redis caching for frequently accessed data
@cache(ttl=300)  # 5 minutes
def get_active_jobs():
    return db.query(Job).filter(Job.is_active == True).all()
```

### Database Indexing

```sql
-- Optimize job searches
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at DESC);

-- Optimize application queries
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
```

### Async Operations

```python
# Async database queries
@app.get("/jobs")
async def get_jobs(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Job))
    return result.scalars().all()
```

### Background Tasks

```python
# Offload heavy tasks to Celery
@celery_app.task
def send_notification_email(user_id, message):
    # Heavy email sending logic
    pass
```

## Scalability Considerations

### Horizontal Scaling

- Stateless backend servers (multiple Uvicorn workers)
- Load balancing with Nginx
- Session storage in Redis (not in-memory)

### Database Scaling

- Read replicas for query load distribution
- Connection pooling (SQLAlchemy)
- Query optimization and indexing

### Caching Layers

- Application-level caching (Redis)
- CDN for static assets
- Browser caching for API responses

### Microservices Ready

Current monolithic structure can be split into:
- **Job Service**: Job scraping and management
- **Application Service**: Application tracking
- **AI Service**: Resume generation and analysis
- **Notification Service**: Email and alerts
- **Analytics Service**: Reporting and insights

## Monitoring & Observability

### Logging

- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized log aggregation

### Metrics

- Application metrics (Prometheus)
- System metrics (CPU, memory, disk)
- Custom business metrics

### Health Checks

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": check_database(),
        "redis": check_redis(),
        "celery": check_celery()
    }
```

## Next Steps

- [API Documentation](../api/API.md) - Explore API endpoints
- [Development Guide](../development/DEVELOPMENT.md) - Start developing
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Deploy to production
- [Security Guide](../security/SECURITY.md) - Security best practices
