# Career Copilot - Backend

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

FastAPI-based backend with AI-powered job management, multi-provider LLM integration, and real-time notifications.

## Quick Links

- **Setup**: [[../LOCAL_SETUP|Local Setup]] - Complete development guide
- **Testing**: [[tests/TESTING_NOTES|Testing Notes]] - Test infrastructure and known issues
- **API Docs**: http://localhost:8000/docs (OpenAPI, when running)
- **Main App**: [[app/main.py|Main Application]] - FastAPI application entry point
- **Documentation Hub**: [[../docs/index|Documentation Hub]] - Central documentation

## Architecture

### Core Application

**Entry Point**: [[app/main.py|Main Application]]
- FastAPI app initialization
- CORS configuration
- API route registration
- WebSocket setup

**Configuration**: [[app/core/|Core Directory]]
- [[app/core/config.py|Configuration]] - Unified settings management
- [[app/core/database.py|Database]] - Database manager (sync + async)
- [[app/core/security.py|Security]] - JWT auth, password hashing
- [[app/core/celery_app.py|Celery]] - Celery config and scheduler
- [[app/core/websocket_manager.py|WebSocket Manager]] - WebSocket connection manager
- [[app/core/logging.py|Logging]] - Structured logging setup

### Service Layer (Business Logic)

All services in [[app/services/|Services Directory]]:

**AI & Content Generation**:
- [[app/services/llm_service.py|LLM Service]] - Multi-provider LLM (OpenAI, Groq, Anthropic)
- [[app/services/content_generator_service.py|Content Generator]] - Resume/cover letter generation
- [[app/services/job_recommendation_service.py|Job Recommendations]] - Job recommendations

**Job Management**:
- [[app/services/job_service.py|Job Service]] - Job CRUD and search
- [[app/services/job_deduplication_service.py|Job Deduplication]] - MinHash-based deduplication
- [[app/services/scraping/|Scrapers]] - 9 job board scrapers (LinkedIn, Indeed, etc.)

**Application Tracking**:
- [[app/services/application_service.py|Application Service]] - Application lifecycle management
- [[app/services/analytics_service.py|Analytics Service]] - Application analytics

**Notifications**:
- [[app/services/notification_service.py|Notification Service]] - Unified notification service
- [[app/services/slack_service.py|Slack Service]] - Slack integration

- [[app/services/email_service.py]] - Email notifications│   └── data/                 # Application data

│       ├── databases/        # SQLite databases (dev)

### API Routes│       ├── uploads/          # User file uploads

│       ├── backups/          # Database backups

All routes in [[app/api/v1/]]:│       └── logs/             # Application logs

│

| Route | File | Description |├── 📂 Executable Scripts

|-------|------|-------------|│   └── bin/                  # Initialization & seeding

| `/auth` | [[app/api/v1/auth.py]] | JWT authentication |│       ├── init_db.py       # Initialize database

| `/jobs` | [[app/api/v1/jobs.py]] | Job search, filtering |│       └── seed_data.py     # Seed initial data

| `/applications` | [[app/api/v1/applications.py]] | Application tracking |│

| `/notifications` | [[app/api/v1/notifications.py]] | Notification management |├── 📂 Utility Scripts

| `/templates` | [[app/api/v1/templates.py]] | Document templates |│   └── scripts/              # Organized by function

| `/websocket` | [[app/api/v1/websocket.py]] | Real-time updates |│       ├── database/         # Database operations

│       │   ├── backfill_job_fingerprints.py

### Database Models│       │   └── verify_indexes.py

│       │

All models in [[app/models/]]:│       ├── monitoring/       # System monitoring

│       │   ├── monitor_deduplication.py

- [[app/models/user.py]] - User accounts│       │   └── verify_system_health.py

- [[app/models/job.py]] - Job postings│       │

- [[app/models/application.py]] - Applications│       ├── testing/          # Testing & debugging

- [[app/models/notification.py]] - Notifications│       │   ├── debug_auth.py

- [[app/models/template.py]] - Document templates│       │   ├── test_deduplication_e2e.py

- [[app/models/document.py]] - User documents│       │   ├── test_email_notification.py

- [[app/models/goal.py]] - User goals│       │   └── test_new_scrapers.py

- [[app/models/interview.py]] - Interview tracking│       │

│       ├── maintenance/      # Maintenance tasks

**Migrations**: [[alembic/versions/]]│       │   └── validate_configs.py

│       │

### Background Tasks│       ├── celery/           # Celery utilities

│       └── verification/     # Verification scripts

Celery tasks in [[app/tasks/]]:│

├── 📂 Testing

- [[app/tasks/job_ingestion_tasks.py]] - Job scraping (daily 4 AM UTC)│   └── tests/                # Integration tests

- [[app/tasks/notification_tasks.py]] - Morning briefing, evening update│       ├── conftest.py       # Pytest configuration

│       ├── test_auth.py

**Scheduler**: [[app/core/celery_app.py]]│       ├── test_resume_routes.py

│       ├── test_profile_endpoints.py

## Configuration│       ├── test_production_services.py

│       ├── test_market_analysis.py

### Environment Variables│       ├── test_feedback_analysis.py

│       ├── test_advanced_user_analytics.py

Template: [[.env.example]] → Copy to `.env`│       └── test_eu_visa_sponsorship.py

│

**Required**:├── 📂 Build Artifacts (git-ignored)

```bash│   ├── .venv/                # Python virtual environment

DATABASE_URL=postgresql://user:pass@host:5432/career_copilot│   ├── .ruff_cache/          # Ruff cache

REDIS_URL=redis://localhost:6379/0│   ├── .pytest_cache/        # Pytest cache

SECRET_KEY=<64-char-hex>│   ├── career_copilot.egg-info/  # Package info

JWT_SECRET_KEY=<64-char-hex>│   └── __pycache__/          # Python bytecode

OPENAI_API_KEY=sk-...│

```└── 📂 Hidden/Archive

    └── .archive/             # Old configs, deprecated files

See [[.env.example]] for complete list and [[../LOCAL_SETUP.md#configuration]].```



### Config Files## 🚀 Quick Start



- **LLM Providers**: [[../config/llm_config.json]]### Prerequisites

- **Feature Flags**: [[../config/feature_flags.json]]

- **Linting**: [[../config/ruff.toml]]- Python 3.11+

- PostgreSQL 14+

## Development- Redis 7+



### Running Locally### Installation



**Via Docker** (recommended):```bash

```bash# Navigate to backend

docker-compose up -d backend celery celery-beatcd backend/

```

## Create virtual environment

See [[../LOCAL_SETUP.md]] for complete setup guide.python3.11 -m venv .venv

source .venv/bin/activate  # On Windows: .venv\Scripts\activate

### Testing

## Install dependencies

**Documentation**: [[tests/TESTING_NOTES.md]]pip install -e .



```bash# Set up environment

pytest -v                                  # All testscp .env.example .env

pytest --cov=backend --cov-report=html     # With coverage# Edit .env with your configuration

pytest tests/unit/test_simple_async.py -xvs  # Specific test

```# Initialize database

python bin/init_db.py

**Test structure**:

- [[tests/conftest.py]] - Shared fixtures# Seed initial data

- [[tests/unit/]] - Unit testspython bin/seed_data.py

- [[tests/integration/]] - Integration tests

- [[tests/phase_6/]] - Feature tests# Run migrations

alembic upgrade head

### Code Quality```



Via [[../Makefile]]:### Running the Application

```bash

make lint-python          # flake8, ruff```bash

make format-python        # black, isort, ruff format# Development mode (with auto-reload)

make type-check-python    # mypyuvicorn app.main:app --reload --host 0.0.0.0 --port 8000

make security-python      # bandit, safety

```# Production mode

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

## Key Patterns

## With Celery worker

### Service Layer Patterncelery -A app.celery worker --loglevel=info

```

**All business logic in [[app/services/]]**:

## 📂 Directory Purpose Guide

```python
## ✅ Service handles logic - app/services/job_service.py

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_matching_jobs(self, user_id: int) -> List[Job]:
        # Complex logic here
        pass
```

### Application Code (`app/`)

| Directory       | Purpose                   | Examples                                 |
| --------------- | ------------------------- | ---------------------------------------- |
| `api/`          | API routes and endpoints  | REST endpoints, GraphQL resolvers        |
| `config/`       | Application configuration | Settings, constants, env loading         |
| `core/`         | Core business logic       | Domain models, business rules            |
| `middleware/`   | FastAPI middleware        | Auth, CORS, logging, error handling      |
| `models/`       | SQLAlchemy ORM models     | Database tables, relationships           |
| `schemas/`      | Pydantic schemas          | Request/response validation              |
| `services/`     | Business logic services   | Job scraping, AI analysis, notifications |
| `repositories/` | Data access layer         | CRUD operations, queries                 |
| `security/`     | Auth & authorization      | JWT, OAuth, permissions                  |
| `tasks/`        | Celery background tasks   | Async jobs, scheduled tasks              |

```python
## ✅ Route is thin wrapper - app/api/v1/jobs.py

@router.get("/jobs/matches")
def get_jobs(db: Session = Depends(get_db)):
    service = JobService(db)
    return service.get_matching_jobs(user_id)
```

```| `workers/` | Background workers | Long-running processes |

| `utils/` | Utility functions | Helpers, formatters, converters |

### Dependency Injection| `monitoring/` | Observability | Metrics, logging, tracing |

| `templates/` | Email/notification templates | Jinja2 templates |

Always use FastAPI dependencies:

### Database (`alembic/` & `data/`)

```python

from app.core.database import get_db| Directory | Purpose | Notes |

|-----------|---------|-------|

@router.post("/jobs")| `alembic/versions/` | Migration files | Auto-generated, version controlled |

def create_job(db: Session = Depends(get_db)):| `data/databases/` | SQLite databases | Development only, git-ignored |

    # db is automatically injected| `data/uploads/` | User uploads | Resumes, documents, git-ignored |

    pass| `data/backups/` | Database backups | Git-ignored |

```| `data/logs/` | Application logs | Git-ignored |



## Project Structure### Scripts (`scripts/` & `bin/`)



```| Directory | Purpose | When to Use |

backend/|-----------|---------|-------------|

├── app/                  # Application code| `bin/` | Initialization scripts | Database setup, data seeding |

│   ├── api/v1/          # API routes| `scripts/database/` | Database operations | Backfills, index verification |

│   ├── core/            # Core configuration| `scripts/monitoring/` | System monitoring | Health checks, deduplication |

│   ├── models/          # Database models| `scripts/testing/` | Testing & debugging | E2E tests, debugging tools |

│   ├── services/        # Business logic (PRIMARY)| `scripts/maintenance/` | Maintenance tasks | Config validation, cleanup |

│   ├── tasks/           # Celery tasks| `scripts/celery/` | Celery utilities | Task management |

│   └── main.py          # FastAPI app| `scripts/verification/` | Verification scripts | Deployment checks |

├── tests/               # Test suite

├── alembic/             # Database migrations### Testing (`tests/`)

├── scripts/             # Utility scripts

├── data/                # Uploads, logs, backups| Type | Location | Purpose |

├── .env.example         # Environment template|------|----------|---------|

└── pyproject.toml       # Package config| **Unit Tests** | `app/*/tests/` | Test individual components |

```| **Integration Tests** | `tests/` | Test component interactions |

| **E2E Tests** | `scripts/testing/` | Test full workflows |

## Troubleshooting

## 🔧 Common Tasks

See [[../LOCAL_SETUP.md#troubleshooting]] for detailed troubleshooting.

### Database Operations

**Quick checks**:

```bash```bash

## Test database connection

```bash
docker-compose exec backend python -c "from app.core.database import engine; print(engine)"
```

## Initialize database

```bash
python bin/init_db.py
```

## View logs

```bash
docker-compose logs -f backend
```

## Create migration

```bash
alembic revision --autogenerate -m "description"
```

## Run migrations

```bash
alembic upgrade head
```

## Rollback migration

```bash
alembic downgrade -1
```

## Seed data

```bash
python bin/seed_data.py
```

## Verify indexes

```bash
python scripts/database/verify_indexes.py
```

## Backfill data

```bash
python scripts/database/backfill_job_fingerprints.py
```

## Additional Resources

- **Project Status**: [[../PROJECT_STATUS.md]]
- **Setup Guide**: [[../LOCAL_SETUP.md]]
- **Coding Standards**: [[../.github/copilot-instructions.md]]
- **API Documentation**: http://localhost:8000/docs

```bash
## Run all tests
pytest

## Run specific test file
pytest tests/test_auth.py

## Run with coverage
pytest --cov=app --cov-report=html

## Run E2E tests
python scripts/testing/test_deduplication_e2e.py
python scripts/testing/test_email_notification.py

## Debug authentication
python scripts/testing/debug_auth.py
```

## Monitoring & Maintenance

```bash
## System health check
python scripts/monitoring/verify_system_health.py

## Monitor deduplication
python scripts/monitoring/monitor_deduplication.py

## Validate configurations
python scripts/maintenance/validate_configs.py
```

### Celery Tasks

```bash
## Start Celery worker
celery -A app.celery worker --loglevel=info

## Start Celery beat (scheduler)
celery -A app.celery beat --loglevel=info

## Monitor tasks
celery -A app.celery events

## Purge queue
celery -A app.celery purge
```

## 🔐 Environment Variables

See `.env.example` for all available environment variables.

### Required Variables

```bash
## Database
DATABASE_URL=postgresql://user:pass@localhost:5432/career_copilot

## Redis
REDIS_URL=redis://localhost:6379/0

## Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

## AI Providers
OPENAI_API_KEY=your-openai-key
```

### Optional Variables

```bash
## Email (SendGrid)
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@careercopilot.com

## Storage
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

## Monitoring
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
## Example: app/services/tests/test_job_service.py
def test_job_search():
    # Test job search logic
    pass
```

### Integration Tests

Located in `tests/` for testing component interactions.

```python
## Example: tests/test_auth.py
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
## Format code with Ruff
ruff format .

## Lint code
ruff check .

## Fix auto-fixable issues
ruff check --fix .
```

### Type Checking

```bash
## Run mypy
mypy app/
```

### Security Scanning

```bash
## Run Bandit
bandit -r app/

## Run safety check
safety check
```

## 📝 Adding New Features

### 1. Create Model (`app/models/`)

```python
## app/models/job.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
```

### 2. Create Schema (`app/schemas/`)

```python
## app/schemas/job.py
from pydantic import BaseModel

class JobCreate(BaseModel):
    title: str

class JobResponse(BaseModel):
    id: int
    title: str
```

### 3. Create Repository (`app/repositories/`)

```python
## app/repositories/job_repository.py
from app.models.job import Job

class JobRepository:
    def create(self, data: dict) -> Job:
        # CRUD operations
        pass
```

### 4. Create Service (`app/services/`)

```python
## app/services/job_service.py
class JobService:
    def __init__(self, repo: JobRepository):
        self.repo = repo
    
    def create_job(self, data: JobCreate) -> Job:
        # Business logic
        return self.repo.create(data.dict())
```

### 5. Create API Route (`app/api/`)

```python
## app/api/v1/jobs.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/jobs", response_model=JobResponse)
def create_job(data: JobCreate, service: JobService = Depends()):
    return service.create_job(data)
```

### 6. Add Tests

```python
## app/services/tests/test_job_service.py
def test_create_job():
    # Unit test
    pass

## tests/test_jobs.py
def test_job_api():
    # Integration test
    pass
```

## 🐛 Debugging

### Enable Debug Mode

```bash
## Set in .env
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
## Flower (Celery monitoring)
celery -A app.celery flower

## Access at http://localhost:5555
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
