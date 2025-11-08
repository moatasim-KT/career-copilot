# Career Copilot - AI Agent Instructions

## Project Overview
Career Copilot is a production-ready AI-powered job application tracking and career management platform targeting EU tech markets. The system combines intelligent web scraping, AI-driven content generation (GPT-4/Claude/Groq), and comprehensive application tracking.

**Architecture**: FastAPI backend + Next.js 15 frontend, PostgreSQL + Redis, Celery for async jobs, ChromaDB for vector embeddings.

## Critical Setup Commands

### Development Environment
```bash
# Full stack startup (Docker - RECOMMENDED)
docker-compose up -d

# Local development (requires Python 3.11+, Node 18+, PostgreSQL 14+, Redis 7+)
make install              # Install all dependencies
make dev-setup            # Complete dev environment setup

# Backend only
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend only  
cd frontend && npm run dev

# Celery workers (required for background jobs)
celery -A app.core.celery_app worker --loglevel=info --concurrency=2
celery -A app.core.celery_app beat --loglevel=info  # Scheduler
```

### Testing & Quality
```bash
make quality-check        # Run all linting, type-checking, security
make test                 # Run all tests (backend + frontend)
make ci-check            # Full CI validation

# Backend specific
pytest -v --cov=backend   # With coverage
pytest backend/tests/test_auth.py -v  # Specific test

# Frontend specific
cd frontend && npm test   # Unit tests
cd frontend && npm run test:coverage
```

## Project-Specific Conventions

### Backend Architecture Patterns

#### 1. **Service Layer Pattern** (PRIMARY PATTERN)
All business logic lives in `backend/app/services/`. Never put business logic in routes.

```python
# ✅ CORRECT - Service handles business logic
# backend/app/services/job_service.py
class JobService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_matching_jobs(self, user_id: int, filters: dict) -> List[Job]:
        # Complex business logic here
        pass

# backend/app/api/v1/jobs.py
@router.get("/jobs/matches")
def get_jobs(db: Session = Depends(get_db)):
    service = JobService(db)
    return service.get_matching_jobs(user_id, filters)

# ❌ WRONG - Logic in route
@router.get("/jobs/matches")
def get_jobs(db: Session = Depends(get_db)):
    # Don't put business logic here!
    jobs = db.query(Job).filter(...).all()
```

#### 2. **Unified Configuration System**
Configuration uses `UnifiedSettings` in `backend/app/core/unified_config.py`. Access via `get_config()` or the adapter `Settings` class.

```python
from app.core.config import get_settings
settings = get_settings()
api_key = settings.openai_api_key  # All settings accessed this way
```

#### 3. **Database Management**
- Uses SQLAlchemy 2.0 with async support (asyncpg for PostgreSQL, aiosqlite for SQLite)
- Both sync and async engines managed by `DatabaseManager` in `backend/app/core/database.py`
- Always use dependency injection: `db: Session = Depends(get_db)`

```python
# Synchronous database operations
from app.core.database import get_db
from sqlalchemy.orm import Session

def get_user(db: Session = Depends(get_db)):
    return db.query(User).first()

# Async operations (less common, but supported)
from app.core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_async(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalar_one_or_none()
```

#### 4. **LLM Service Usage** (Multi-Provider AI)
The platform uses multiple LLM providers (OpenAI, Groq, Anthropic) with intelligent fallback.

```python
from app.services.llm_service import LLMService

llm_service = LLMService()
# Auto-selects best provider based on task complexity, cost, and availability
response = await llm_service.generate_completion(
    prompt="Analyze this job posting...",
    task_category="analysis",  # Routes to appropriate model
    max_tokens=2000
)
```

Provider configuration: `config/llm_config.json` defines priorities and capabilities.

#### 5. **Celery Background Tasks**
All long-running operations use Celery tasks in `backend/app/tasks/`.

```python
from celery import shared_task

@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.ingest_jobs", max_retries=3)
def ingest_jobs(self, user_ids: List[int] = None):
    # Background job logic
    pass

# Trigger from route
from app.celery import celery_app
result = celery_app.send_task("app.tasks.job_ingestion_tasks.ingest_jobs", args=[user_ids])
```

Scheduled tasks defined in `backend/app/celery.py` with `beat_schedule` (daily job scraping at 4am UTC, etc.).

### Frontend Architecture Patterns

#### 1. **Next.js 15 App Router** 
Uses App Router (not Pages Router). Structure: `frontend/src/app/[route]/page.tsx`

```tsx
// frontend/src/app/dashboard/page.tsx
export default async function DashboardPage() {
  // Server components by default, use 'use client' for interactivity
  return <DashboardLayout />
}
```

#### 2. **Unified API Client**
All backend communication through `frontend/src/lib/api/client.ts`. Never use raw `fetch`.

```typescript
// ✅ CORRECT
import { fetchApi } from '@/lib/api/client';

const response = await fetchApi<Job[]>('/jobs/matches', {
  params: { limit: 10 },
  requiresAuth: false  // Auth disabled by default in this codebase
});

if (response.error) {
  console.error(response.error);
  return;
}
const jobs = response.data;

// ❌ WRONG
const response = await fetch('http://localhost:8000/api/v1/jobs');
```

#### 3. **Component Organization**
- `frontend/src/components/ui/` - shadcn/ui primitives
- `frontend/src/components/pages/` - Page-level components
- `frontend/src/components/forms/` - Form components
- `frontend/src/components/layout/` - Layout components

#### 4. **State Management**
Uses React Context + hooks for global state, Zustand for complex state. No Redux.

```typescript
// frontend/src/contexts/AuthContext.tsx (example pattern)
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>;
}
```

### Job Scraping & Deduplication

**Critical**: The system scrapes 9 job boards (LinkedIn, Indeed, StepStone, etc.) and uses content fingerprinting to deduplicate.

- Scrapers: `backend/app/services/scraping/` (per-board implementations)
- Deduplication: `backend/app/services/job_deduplication_service.py` (uses MinHash + Jaccard similarity)
- Ingestion: `backend/app/tasks/job_ingestion_tasks.py` (Celery task scheduled daily)

```python
# Job fingerprint calculated from title, company, location, description
fingerprint = generate_job_fingerprint(job_data)
# Check if exists before saving
if not is_duplicate(fingerprint, threshold=0.85):
    save_job(job_data)
```

### Security Patterns

**ALWAYS run Snyk scan** for new code (see `.github/instructions/snyk_rules.instructions.md`).

```bash
# Security checks
make security  # Bandit + Safety
```

- JWT authentication in `backend/app/security/` (though auth is disabled by default in development)
- CORS configured in `backend/app/main.py`
- Content Security Policy (CSP) for frontend in `frontend/src/middleware/csp.ts` (includes Sentry domains)

### Testing Conventions

#### Backend Tests
- Fixtures in `backend/tests/conftest.py` (creates test DB with SQLite, seeds test users)
- Tests co-located with code AND in `backend/tests/`
- Use pytest fixtures: `def test_feature(db: Session):`

```python
def test_job_deduplication(db: Session):
    # Test user with id=1 is automatically created by conftest.py
    job1 = Job(user_id=1, title="Software Engineer", company="Acme")
    db.add(job1)
    db.commit()
    assert db.query(Job).count() == 1
```

#### Frontend Tests
- Jest for unit tests, Playwright for E2E
- Test files: `frontend/tests/` or co-located `.test.ts`

### Configuration Files

- **Backend env**: `backend/.env` (see `backend/.env.example` for required vars)
- **Frontend env**: `frontend/.env` (see `frontend/.env.example`)
- **LLM config**: `config/llm_config.json` (provider settings, rate limits)
- **Feature flags**: `config/feature_flags.json`

### Common Gotchas

1. **Database migrations**: Use Alembic. `alembic revision --autogenerate -m "message"` then `alembic upgrade head`
2. **Celery must be running** for background jobs (job scraping, AI generation). Docker Compose handles this.
3. **ChromaDB for vector embeddings**: Required for job similarity matching. Auto-initialized in `backend/app/services/vector_store_service.py`
4. **Frontend authentication**: Currently disabled by default (`requiresAuth: false` in API client). If enabling, set `NEXT_PUBLIC_API_URL` correctly.
5. **CORS**: If frontend can't reach backend, check `CORS_ORIGINS` in backend config matches frontend URL.

## Key Files to Reference

- **Backend entry**: `backend/app/main.py`
- **Backend config**: `backend/app/core/config.py` + `backend/app/core/unified_config.py`
- **Database setup**: `backend/app/core/database.py`
- **Service example**: `backend/app/services/job_service.py`
- **Celery config**: `backend/app/celery.py`
- **Frontend entry**: `frontend/src/app/layout.tsx` + `frontend/src/app/page.tsx`
- **API client**: `frontend/src/lib/api/client.ts`
- **Docker setup**: `docker-compose.yml`

## Quick Debugging

```bash
# Check service health
curl http://localhost:8000/health        # Backend health
curl http://localhost:3000/api/health    # Frontend health

# View logs
docker-compose logs -f backend    # Backend logs
docker-compose logs -f celery     # Celery worker logs
docker-compose logs -f frontend   # Frontend logs

# Database access
docker-compose exec postgres psql -U postgres -d career_copilot

# Redis access  
docker-compose exec redis redis-cli
```

## Production Deployment

- Docker-based deployment (see `deployment/docker/`)
- Nginx as reverse proxy (`deployment/nginx/`)
- CI/CD via GitHub Actions (`.github/workflows/`)
- Health checks: `/health` endpoint for backend
- Monitoring: Prometheus + Grafana (configs in `monitoring/`)

---

**When in doubt**: Check README.md first, then relevant service files. Follow the Service Layer pattern religiously.
