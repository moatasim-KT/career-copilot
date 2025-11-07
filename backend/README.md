# Career Copilot - Backend

FastAPI-based backend for the Career Copilot AI-powered career management platform.

## 📁 Directory Structure

```
backend/
├── 📄 Core Files
│   ├── __init__.py            # Package initialization
│   ├── alembic.ini            # Alembic migration config
│   ├── init.sql               # Database initialization SQL
│   ├── .env.example           # Environment variables template
│   └── .gitignore             # Git ignore patterns
│
├── 🔧 Configuration
│   └── .tools/                # Tool configurations
│       └── .coveragerc        # Code coverage config
│
├── 📂 Application Code
│   └── app/                   # Main application package
│       ├── __init__.py
│       ├── main.py           # FastAPI application entry
│       ├── dependencies.py    # Dependency injection
│       ├── celery.py         # Celery configuration
│       ├── local_celery.py   # Local Celery runner
│       ├── cli.py            # CLI commands
│       │
│       ├── api/              # API routes & endpoints
│       ├── config/           # Application configuration
│       ├── core/             # Core business logic
│       ├── middleware/       # FastAPI middleware
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic services
│       ├── repositories/     # Data access layer
│       ├── security/         # Authentication & authorization
│       ├── tasks/            # Celery background tasks
│       ├── workers/          # Background workers
│       ├── utils/            # Utility functions
│       ├── monitoring/       # Monitoring & observability
│       ├── templates/        # Email/notification templates
│       └── tests/            # Unit tests (co-located)
│
├── 📂 Database
│   ├── alembic/              # Database migrations
│   │   ├── versions/         # Migration versions
│   │   ├── env.py           # Alembic environment
│   │   └── script.py.mako   # Migration template
│   │
│   └── data/                 # Application data
│       ├── databases/        # SQLite databases (dev)
│       ├── uploads/          # User file uploads
│       ├── backups/          # Database backups
│       └── logs/             # Application logs
│
├── 📂 Executable Scripts
│   └── bin/                  # Initialization & seeding
│       ├── init_db.py       # Initialize database
│       └── seed_data.py     # Seed initial data
│
├── 📂 Utility Scripts
│   └── scripts/              # Organized by function
│       ├── database/         # Database operations
│       │   ├── backfill_job_fingerprints.py
│       │   └── verify_indexes.py
│       │
│       ├── monitoring/       # System monitoring
│       │   ├── monitor_deduplication.py
│       │   └── verify_system_health.py
│       │
│       ├── testing/          # Testing & debugging
│       │   ├── debug_auth.py
│       │   ├── test_deduplication_e2e.py
│       │   ├── test_email_notification.py
│       │   └── test_new_scrapers.py
│       │
│       ├── maintenance/      # Maintenance tasks
│       │   └── validate_configs.py
│       │
│       ├── celery/           # Celery utilities
│       └── verification/     # Verification scripts
│
├── 📂 Testing
│   └── tests/                # Integration tests
│       ├── conftest.py       # Pytest configuration
│       ├── test_auth.py
│       ├── test_resume_routes.py
│       ├── test_profile_endpoints.py
│       ├── test_production_services.py
│       ├── test_market_analysis.py
│       ├── test_feedback_analysis.py
│       ├── test_advanced_user_analytics.py
│       └── test_eu_visa_sponsorship.py
│
├── 📂 Build Artifacts (git-ignored)
│   ├── .venv/                # Python virtual environment
│   ├── .ruff_cache/          # Ruff cache
│   ├── .pytest_cache/        # Pytest cache
│   ├── career_copilot.egg-info/  # Package info
│   └── __pycache__/          # Python bytecode
│
└── 📂 Hidden/Archive
    └── .archive/             # Old configs, deprecated files
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Installation

```bash
# Navigate to backend
cd backend/

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python bin/init_db.py

# Seed initial data
python bin/seed_data.py

# Run migrations
alembic upgrade head
```

### Running the Application

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Celery worker
celery -A app.celery worker --loglevel=info
```

## 📂 Directory Purpose Guide

### Application Code (`app/`)

| Directory | Purpose | Examples |
|-----------|---------|----------|
| `api/` | API routes and endpoints | REST endpoints, GraphQL resolvers |
| `config/` | Application configuration | Settings, constants, env loading |
| `core/` | Core business logic | Domain models, business rules |
| `middleware/` | FastAPI middleware | Auth, CORS, logging, error handling |
| `models/` | SQLAlchemy ORM models | Database tables, relationships |
| `schemas/` | Pydantic schemas | Request/response validation |
| `services/` | Business logic services | Job scraping, AI analysis, notifications |
| `repositories/` | Data access layer | CRUD operations, queries |
| `security/` | Auth & authorization | JWT, OAuth, permissions |
| `tasks/` | Celery background tasks | Async jobs, scheduled tasks |
| `workers/` | Background workers | Long-running processes |
| `utils/` | Utility functions | Helpers, formatters, converters |
| `monitoring/` | Observability | Metrics, logging, tracing |
| `templates/` | Email/notification templates | Jinja2 templates |

### Database (`alembic/` & `data/`)

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `alembic/versions/` | Migration files | Auto-generated, version controlled |
| `data/databases/` | SQLite databases | Development only, git-ignored |
| `data/uploads/` | User uploads | Resumes, documents, git-ignored |
| `data/backups/` | Database backups | Git-ignored |
| `data/logs/` | Application logs | Git-ignored |

### Scripts (`scripts/` & `bin/`)

| Directory | Purpose | When to Use |
|-----------|---------|-------------|
| `bin/` | Initialization scripts | Database setup, data seeding |
| `scripts/database/` | Database operations | Backfills, index verification |
| `scripts/monitoring/` | System monitoring | Health checks, deduplication |
| `scripts/testing/` | Testing & debugging | E2E tests, debugging tools |
| `scripts/maintenance/` | Maintenance tasks | Config validation, cleanup |
| `scripts/celery/` | Celery utilities | Task management |
| `scripts/verification/` | Verification scripts | Deployment checks |

### Testing (`tests/`)

| Type | Location | Purpose |
|------|----------|---------|
| **Unit Tests** | `app/*/tests/` | Test individual components |
| **Integration Tests** | `tests/` | Test component interactions |
| **E2E Tests** | `scripts/testing/` | Test full workflows |

## 🔧 Common Tasks

### Database Operations

```bash
# Initialize database
python bin/init_db.py

# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Seed data
python bin/seed_data.py

# Verify indexes
python scripts/database/verify_indexes.py

# Backfill data
python scripts/database/backfill_job_fingerprints.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run E2E tests
python scripts/testing/test_deduplication_e2e.py
python scripts/testing/test_email_notification.py

# Debug authentication
python scripts/testing/debug_auth.py
```

### Monitoring & Maintenance

```bash
# System health check
python scripts/monitoring/verify_system_health.py

# Monitor deduplication
python scripts/monitoring/monitor_deduplication.py

# Validate configurations
python scripts/maintenance/validate_configs.py
```

### Celery Tasks

```bash
# Start Celery worker
celery -A app.celery worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.celery beat --loglevel=info

# Monitor tasks
celery -A app.celery events

# Purge queue
celery -A app.celery purge
```

## 🔐 Environment Variables

See `.env.example` for all available environment variables.

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/career_copilot

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# AI Providers
OPENAI_API_KEY=your-openai-key
```

### Optional Variables

```bash
# Email (SendGrid)
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@careercopilot.com

# Storage
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

## 📊 Application Architecture

### Tech Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.0+
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+
- **Task Queue**: Celery 5.3+
- **Migrations**: Alembic 1.12+

### Design Patterns

- **Repository Pattern**: Data access abstraction (`repositories/`)
- **Service Layer**: Business logic separation (`services/`)
- **Dependency Injection**: FastAPI dependencies (`dependencies.py`)
- **Schema Validation**: Pydantic models (`schemas/`)
- **Background Tasks**: Celery tasks (`tasks/`)

### API Structure

```
/api/v1/
├── /auth          # Authentication (login, register, tokens)
├── /users         # User management
├── /profiles      # User profiles
├── /jobs          # Job listings & search
├── /applications  # Job applications
├── /resumes       # Resume management
├── /analytics     # User analytics
├── /market        # Market analysis
└── /health        # Health checks
```

## 🧪 Testing Strategy

### Unit Tests (90%+ coverage goal)

Located in `app/*/tests/` alongside the code they test.

```python
# Example: app/services/tests/test_job_service.py
def test_job_search():
    # Test job search logic
    pass
```

### Integration Tests

Located in `tests/` for testing component interactions.

```python
# Example: tests/test_auth.py
def test_user_login_flow():
    # Test complete login flow
    pass
```

### E2E Tests

Located in `scripts/testing/` for end-to-end workflows.

```bash
python scripts/testing/test_deduplication_e2e.py
```

## 🔍 Code Quality

### Linting & Formatting

```bash
# Format code with Ruff
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Type Checking

```bash
# Run mypy
mypy app/
```

### Security Scanning

```bash
# Run Bandit
bandit -r app/

# Run safety check
safety check
```

## 📝 Adding New Features

### 1. Create Model (`app/models/`)

```python
# app/models/job.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
```

### 2. Create Schema (`app/schemas/`)

```python
# app/schemas/job.py
from pydantic import BaseModel

class JobCreate(BaseModel):
    title: str

class JobResponse(BaseModel):
    id: int
    title: str
```

### 3. Create Repository (`app/repositories/`)

```python
# app/repositories/job_repository.py
from app.models.job import Job

class JobRepository:
    def create(self, data: dict) -> Job:
        # CRUD operations
        pass
```

### 4. Create Service (`app/services/`)

```python
# app/services/job_service.py
class JobService:
    def __init__(self, repo: JobRepository):
        self.repo = repo
    
    def create_job(self, data: JobCreate) -> Job:
        # Business logic
        return self.repo.create(data.dict())
```

### 5. Create API Route (`app/api/`)

```python
# app/api/v1/jobs.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/jobs", response_model=JobResponse)
def create_job(data: JobCreate, service: JobService = Depends()):
    return service.create_job(data)
```

### 6. Add Tests

```python
# app/services/tests/test_job_service.py
def test_create_job():
    # Unit test
    pass

# tests/test_jobs.py
def test_job_api():
    # Integration test
    pass
```

## 🐛 Debugging

### Enable Debug Mode

```bash
# Set in .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Debug Authentication Issues

```bash
python scripts/testing/debug_auth.py
```

### Check Database Connection

```python
from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchone())
```

### Monitor Celery Tasks

```bash
# Flower (Celery monitoring)
celery -A app.celery flower

# Access at http://localhost:5555
```

## 📚 Documentation

- **API Docs**: `/docs` (Swagger UI)
- **Alternative API Docs**: `/redoc` (ReDoc)
- **OpenAPI Schema**: `/openapi.json`

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [Installation Guide](../docs/setup/INSTALLATION.md) - Full setup guide
- [API Documentation](../docs/api/API.md) - Complete API reference
- [Architecture](../docs/architecture/ARCHITECTURE.md) - System design
- [Development Guide](../docs/development/DEVELOPMENT.md) - Developer handbook

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/moatasim-KT/career-copilot/issues)
- **Email**: <moatasimfarooque@gmail.com>

---

**Last Updated**: November 7, 2025  
**Version**: 1.0.0
