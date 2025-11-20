# System Components Architecture

> **Component Details**: Frontend, backend, API, data layer, and database architecture details.

**Quick Links**: [[README|Architecture Hub]] | [[ARCHITECTURE|System Architecture]] | [[AI_AND_INTEGRATIONS|AI & Integrations]]

---

## Table of Contents

1. [Frontend Architecture](#frontend-architecture)
2. [Backend Architecture](#backend-architecture)
3. [API Architecture](#api-architecture)
4. [Data Architecture](#data-architecture)
5. [Database Schema](#database-schema)

---

## Frontend Architecture

### Overview

The frontend is built with **Next.js 14** using the App Router, providing a modern, performant React application with server-side rendering capabilities.

### Technology Stack

- **Framework**: Next.js 14+ (App Router)
- **UI Library**: React 18+
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand (client), TanStack React Query (server)
- **Forms**: React Hook Form + Zod validation
- **Animations**: Framer Motion
- **HTTP Client**: Axios with TypeScript types

### Directory Structure

```
frontend/src/
├── app/                    # Next.js App Router pages
│   ├── dashboard/          # Dashboard pages
│   ├── jobs/               # Job browsing/search
│   ├── applications/       # Application tracking
│   ├── analytics/          # Analytics dashboards
│   ├── settings/           # User settings
│   └── ...                 # Other feature pages
│
├── components/             # React components
│   ├── ui/                 # Base UI primitives (shadcn/ui)
│   ├── applications/       # Application management components
│   ├── jobs/               # Job-related components
│   ├── dashboard/          # Dashboard widgets
│   ├── layout/             # Layout components
│   └── ...                 # Other domain components
│
├── lib/                    # Utilities and services
│   ├── api/                # API client
│   ├── hooks/              # Custom React hooks
│   ├── utils/              # Utility functions
│   └── contexts/           # React Context providers
│
├── hooks/                  # Additional custom hooks
│   ├── useNetworkStatus.ts
│   ├── useWebSocket.ts
│   └── ...
│
└── styles/                 # Global styles
    └── globals.css         # Global CSS + Tailwind
```

### Component Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  App Router (Pages)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  dashboard/  │  │    jobs/     │  │  apps/   │  │
│  │  page.tsx    │  │  page.tsx    │  │page.tsx  │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
          ▼                  ▼                ▼
┌─────────────────────────────────────────────────────┐
│           Feature Components (Domain Logic)         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ EnhancedDash │  │  JobList     │  │ AppCard  │  │
│  │    board     │  │  JobFilters  │  │ AppList  │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
          ▼                  ▼                ▼
┌─────────────────────────────────────────────────────┐
│          UI Components (Presentational)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Button  │  │   Card   │  │   DataTable      │  │
│  │  Input   │  │  Badge   │  │   Modal/Dialog   │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│              State Management Layer                 │
│  ┌──────────────┐  ┌──────────────────────────────┐│
│  │   Zustand    │  │   TanStack React Query       ││
│  │ (Client State│  │   (Server State Sync)        ││
│  └──────────────┘  └──────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Key Patterns

**1. Server Components (RSC)**:
- Used for static pages, SEO-critical content
- Data fetching happens on the server
- Reduced JavaScript bundle size

**2. Client Components**:
- Interactive UI components
- State management
- Event handlers

**3. Custom Hooks**:
- `useWebSocket` - WebSocket connection management
- `useNetworkStatus` - Network status monitoring
- `useAuth` - Authentication state
- `useJobs` - Job data fetching/caching

**4. API Client Pattern**:
```typescript
// lib/api/client.ts
export const apiClient = {
  jobs: {
    getAll: () => axios.get<Job[]>('/api/v1/jobs'),
    getById: (id: string) => axios.get<Job>(`/api/v1/jobs/${id}`),
    // ... typed API methods
  },
  applications: {
    // ... typed methods
  }
}
```

---

## Backend Architecture

### Overview

The backend is built with **FastAPI**, following a layered architecture pattern with clear separation between routing, business logic, and data access.

### Technology Stack

- **Framework**: FastAPI 0.100+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2+
- **Validation**: Pydantic 2+
- **Migrations**: Alembic
- **Task Queue**: Celery 5+
- **Async**: AsyncIO, async/await

### Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                  API Routes Layer                   │
│         (backend/app/api/v1/*.py)                   │
│  - Request/Response handling                        │
│  - Input validation (Pydantic)                      │
│  - Authentication/Authorization                     │
│  - Dependency injection                             │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│               Service Layer                         │
│         (backend/app/services/*.py)                 │
│  - Business logic                                   │
│  - Orchestration between repositories               │
│  - External service integration                     │
│  - 50+ specialized services                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│            Repository Layer (Implicit)              │
│  - Data access abstraction                          │
│  - Query building                                   │
│  - Transaction management                           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                 Data Models                         │
│         (backend/app/models/*.py)                   │
│  - SQLAlchemy ORM models                            │
│  - Database schema definition                       │
└─────────────────────────────────────────────────────┘
```

### Service Organization

**Core Services** (50+ total):

**Job Management**:
- `job_service.py` - Job CRUD operations
- `job_scraping_service.py` - Multi-source job scraping
- `job_recommendation_service.py` - AI-powered matching
- `job_deduplication_service.py` - Duplicate detection

**AI/LLM**:
- `llm_service.py` - Multi-provider LLM management
- `content_generator_service.py` - Resume/cover letter generation
- `skill_analysis_service.py` - Skill extraction
- `skill_gap_analyzer.py` - Gap identification

**User/Application**:
- `user_service.py` - User management
- `application_service.py` - Application tracking
- `notification_service.py` - Real-time notifications
- `analytics_service.py` - Metrics and insights

**Infrastructure**:
- `cache_service.py` - Redis caching
- `websocket_service.py` - WebSocket management
- `quota_manager.py` - API quota tracking

### Design Patterns

**1. Dependency Injection**:
```python
from fastapi import Depends
from app.core.database import get_db

@app.get("/jobs")
async def get_jobs(db: AsyncSession = Depends(get_db)):
    service = JobService(db)
    return await service.get_all()
```

**2. Service Layer**:
```python
class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all(self) -> List[Job]:
        # Business logic here
        pass
```

**3. Pydantic Schemas**:
```python
class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    # ... validation rules

class JobResponse(BaseModel):
    id: int
    title: str
    # ... response fields
    
    class Config:
        from_attributes = True
```

---

## API Architecture

### RESTful API Design

**Base URL**: `/api/v1/`

**Authentication**:
- JWT tokens via `Authorization: Bearer <token>` header
- OAuth 2.0 for third-party auth (Google, GitHub, LinkedIn)

### Endpoint Organization

**80+ endpoints** organized by resource:

```
/api/v1/
├── /auth                  # Authentication
│   ├── POST /login
│   ├── POST /register
│   ├── POST /logout
│   └── POST /refresh
│
├── /users                 # User management
│   ├── GET /me
│   ├── PATCH /me
│   └── DELETE /me
│
├── /jobs                  # Job operations
│   ├── GET /
│   ├── GET /{id}
│   ├── POST /search
│   └── GET /recommendations
│
├── /applications          # Application tracking
│   ├── GET /
│   ├── POST /
│   ├── PATCH /{id}
│   └── DELETE /{id}
│
├── /analytics             # Analytics
│   ├── GET /dashboard
│   ├── GET /metrics
│   └── GET /trends
│
└── ...                    # 70+ more endpoints
```

### API Response Format

**Success Response**:
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2025-11-20T12:00:00Z",
    "version": "1.0"
  }
}
```

**Error Response**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Job not found",
    "details": { ... }
  }
}
```

### API Documentation

- **OpenAPI/Swagger**: Auto-generated at `/docs`
- **ReDoc**: Alternative docs at `/redoc`
- **Type Safety**: Full TypeScript types on frontend

---

## Data Architecture

### Data Flow Diagram

```
┌──────────────┐
│   Frontend   │
└──────┬───────┘
       │ HTTP Request
       ▼
┌──────────────┐
│  API Layer   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│           Service Layer                  │
│  ┌────────────┐    ┌─────────────────┐  │
│  │  Primary   │    │   Cache Layer   │  │
│  │  Logic     │◄───│    (Redis)      │  │
│  └─────┬──────┘    └─────────────────┘  │
└────────┼─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Database Layer                      │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │ PostgreSQL   │  │    ChromaDB        │  │
│  │ (Structured  │  │  (Vector Store)    │  │
│  │   Data)      │  │  (Embeddings)      │  │
│  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Caching Strategy

**Redis Cache Layers**:

1. **Application Cache**:
   - User sessions
   - Frequently accessed data (user profiles, job listings)
   - TTL: 5-60 minutes based on volatility

2. **Query Result Cache**:
   - Expensive database queries
   - Analytics aggregations
   - TTL: 1-24 hours

3. **Rate Limiting**:
   - API rate limit tracking
   - Per-user, per-IP tracking

4. **Celery Broker**:
   - Task queue messages
   - Task result storage

---

## Database Schema

### Core Tables

**Users & Authentication**:
```sql
users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR,
    profile JSONB DEFAULT '{}',
    settings_json JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
```

**Jobs**:
```sql
jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    location VARCHAR,
    description TEXT,
    url VARCHAR UNIQUE,
    salary_min INTEGER,
    salary_max INTEGER,
    employment_type VARCHAR,
    seniority_level VARCHAR,
    skills JSONB DEFAULT '[]',
    source VARCHAR NOT NULL,
    source_id VARCHAR,
    posted_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Indexes
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_source ON jobs(source);
```

**Applications**:
```sql
applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    status VARCHAR DEFAULT 'applied',
    applied_date DATE,
    notes TEXT,
    resume_version VARCHAR,
    cover_letter TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

-- Indexes
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_applied_date ON applications(applied_date DESC);
```

**Notifications**:
```sql
notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

### Relationships

```
users (1) ──< (M) applications
jobs (1) ──< (M) applications
users (1) ──< (M) notifications
users (1) ──< (M) saved_searches
users (1) ──< (M) goals
```

### Database Optimizations

**Indexes**:
- Primary keys (automatic)
- Foreign keys for joins
- Frequently queried columns (title, company, status, dates)
- Composite indexes for common filter combinations

**Partitioning**:
- Time-based partitioning for large tables (jobs, notifications)
- Archival of old data

**Connection Pooling**:
- SQLAlchemy connection pool (10-20 connections)
- Async connection management

---

## Related Documentation

- **Main Architecture**: [[ARCHITECTURE|System Architecture Overview]]
- **AI & Integrations**: [[AI_AND_INTEGRATIONS|AI/LLM & Job Board Integrations]]
- **Security**: [[/security/ARCHITECTURE|Security Architecture]]
- **Performance**: [[/performance/ARCHITECTURE|Performance Architecture]]
- **Development**: [[/development/DEVELOPER_GUIDE|Developer Guide]]
- **Database Setup**: [[/setup/GETTING_STARTED|Getting Started Guide]]

---

**Last Updated**: November 2025  
**Component Version**: 2.0
