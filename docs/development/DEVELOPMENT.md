# Development Guide

## Getting Started

This guide will help you set up your development environment and start contributing to Career Copilot.

## Prerequisites

### Required Software

- Python 3.11 or higher
- Node.js 18.0 or higher
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)
- Git
- Docker & Docker Compose (optional but recommended)

### Recommended Tools

- **IDE**: VS Code, PyCharm, or WebStorm
- **API Testing**: Postman or Insomnia
- **Database Client**: pgAdmin, DBeaver, or TablePlus
- **Redis Client**: RedisInsight or redis-cli

## Development Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot
```

### 2. Backend Development Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Set up database
createdb career_copilot  # or use Docker

# Run migrations
alembic upgrade head

# Create test user
python scripts/create_test_user.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Development Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

### 4. Background Services

```bash
# Terminal 1: Celery Worker
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=debug

# Terminal 2: Celery Beat (Scheduler)
cd backend
source venv/bin/activate
celery -A app.core.celery_app beat --loglevel=debug
```

### 5. Using Docker for Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Run migrations in Docker
docker-compose exec backend alembic upgrade head

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U postgres -d career_copilot
```

## Project Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry
│   │
│   ├── api/v1/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── jobs.py            # Job endpoints
│   │   ├── applications.py    # Application endpoints
│   │   ├── users.py           # User endpoints
│   │   └── ...
│   │
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration
│   │   ├── security.py        # Security utilities
│   │   ├── database.py        # Database connection
│   │   └── celery_app.py      # Celery configuration
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── application.py
│   │   └── ...
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── user.py
│   │   ├── job.py
│   │   └── ...
│   │
│   ├── services/               # Business logic
│   │   ├── job_service.py
│   │   ├── ai_service.py
│   │   ├── scraping_service.py
│   │   └── ...
│   │
│   └── utils/                  # Helper functions
│       ├── validators.py
│       ├── formatters.py
│       └── ...
│
├── alembic/                    # Database migrations
├── tests/                      # Test suite
└── requirements.txt            # Python dependencies
```

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   ├── (auth)/            # Auth routes
│   │   ├── (dashboard)/       # Dashboard routes
│   │   ├── jobs/              # Job routes
│   │   └── applications/      # Application routes
│   │
│   ├── components/             # React components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── forms/             # Form components
│   │   ├── tables/            # Table components
│   │   ├── layouts/           # Layout components
│   │   └── ...
│   │
│   ├── lib/                    # Utilities
│   │   ├── api.ts             # API client
│   │   ├── utils.ts           # Helper functions
│   │   ├── hooks.ts           # Custom hooks
│   │   └── ...
│   │
│   └── types/                  # TypeScript types
│       ├── job.ts
│       ├── user.ts
│       └── ...
│
├── public/                     # Static assets
└── package.json                # Node dependencies
```

## Development Workflow

### 1. Creating a New Feature

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes...

# Run tests
pytest  # Backend
npm test  # Frontend

# Lint code
ruff check .  # Backend
npm run lint  # Frontend

# Format code
ruff format .  # Backend
npm run format  # Frontend

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
```

### 2. Adding a New API Endpoint

**Backend** (`backend/app/api/v1/example.py`):

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.example import ExampleCreate, ExampleResponse
from app.services.example_service import ExampleService

router = APIRouter()

@router.post("/examples", response_model=ExampleResponse)
def create_example(
    example: ExampleCreate,
    db: Session = Depends(get_db)
):
    service = ExampleService(db)
    return service.create(example)
```

**Frontend** (`frontend/src/lib/api.ts`):

```typescript
export async function createExample(data: ExampleCreate): Promise<Example> {
  const response = await fetch(`${API_URL}/api/v1/examples`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(data)
  });
  return response.json();
}
```

### 3. Adding a Database Model

**Create Model** (`backend/app/models/example.py`):

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Example(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Create Migration**:

```bash
cd backend
alembic revision --autogenerate -m "Add examples table"
alembic upgrade head
```

**Create Schema** (`backend/app/schemas/example.py`):

```python
from pydantic import BaseModel
from datetime import datetime

class ExampleBase(BaseModel):
    name: str

class ExampleCreate(ExampleBase):
    pass

class ExampleResponse(ExampleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 4. Adding a Frontend Component

```typescript
// frontend/src/components/example/Example.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';

interface ExampleProps {
  title: string;
  onSave: (data: any) => void;
}

export function Example({ title, onSave }: ExampleProps) {
  const [value, setValue] = useState('');
  
  const handleSubmit = () => {
    onSave({ value });
  };
  
  return (
    <div>
      <h2>{title}</h2>
      <input 
        value={value} 
        onChange={(e) => setValue(e.target.value)} 
      />
      <Button onClick={handleSubmit}>Save</Button>
    </div>
  );
}
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_jobs.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_jobs.py::test_create_job

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e
```

### Writing Tests

**Backend Test Example**:

```python
# tests/test_jobs.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_job():
    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Software Engineer",
            "company": "TechCorp",
            "location": "Berlin"
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Software Engineer"
```

**Frontend Test Example**:

```typescript
// tests/components/Example.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Example } from '@/components/example/Example';

describe('Example Component', () => {
  it('renders title', () => {
    render(<Example title="Test" onSave={() => {}} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
  
  it('calls onSave when button clicked', () => {
    const onSave = jest.fn();
    render(<Example title="Test" onSave={onSave} />);
    
    const button = screen.getByText('Save');
    fireEvent.click(button);
    
    expect(onSave).toHaveBeenCalled();
  });
});
```

## Code Style & Linting

### Backend (Python)

```bash
# Lint with ruff
ruff check .

# Format code
ruff format .

# Type checking with mypy
mypy app/
```

### Frontend (TypeScript)

```bash
# Lint
npm run lint

# Fix linting issues
npm run lint:fix

# Type check
npm run type-check

# Format with Prettier
npm run format
```

## Debugging

### Backend Debugging

**VS Code** (`launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

**Print Debugging**:

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Frontend Debugging

**Browser DevTools**:
- Use React DevTools extension
- Check Network tab for API calls
- Use Console for logging

**VS Code Debugging**:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug server-side",
      "type": "node-terminal",
      "request": "launch",
      "command": "npm run dev"
    }
  ]
}
```

## Database Management

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current
```

### Database Tools

```bash
# Connect to database
psql -h localhost -U postgres -d career_copilot

# Backup database
pg_dump -U postgres career_copilot > backup.sql

# Restore database
psql -U postgres career_copilot < backup.sql

# Reset database (CAUTION: destroys all data)
dropdb career_copilot
createdb career_copilot
alembic upgrade head
```

## Performance Profiling

### Backend

```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### Frontend

```bash
# Build production bundle
npm run build

# Analyze bundle size
npm run analyze
```

## Useful Commands

### Backend

```bash
# Start backend
uvicorn app.main:app --reload

# Start with specific port
uvicorn app.main:app --reload --port 8001

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Start Celery beat
celery -A app.core.celery_app beat --loglevel=info

# Purge Celery tasks
celery -A app.core.celery_app purge
```

### Frontend

```bash
# Start dev server
npm run dev

# Build production
npm run build

# Start production server
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

### Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service]

# Rebuild specific service
docker-compose up -d --build backend

# Execute command in container
docker-compose exec backend bash
```

## Best Practices

### Code Organization

- Keep files focused and single-purpose
- Use meaningful names for functions and variables
- Document complex logic with comments
- Follow DRY (Don't Repeat Yourself) principle
- Write modular, reusable code

### Error Handling

```python
# Backend
from fastapi import HTTPException

@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
```

```typescript
// Frontend
async function fetchJob(id: number) {
  try {
    const response = await fetch(`/api/v1/jobs/${id}`);
    if (!response.ok) {
      throw new Error('Job not found');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching job:', error);
    throw error;
  }
}
```

### Security

- Never commit sensitive data (use .env files)
- Validate all user input
- Use parameterized queries (SQLAlchemy ORM)
- Implement rate limiting
- Use HTTPS in production
- Keep dependencies updated

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## Getting Help

- Check [Troubleshooting Guide](../troubleshooting/COMMON_ISSUES.md)
- Review [API Documentation](../api/API.md)
- Open an issue on [GitHub](https://github.com/moatasim-KT/career-copilot/issues)
- Contact: <moatasimfarooque@gmail.com>

## Next Steps

- [API Documentation](../api/API.md) - Learn the API
- [Architecture](../architecture/ARCHITECTURE.md) - Understand the system
- [Deployment](../deployment/DEPLOYMENT.md) - Deploy to production
- [Contributing](../../frontend/CONTRIBUTING.md) - Contribution guidelines
