# Codebase Consolidation and Streamlining Design

## Overview

This design document outlines the technical approach for consolidating and streamlining the Career Copilot codebase. The goal is to create a clean, maintainable job application tracking system by removing over-engineering, fixing broken dependencies, and establishing a clear project identity.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Career Copilot System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐              ┌─────────────────┐       │
│  │    Frontend     │              │    Backend      │       │
│  │   (Streamlit)   │◄────HTTP────►│   (FastAPI)     │       │
│  │                 │              │                 │       │
│  │  - Job List     │              │  - REST API     │       │
│  │  - Add/Edit     │              │  - Business     │       │
│  │  - Analytics    │              │    Logic        │       │
│  │  - Dashboard    │              │  - Auth         │       │
│  └─────────────────┘              └────────┬────────┘       │
│                                             │                │
│                                    ┌────────▼────────┐       │
│                                    │    Database     │       │
│                                    │    (SQLite)     │       │
│                                    │                 │       │
│                                    │  - Jobs         │       │
│                                    │  - Applications │       │
│                                    │  - Users        │       │
│                                    └─────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Backend Architecture (Simplified)

```
backend/
├── app/
│   ├── main.py                 # Single entry point
│   ├── api/
│   │   └── v1/
│   │       ├── jobs.py         # Job endpoints
│   │       ├── applications.py # Application endpoints
│   │       ├── users.py        # User endpoints
│   │       ├── analytics.py    # Analytics endpoints
│   │       └── health.py       # Health check
│   ├── core/
│   │   ├── config.py           # Simple config
│   │   ├── database.py         # DB connection
│   │   ├── security.py         # Auth/security
│   │   └── logging.py          # Logging setup
│   ├── models/
│   │   ├── job.py              # Job model
│   │   ├── application.py      # Application model
│   │   └── user.py             # User model
│   ├── services/
│   │   ├── job_service.py      # Job business logic
│   │   ├── application_service.py
│   │   └── analytics_service.py
│   └── schemas/
│       ├── job.py              # Pydantic schemas
│       ├── application.py
│       └── user.py
├── tests/
│   ├── test_jobs.py
│   ├── test_applications.py
│   └── test_analytics.py
└── requirements.txt            # Minimal dependencies
```

### Frontend Architecture (Simplified)

```
frontend/
├── app.py                      # Single entry point
├── components/
│   ├── job_list.py             # Job listing component
│   ├── job_form.py             # Add/edit job form
│   ├── analytics_dashboard.py # Analytics display
│   └── filters.py              # Search/filter component
├── utils/
│   ├── api_client.py           # Backend API client
│   └── formatters.py           # Data formatting
└── requirements.txt            # Streamlit + deps
```

## Components and Interfaces

### 1. Backend API (FastAPI)

**Purpose**: Provide REST API for job application management

**Key Components**:
- **main.py**: Application factory with minimal middleware
- **API Routes**: RESTful endpoints for CRUD operations
- **Services**: Business logic layer
- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic validation schemas

**Middleware Stack** (Essential Only):
1. CORS Middleware (for frontend communication)
2. Authentication Middleware (JWT-based)
3. Logging Middleware (request/response logging)
4. Error Handler Middleware (consistent error responses)

**API Endpoints**:

```
GET    /api/v1/health              # Health check
POST   /api/v1/auth/login          # User login
POST   /api/v1/auth/register       # User registration

GET    /api/v1/jobs                # List jobs
POST   /api/v1/jobs                # Create job
GET    /api/v1/jobs/{id}           # Get job details
PUT    /api/v1/jobs/{id}           # Update job
DELETE /api/v1/jobs/{id}           # Delete job

GET    /api/v1/applications        # List applications
POST   /api/v1/applications        # Create application
GET    /api/v1/applications/{id}   # Get application
PUT    /api/v1/applications/{id}   # Update application
DELETE /api/v1/applications/{id}   # Delete application

GET    /api/v1/analytics/summary   # Application statistics
GET    /api/v1/analytics/timeline  # Application timeline
GET    /api/v1/analytics/status    # Status breakdown
```

### 2. Frontend Interface (Streamlit)

**Purpose**: Provide user interface for job tracking

**Key Components**:
- **app.py**: Main application with page routing
- **Components**: Reusable UI components
- **API Client**: Simple HTTP client for backend communication

**Pages**:
1. **Dashboard**: Overview of applications and statistics
2. **Job List**: Browse and search job opportunities
3. **Add/Edit Job**: Form for creating/updating jobs
4. **Analytics**: Visual analytics and insights
5. **Settings**: User preferences and configuration

### 3. Database Layer

**Purpose**: Persist job application data

**Technology**: SQLite (simple, file-based, no setup required)

**Schema**:

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    url VARCHAR(500),
    salary_range VARCHAR(100),
    job_type VARCHAR(50),
    remote BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Applications table
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    applied_date DATE,
    interview_date DATE,
    response_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- Application status values: 
-- 'interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined'
```

## Data Models

### Job Model

```python
class Job(Base):
    __tablename__ = "jobs"
    
    id: int
    user_id: int
    company: str
    title: str
    location: Optional[str]
    description: Optional[str]
    url: Optional[str]
    salary_range: Optional[str]
    job_type: Optional[str]  # full-time, part-time, contract
    remote: bool
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
    applications: List[Application]
```

### Application Model

```python
class Application(Base):
    __tablename__ = "applications"
    
    id: int
    user_id: int
    job_id: int
    status: str  # interested, applied, interview, offer, rejected, accepted, declined
    applied_date: Optional[date]
    interview_date: Optional[date]
    response_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
    job: Job
```

### User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    jobs: List[Job]
    applications: List[Application]
```

## Configuration Management

### Simple Environment-Based Configuration

**Configuration Source**: Single `.env` file

**Required Variables**:
```bash
# Application
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./data/career_copilot.db

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API
API_HOST=0.0.0.0
API_PORT=8002
CORS_ORIGINS=http://localhost:8501,http://localhost:3000

# Frontend
BACKEND_URL=http://localhost:8002
```

**Configuration Loading**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    cors_origins: str = "http://localhost:8501"
    
    class Config:
        env_file = ".env"
```

## Error Handling

### Consistent Error Response Format

```python
{
    "error": "Error Type",
    "message": "User-friendly error message",
    "details": {
        "field": "Specific error details"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Categories

1. **Validation Errors** (400): Invalid input data
2. **Authentication Errors** (401): Invalid or missing credentials
3. **Authorization Errors** (403): Insufficient permissions
4. **Not Found Errors** (404): Resource doesn't exist
5. **Server Errors** (500): Internal server errors

## Testing Strategy

### Test Levels

1. **Unit Tests**: Test individual functions and methods
   - Services layer
   - Utility functions
   - Data validation

2. **Integration Tests**: Test API endpoints
   - CRUD operations
   - Authentication flow
   - Error handling

3. **End-to-End Tests**: Test complete workflows
   - User registration and login
   - Job creation and application
   - Analytics generation

### Test Coverage Goals

- Minimum 70% code coverage
- 100% coverage for critical paths (auth, data persistence)
- All API endpoints tested

## Deployment Strategy

### Development Environment

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload --port 8002

# Start frontend
cd frontend
streamlit run app.py --server.port 8501
```

### Production Environment

**Option 1: Docker Compose**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8002:8002"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=sqlite:///./data/career_copilot.db
  
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8002
    depends_on:
      - backend
```

**Option 2: Cloud Deployment**
- Backend: Deploy to Cloud Run, Heroku, or similar
- Frontend: Deploy to Streamlit Cloud or similar
- Database: Use managed SQLite or upgrade to PostgreSQL

## Migration Plan

### Phase 1: Cleanup and Consolidation

1. Remove contract analysis code
2. Delete redundant main.py files
3. Remove unused middleware and services
4. Clean up configuration files
5. Update documentation

### Phase 2: Fix Dependencies

1. Create minimal requirements.txt
2. Fix all import statements
3. Remove references to non-existent modules
4. Test application startup

### Phase 3: Implement Core Features

1. Set up database models
2. Implement job CRUD endpoints
3. Implement application CRUD endpoints
4. Add authentication
5. Create frontend components

### Phase 4: Testing and Documentation

1. Write unit tests
2. Write integration tests
3. Update README
4. Create deployment guide
5. Add API documentation

## Security Considerations

### Authentication

- JWT-based authentication
- Password hashing with bcrypt
- Token expiration and refresh

### Authorization

- User-based access control
- Users can only access their own data
- Admin role for system management (optional)

### Data Protection

- Input validation on all endpoints
- SQL injection prevention (ORM)
- XSS prevention (output encoding)
- CORS configuration for frontend

### Best Practices

- Environment variables for secrets
- HTTPS in production
- Rate limiting on auth endpoints
- Audit logging for sensitive operations

## Performance Considerations

### Database Optimization

- Indexes on frequently queried fields (user_id, status, created_at)
- Pagination for list endpoints
- Efficient queries with proper joins

### Caching Strategy

- Simple in-memory caching for analytics
- Cache invalidation on data updates
- No complex caching infrastructure needed initially

### API Performance

- Response time target: < 200ms for most endpoints
- Async/await for I/O operations
- Connection pooling for database

## Monitoring and Observability

### Health Checks

```python
GET /api/v1/health
Response: {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Logging

- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request/response logging
- Error tracking with stack traces

### Metrics (Optional)

- Request count and latency
- Error rates
- Active users
- Database query performance

## Files to Remove

### Backend Files to Delete

- `backend/app/main_simple.py`
- `backend/app/main_streamlined.py`
- `backend/app/main_job_tracker.py`
- All contract analysis related files in `backend/app/api/v1/`
- Unused middleware files
- Complex configuration system files

### Frontend Files to Delete

- Contract analysis components
- Unused utility files
- Next.js files (if using Streamlit only)

### Configuration Files to Simplify

- Remove complex YAML configurations
- Keep only `.env` and simple config loader
- Remove redundant Docker configurations

### Documentation to Update

- README.md (focus on job tracking)
- API documentation
- Deployment guides
- Remove contract analysis references

## Success Criteria

1. **Single Entry Point**: One main.py for backend, one app.py for frontend
2. **Working Imports**: No import errors on startup
3. **Clear Purpose**: All code focused on job tracking
4. **Minimal Dependencies**: Only essential packages in requirements.txt
5. **Clean Architecture**: Clear separation of concerns
6. **Working Tests**: All tests pass
7. **Documentation**: Clear, accurate documentation
8. **Easy Deployment**: Simple deployment process with clear instructions