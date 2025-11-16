# Local Development Setup

**Quick Links**: [[README.md]] | [[PROJECT_STATUS.md]] | [[docs/index.md]] | [[CONTRIBUTING.md]]

**Detailed Guides**:
- [[docs/setup/INSTALLATION.md]] - Complete installation guide
- [[docs/setup/CONFIGURATION.md]] - Configuration details
- [[docs/development/DEVELOPMENT.md]] - Development workflow
- [[docs/troubleshooting/COMMON_ISSUES.md]] - Troubleshooting guide

**Component Guides**:
- [[backend/README.md]] - Backend development
- [[frontend/README.md]] - Frontend development
- [[backend/tests/TESTING_NOTES.md]] - Testing guide

## Quick Start

Get Career Copilot running locally in 3 steps:

```bash
# 1. Start services
docker-compose up -d

# 2. Run migrations
docker-compose exec backend alembic upgrade head

# 3. Access application
open http://localhost:3000  # Frontend
open http://localhost:8000/docs  # API docs
```

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

## Project Structure

```
career-copilot/
├── [[backend/]]                    # FastAPI backend
│   ├── [[backend/app/]]           # Application code
│   │   ├── [[backend/app/api/]]   # API routes (v1 endpoints)
│   │   ├── [[backend/app/core/]]  # Core config & database
│   │   ├── [[backend/app/models/]] # SQLAlchemy models
│   │   ├── [[backend/app/services/]] # Business logic
│   │   └── [[backend/app/tasks/]]  # Celery background tasks
│   ├── [[backend/tests/]]         # Test suite
│   │   ├── [[backend/tests/TESTING_NOTES.md]] # Testing documentation
│   │   └── [[backend/tests/conftest.py]] # Pytest fixtures
│   ├── [[backend/.env.example]]   # Environment template
│   └── [[backend/alembic/]]       # Database migrations
├── [[frontend/]]                   # Next.js 15 frontend
│   ├── [[frontend/src/app/]]      # App router pages
│   ├── [[frontend/src/components/]] # React components
│   └── [[frontend/src/lib/]]      # Utilities & API client
├── [[docker-compose.yml]]         # Local development stack
├── [[Makefile]]                   # Development commands
└── [[config/]]                    # Configuration files
    ├── [[config/llm_config.json]] # LLM provider settings
    └── [[config/feature_flags.json]] # Feature toggles
```

## Configuration

### 1. Backend Environment

Copy and configure [[backend/.env.example]]:

```bash
cd backend
cp .env.example .env
```

**Required variables in [[backend/.env]]**:

```bash
# Database (matches [[docker-compose.yml]] postgres service)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot

# Redis (matches [[docker-compose.yml]] redis service)
REDIS_URL=redis://localhost:6379/0

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# LLM Provider (at least one required)
OPENAI_API_KEY=sk-...  # From https://platform.openai.com/api-keys
# Optional:
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...

# Slack Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# Monitoring (optional)
SENTRY_DSN=https://your-key@sentry.io/project
```

**LLM Configuration**: See [[config/llm_config.json]] for provider priorities and capabilities.

### 2. Frontend Environment

Copy and configure [[frontend/.env.example]]:

```bash
cd frontend
cp .env.example .env
```

**Required variables in [[frontend/.env]]**:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Docker Compose Services

The [[docker-compose.yml]] file defines 6 services:

### Core Services

**postgres** (Port 5432)
- Image: postgres:14-alpine
- Database initialization: [[backend/init.sql]]
- Data persists in `./data/postgres/`
- Health check: `pg_isready`

**redis** (Port 6379)
- Image: redis:7-alpine
- Used for: Celery broker, caching, WebSocket state
- Data persists in `./data/redis/`
- Health check: `redis-cli ping`

### Application Services

**backend** (Port 8000)
- Built from: [[deployment/docker/Dockerfile.backend]]
- Entry point: [[backend/app/main.py]] (FastAPI app)
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

**celery** (Background worker)
- Same image as backend
- Handles: Job scraping, AI generation, notifications
- Task definitions: [[backend/app/tasks/]]
- Configuration: [[backend/app/core/celery_app.py]]
- Command: `celery -A app.core.celery_app worker --loglevel=info --concurrency=2`

**celery-beat** (Scheduler)
- Same image as backend
- Scheduled tasks: Daily job scraping (4 AM UTC), morning briefings (8 AM)
- Schedule config: [[backend/app/core/celery_app.py]] (`beat_schedule`)

**frontend** (Port 3000)
- Built from: [[deployment/docker/Dockerfile.frontend]]
- Entry point: [[frontend/src/app/layout.tsx]]
- Command: `npm run dev`
- Access: http://localhost:3000

## Development Workflow

### Git Hooks & Linting Guardrails

Enable the shared pre-commit setup so Ruff (backend) and ESLint (frontend) run automatically before every commit:

```bash
pip install pre-commit
pre-commit install
cd frontend && npm install
```

- The root `.pre-commit-config.yaml` triggers Ruff format/lint passes across `backend/` and `scripts/`.
- A local hook shells into `frontend/` and runs `npm run lint:check -- --max-warnings=0`, so make sure your frontend dependencies are installed.
- You can run the entire suite on demand with `pre-commit run --all-files`.

### Starting Services

```bash
# Start all services
docker-compose up -d

# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery
```

### Database Migrations

Database schema is managed with Alembic in [[backend/alembic/]]:

```bash
# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Create new migration (after model changes)
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history
```

**Model files**: [[backend/app/models/]] (user.py, job.py, application.py, notification.py, etc.)

### Running Tests

Tests are in [[backend/tests/]]. See [[backend/tests/TESTING_NOTES.md]] for details.

```bash
# Using Makefile (defined in [[Makefile]])
make test-python          # Backend tests
make test-frontend        # Frontend tests
make test                 # All tests

# Using pytest directly
cd backend
pytest -v                                # All tests
pytest tests/unit/test_simple_async.py  # Specific test
pytest --cov=backend --cov-report=html  # With coverage

# Run tests in Docker
docker-compose exec backend pytest -v
```

**Test configuration**: [[backend/pytest.ini]], [[backend/tests/conftest.py]]

### Code Quality

Quality checks are defined in [[Makefile]]:

```bash
# Linting
make lint-python          # flake8, ruff
make lint-frontend        # ESLint

# Formatting
make format-python        # black, isort, ruff format
make format-frontend      # Prettier, ESLint fix

# Type checking
make type-check-python    # mypy
make type-check-frontend  # TypeScript

# Security scanning
make security            # bandit, safety

# All quality checks
make quality-check       # Run everything
make quality-fix         # Auto-fix issues
```

**Configuration files**:
- Python: [[config/ruff.toml]], [[backend/pyproject.toml]]
- Frontend: [[frontend/.eslintrc.json]], [[frontend/tsconfig.json]]

### Accessing Services

**Frontend**: http://localhost:3000
- Main app: [[frontend/src/app/page.tsx]]
- Dashboard: [[frontend/src/app/dashboard/page.tsx]]
- API client: [[frontend/src/lib/api/client.ts]]

**Backend API**: http://localhost:8000
- Interactive docs: http://localhost:8000/docs (OpenAPI)
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health
- API routes: [[backend/app/api/v1/]]

**Database**: localhost:5432
- User: postgres
- Password: postgres (default from [[docker-compose.yml]])
- Database: career_copilot
- Connect: `psql postgresql://postgres:postgres@localhost:5432/career_copilot`

**Redis**: localhost:6379
- Connect: `redis-cli -h localhost -p 6379`
- Monitor commands: `redis-cli MONITOR`

### Monitoring Celery Tasks

```bash
# View active tasks
docker-compose exec celery celery -A app.core.celery_app inspect active

# View registered tasks
docker-compose exec celery celery -A app.core.celery_app inspect registered

# View scheduled tasks
docker-compose exec celery celery -A app.core.celery_app inspect scheduled

# Purge all tasks (⚠️ use carefully)
docker-compose exec celery celery -A app.core.celery_app purge
```

**Task implementations**: [[backend/app/tasks/job_ingestion_tasks.py]], [[backend/app/tasks/notification_tasks.py]]

## Service Architecture

Services communicate as follows:

```
┌─────────────┐     HTTP      ┌─────────────┐
│   Frontend  │──────────────►│   Backend   │
│  (Next.js)  │◄──────────────│  (FastAPI)  │
└─────────────┘   WebSocket   └──────┬──────┘
                                     │
              ┌──────────────────────┼──────────────────┐
              │                      │                  │
        ┌─────▼─────┐         ┌─────▼─────┐     ┌─────▼─────┐
        │ PostgreSQL│         │   Redis   │     │  Celery   │
        │           │         │  (Cache/  │     │  Workers  │
        │  Models:  │         │  Broker)  │     │           │
        │ [[backend/app/models/]]│    └───────────┘     │  Tasks:   │
        └───────────┘                                   │ [[backend/app/tasks/]] │
                                                        └───────────┘
```

**Key services**:
- Job scraping: [[backend/app/services/scraping/]]
- Job deduplication: [[backend/app/services/job_deduplication_service.py]]
- LLM integration: [[backend/app/services/llm_service.py]]
- Notifications: [[backend/app/services/notification_service.py]]
- WebSocket: [[backend/app/core/websocket_manager.py]]

## Common Tasks

### Creating a Test User

```bash
# Via Docker
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
user = User(
    username='testuser',
    email='test@example.com',
    hashed_password=get_password_hash('testpass123'),
    is_admin=False
)
db.add(user)
db.commit()
print(f'Created user: {user.email}')
"
```

**User model**: [[backend/app/models/user.py]]
**Auth routes**: [[backend/app/api/v1/auth.py]]

### Triggering Background Jobs

```bash
# Trigger job scraping manually
docker-compose exec celery python -c "
from app.tasks.job_ingestion_tasks import ingest_jobs
result = ingest_jobs.delay([1])  # user_id=1
print(f'Task ID: {result.id}')
"

# Check task result
docker-compose exec celery python -c "
from celery.result import AsyncResult
from app.core.celery_app import celery_app
result = AsyncResult('task-id-here', app=celery_app)
print(result.status)
"
```

**Job ingestion**: [[backend/app/tasks/job_ingestion_tasks.py]]
**Celery config**: [[backend/app/core/celery_app.py]]

### Viewing Application Logs

```bash
# Backend logs
tail -f data/logs/backend/app.log

# Celery logs
tail -f data/logs/celery/celery.log

# PostgreSQL logs
docker-compose logs postgres | tail -50

# Search for errors
docker-compose logs | grep ERROR
```

**Logging config**: [[backend/app/core/logging.py]]

### Database Operations

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d career_copilot

# Common queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM jobs;
SELECT COUNT(*) FROM applications;

# Backup database
docker-compose exec postgres pg_dump -U postgres career_copilot > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U postgres career_copilot
```

**Database config**: [[backend/app/core/database.py]]
**Init script**: [[backend/init.sql]]

## Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs backend

# Common issues:
# 1. Port already in use: Change ports in [[docker-compose.yml]]
# 2. Database not ready: Wait for health check to pass
# 3. Missing .env: Check [[backend/.env.example]]
```

### Database Connection Errors

```bash
# Test connection from backend
docker-compose exec backend python -c "
from app.core.database import engine
try:
    engine.connect()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"

# Check DATABASE_URL matches [[docker-compose.yml]]
grep DATABASE_URL backend/.env
```

**Database manager**: [[backend/app/core/database.py]] (DatabaseManager class)

### Celery Tasks Not Running

```bash
# Check worker is running
docker-compose ps celery

# View worker logs
docker-compose logs celery

# Verify broker connection
docker-compose exec celery python -c "
from app.core.celery_app import celery_app
print(f'Broker: {celery_app.conf.broker_url}')
"
```

**Task registration**: All tasks in [[backend/app/tasks/]] are auto-discovered

### Frontend Build Errors

```bash
# Clear Next.js cache
docker-compose exec frontend rm -rf .next

# Reinstall dependencies
docker-compose exec frontend npm install

# Check Node version (requires 18+)
docker-compose exec frontend node --version
```

**Frontend config**: [[frontend/next.config.js]], [[frontend/tsconfig.json]]

### WebSocket Connection Issues

```bash
# Test WebSocket endpoint
docker-compose exec backend python -c "
from fastapi.testclient import TestClient
from app.main import app
# WebSocket routes defined in [[backend/app/api/v1/websocket.py]]
"

# Check CORS settings in [[backend/app/main.py]]
```

**WebSocket manager**: [[backend/app/core/websocket_manager.py]]
**WebSocket routes**: [[backend/app/api/v1/websocket.py]]

## Stopping & Cleanup

```bash
# Stop all services (preserves data)
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v

# Remove old images
docker system prune -a

# Clean build cache
docker builder prune
```

## Development Tips

1. **Hot Reload**: Both frontend and backend support hot reload
   - Backend: uvicorn `--reload` flag in [[docker-compose.yml]]
   - Frontend: Next.js dev server

2. **API Client**: Frontend uses unified API client in [[frontend/src/lib/api/client.ts]]
   - Handles auth tokens automatically
   - Provides TypeScript types

3. **Service Layer**: Business logic in [[backend/app/services/]]
   - Keep routes thin, logic in services
   - See [[.github/copilot-instructions.md]] for patterns

4. **Configuration**: 
   - Feature flags: [[config/feature_flags.json]]
   - LLM providers: [[config/llm_config.json]]
   - App config: [[config/application.yaml]]

5. **Testing**: 
   - Write tests in [[backend/tests/]]
   - Use fixtures from [[backend/tests/conftest.py]]
   - See [[backend/tests/TESTING_NOTES.md]] for async testing notes

## Next Steps

- Review [[README.md]] for feature overview
- Check [[.github/copilot-instructions.md]] for coding patterns
- Read [[backend/app/core/README.md]] for core architecture (if exists)
- Browse [[backend/app/api/v1/]] for available endpoints

## Support

- GitHub Issues: https://github.com/moatasim-KT/career-copilot/issues
- Project Board: Check [[TODO.md]] for active work
