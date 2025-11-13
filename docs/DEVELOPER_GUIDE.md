# Career Copilot Developer Guide

This guide provides technical documentation for developers working on Career Copilot.

## Related Documents

- [[../README.md]] - Project overview and setup
- [[../TODO.md]] - Current development tasks
- [[../PLAN.md]] - Implementation plan
- [[../CONTRIBUTING.md]] - Contribution guidelines
- [[USER_GUIDE.md]] - User documentation
- [[FRONTEND_QUICK_START.md]] - Frontend development setup

## Table of Contents

- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Coding Conventions](#coding-conventions)
- [Component Patterns](#component-patterns)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Testing Guidelines](#testing-guidelines)
- [Performance Optimization](#performance-optimization)
- [Deployment](#deployment)

## Project Structure

```
career-copilot/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   │   ├── endpoints/     # Route handlers
│   │   │   └── deps.py        # Dependencies
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Settings
│   │   │   ├── security.py    # Auth & security
│   │   │   └── celery_app.py  # Celery configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # Data access layer
│   │   ├── utils/             # Utility functions
│   │   └── main.py            # Application entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   │   ├── (auth)/        # Auth routes group
│   │   │   ├── (dashboard)/   # Dashboard routes group
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── page.tsx       # Home page
│   │   │   └── globals.css    # Global styles & design tokens
│   │   ├── components/        # React components
│   │   │   ├── ui/            # Base UI components
│   │   │   ├── forms/         # Form components
│   │   │   ├── pages/         # Page-level components
│   │   │   ├── layout/        # Layout components
│   │   │   ├── charts/        # Chart components
│   │   │   └── features/      # Feature-specific components
│   │   ├── lib/               # Utilities & helpers
│   │   │   ├── api/           # API client
│   │   │   ├── utils/         # Utility functions
│   │   │   └── hooks/         # Custom hooks
│   │   ├── hooks/             # Additional hooks
│   │   ├── contexts/          # React Context providers
│   │   ├── stores/            # Zustand stores
│   │   └── types/             # TypeScript types
│   ├── public/                # Static assets
│   ├── tests/                 # Frontend tests
│   └── package.json           # Node dependencies
│
├── docs/                       # Documentation
├── config/                     # Configuration files
├── deployment/                 # Deployment configs
├── scripts/                    # Utility scripts
└── docker-compose.yml          # Docker Compose configuration
```

### Key Directories

#### Backend (`backend/app/`)

- **api/v1/**: API endpoints organized by resource
- **core/**: Core configuration, security, and utilities
- **models/**: SQLAlchemy ORM models (database tables)
- **schemas/**: Pydantic schemas for request/response validation
- **services/**: Business logic layer
- **repositories/**: Data access layer (database queries)
- **utils/**: Shared utility functions

#### Frontend (`frontend/src/`)

- **app/**: Next.js App Router pages and layouts
- **components/**: React components organized by type
- **lib/**: Utilities, API client, and custom hooks
- **hooks/**: Custom React hooks
- **contexts/**: React Context providers for global state
- **stores/**: Zustand stores for client-side state
- **types/**: TypeScript type definitions

## Architecture Overview

### Backend Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  ┌───────────────────────────────┐  │
│  │      API Endpoints (v1)       │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │      Services Layer           │  │
│  │  (Business Logic)             │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │    Repositories Layer         │  │
│  │  (Data Access)                │  │
│  └───────────┬───────────────────┘  │
└──────────────┼───────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  PostgreSQL │  │    Redis    │
└─────────────┘  └─────────────┘
```

**Layers:**

1. **API Layer** (`api/v1/endpoints/`)
   - Handles HTTP requests/responses
   - Request validation with Pydantic
   - Authentication and authorization
   - Error handling

2. **Service Layer** (`services/`)
   - Business logic
   - Orchestrates multiple repositories
   - External API calls (AI services, job boards)
   - Background task scheduling

3. **Repository Layer** (`repositories/`)
   - Database queries
   - CRUD operations
   - Query optimization
   - Transaction management

4. **Model Layer** (`models/`)
   - SQLAlchemy ORM models
   - Database schema definition
   - Relationships and constraints

### Frontend Architecture

```
┌─────────────────────────────────────┐
│         Next.js Application         │
│  ┌───────────────────────────────┐  │
│  │      App Router (Pages)       │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │    Page Components            │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │   Feature Components          │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │      UI Components            │  │
│  └───────────────────────────────┘  │
│                                      │
│  ┌───────────────────────────────┐  │
│  │    State Management           │  │
│  │  ┌─────────┐  ┌────────────┐  │  │
│  │  │ TanStack│  │  Zustand   │  │  │
│  │  │  Query  │  │  Stores    │  │  │
│  │  └─────────┘  └────────────┘  │  │
│  └───────────────────────────────┘  │
│                                      │
│  ┌───────────────────────────────┐  │
│  │       API Client              │  │
│  └───────────┬───────────────────┘  │
└──────────────┼───────────────────────┘
               │
               ▼
        ┌─────────────┐
        │   Backend   │
        │     API     │
        └─────────────┘
```

**Layers:**

1. **App Router** (`app/`)
   - Route definitions
   - Layouts and templates
   - Server components
   - Metadata and SEO

2. **Page Components** (`components/pages/`)
   - Page-level logic
   - Data fetching
   - Layout composition

3. **Feature Components** (`components/features/`)
   - Feature-specific components
   - Complex interactions
   - Business logic

4. **UI Components** (`components/ui/`)
   - Reusable UI elements
   - Design system components
   - Styled with Tailwind CSS

5. **State Management**
   - **TanStack Query**: Server state, caching, mutations
   - **Zustand**: Client-side state
   - **React Context**: Theme, auth, global settings

6. **API Client** (`lib/api/`)
   - HTTP client (Axios)
   - Request/response interceptors
   - Error handling
   - Type-safe endpoints

### Consolidated Service Architecture

Career Copilot uses a **singleton service pattern** for all production services to ensure consistent state management, prevent duplicate instances, and optimize resource usage.

#### Key Architectural Principles

1. **Single Responsibility**: Each service handles one domain (analytics, cache, notifications, etc.)
2. **Singleton Pattern**: Services are instantiated once and reused throughout the application lifecycle
3. **Dependency Injection**: Services receive dependencies (database sessions, configs) via constructor
4. **Async-First**: All I/O operations use async/await for optimal performance
5. **Unified Configuration**: Single source of truth via `UnifiedSettings` class

#### Service Lifecycle

```python
# Backend service initialization (app/main.py)
from app.services.analytics_service import AnalyticsService
from app.services.cache_service import CacheService
from app.core.database import get_db

# Services are initialized on application startup
@app.on_event("startup")
async def startup_event():
    # Initialize singleton services
    cache_service = CacheService.get_instance()
    await cache_service.initialize()
    
    # Services auto-connect to shared resources
    logger.info("All services initialized")

# Usage in endpoints
@router.get("/analytics/trends")
async def get_trends(db: Session = Depends(get_db)):
    # Service instances are accessed via get_instance()
    analytics_service = AnalyticsService(db)
    return await analytics_service.calculate_application_trends(user_id=1, days=30)
```

#### Core Services

**1. AnalyticsService** (`backend/app/services/analytics_service.py`)
- Comprehensive analytics calculations
- Trend analysis (daily, weekly, monthly)
- Skill gap analysis with caching
- Performance benchmarking
- Report generation

```python
# Key methods
async def calculate_application_trends(user_id: int, days: int = 30)
async def analyze_skill_gaps(user_id: int, limit: int = 100)
async def generate_performance_benchmarks(user_id: int)
```

**2. CacheService** (`backend/app/services/cache_service.py`)
- Redis-based caching with fallback to in-memory
- Automatic serialization/deserialization
- TTL management
- Cache invalidation patterns

```python
# Usage
cache = CacheService.get_instance()
await cache.set("user:123:profile", user_data, ttl=3600)
cached_data = await cache.get("user:123:profile")
```

**3. NotificationService** (`backend/app/services/notification_service.py`)
- Real-time notifications via WebSocket
- Persistent notification storage
- Multi-channel support (WebSocket, email, Slack)
- Offline queue management

```python
# Send notification
await notification_service.create_and_send_notification(
    user_id=123,
    title="New Job Match",
    message="Found 5 new matching jobs",
    notification_type="job_match"
)
```

**4. LLMService** (`backend/app/services/llm_service.py`)
- Multi-provider LLM integration (OpenAI, Groq, Anthropic)
- Intelligent fallback and rate limiting
- Cost optimization and provider routing
- Prompt template management

```python
# Generate AI content
response = await llm_service.generate_completion(
    prompt="Analyze this job description...",
    task_category="analysis",
    max_tokens=2000
)
```

**5. WebSocketNotificationService** (`backend/app/services/websocket_notifications.py`)
- Manages WebSocket connections
- Heartbeat monitoring
- Connection pooling
- Channel-based broadcasting

#### Database Management

Career Copilot uses **dual database engine approach**:

```python
# backend/app/core/database.py
class DatabaseManager:
    """Manages both sync and async database engines"""
    
    # Synchronous engine (for Celery, scripts)
    sync_engine = create_engine(DATABASE_URL)
    
    # Async engine (for FastAPI endpoints)
    async_engine = create_async_engine(DATABASE_URL_ASYNC)

# Dependency injection for sync operations
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency injection for async operations  
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**Migration Strategy:**
- Alembic for schema migrations
- Both sync and async SQLAlchemy support
- Performance indexes for analytics queries
- Composite indexes for complex queries

#### Unified Configuration System

All configuration is managed through `UnifiedSettings`:

```python
# backend/app/core/unified_config.py
from app.core.config import get_settings

settings = get_settings()

# Access any configuration
api_key = settings.openai_api_key
db_url = settings.database_url
redis_url = settings.redis_url

# Environment-specific overrides
if settings.environment == "production":
    # Production-specific config
    pass
```

Configuration sources (in priority order):
1. Environment variables (`.env` file)
2. Config files (`config/application.yaml`)
3. Default values in `UnifiedSettings`

#### Async Patterns

**Recommended async patterns:**

```python
# ✅ CORRECT: Async database operations
async def get_user_stats(user_id: int, db: AsyncSession):
    result = await db.execute(
        select(Application).where(Application.user_id == user_id)
    )
    return result.scalars().all()

# ✅ CORRECT: Parallel async operations
async def get_dashboard_data(user_id: int, db: AsyncSession):
    # Run multiple queries in parallel
    results = await asyncio.gather(
        get_user_stats(user_id, db),
        get_recent_jobs(user_id, db),
        get_notifications(user_id, db)
    )
    return {
        "stats": results[0],
        "jobs": results[1],
        "notifications": results[2]
    }

# ❌ WRONG: Mixing sync and async
def bad_example(db: Session):
    # Don't call async functions from sync code without proper handling
    result = get_user_stats(user_id, db)  # This will fail!
```

#### Celery Background Tasks

All long-running operations use Celery:

```python
# backend/app/tasks/job_ingestion_tasks.py
from celery import shared_task

@shared_task(bind=True, name="app.tasks.job_ingestion_tasks.ingest_jobs", max_retries=3)
def ingest_jobs(self, user_ids: List[int] = None):
    """Background job scraping task"""
    try:
        # Long-running job scraping logic
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# Trigger from endpoint
from app.celery import celery_app
result = celery_app.send_task("app.tasks.job_ingestion_tasks.ingest_jobs", args=[[1, 2, 3]])
```

**Scheduled tasks** (defined in `backend/app/celery.py`):
- Daily job scraping at 4:00 AM UTC
- Weekly analytics report generation
- Periodic cache cleanup
- Database backup tasks

#### Service Testing Patterns

**Unit tests for services:**

```python
# backend/tests/test_analytics_service.py
import pytest
from app.services.analytics_service import AnalyticsService

@pytest.mark.asyncio
async def test_skill_gap_analysis(async_db: AsyncSession, test_user: User):
    service = AnalyticsService(async_db)
    
    result = await service.analyze_skill_gaps(
        user_id=test_user.id,
        limit=10
    )
    
    assert "skill_gaps" in result
    assert "recommendations" in result
    assert result["total_jobs_analyzed"] >= 0
```

**Integration tests:**

```python
# backend/tests/test_integration.py
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_analytics_endpoint_integration(client: AsyncClient):
    response = await client.get("/api/v1/analytics/trends?days=30")
    
    assert response.status_code == 200
    data = response.json()
    assert "daily_trends" in data
    assert "overall_trend" in data
```


## Coding Conventions

### Python (Backend)

#### Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

- **Line Length**: 100 characters maximum
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Organized in groups (standard library, third-party, local)

#### Naming Conventions

```python
# Classes: PascalCase
class ApplicationService:
    pass

# Functions/methods: snake_case
def get_user_applications(user_id: int) -> List[Application]:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_TIMEOUT = 30

# Private methods: _leading_underscore
def _validate_data(self, data: dict) -> bool:
    pass

# Module-level private: _leading_underscore
_internal_cache = {}
```

#### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import Optional, List, Dict, Any
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationUpdate

def create_application(
    db: Session,
    application_in: ApplicationCreate,
    user_id: int
) -> Application:
    """
    Create a new application.
    
    Args:
        db: Database session
        application_in: Application data
        user_id: User ID
        
    Returns:
        Created application object
        
    Raises:
        ValueError: If validation fails
    """
    # Implementation
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def process_application(
    application_id: int,
    status: str,
    notes: Optional[str] = None
) -> Application:
    """
    Process an application and update its status.
    
    This function updates the application status, sends notifications,
    and logs the change in the application timeline.
    
    Args:
        application_id: The ID of the application to process
        status: New status (applied, screening, interviewing, etc.)
        notes: Optional notes about the status change
        
    Returns:
        The updated application object
        
    Raises:
        NotFoundError: If application doesn't exist
        ValueError: If status is invalid
        
    Example:
        >>> app = process_application(123, "interviewing", "Phone screen scheduled")
        >>> print(app.status)
        'interviewing'
    """
    # Implementation
    pass
```

### TypeScript/React (Frontend)

#### Style Guide

- **Line Length**: 100 characters maximum
- **Indentation**: 2 spaces
- **Quotes**: Single quotes for strings, double for JSX attributes
- **Semicolons**: Required

#### Naming Conventions

```typescript
// Components: PascalCase
export function Button() {}
export function JobCard() {}

// Hooks: camelCase with "use" prefix
export function useAuth() {}
export function useJobs() {}

// Utilities: camelCase
export function formatDate() {}
export function validateEmail() {}

// Types/Interfaces: PascalCase
export interface User {}
export type JobStatus = 'active' | 'closed';

// Constants: UPPER_SNAKE_CASE
export const API_URL = 'http://localhost:8000';
export const MAX_RETRIES = 3;

// Private functions: _leading_underscore (rare in TS)
function _internalHelper() {}
```

#### Component Structure

```typescript
import React from 'react';
import { cn } from '@/lib/utils';

// 1. Type definitions
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
}

// 2. Component definition
export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  children,
  className
}: ButtonProps) {
  // 3. Hooks
  const [isLoading, setIsLoading] = React.useState(false);
  
  // 4. Event handlers
  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };
  
  // 5. Effects
  React.useEffect(() => {
    // Side effects
  }, []);
  
  // 6. Render
  return (
    <button
      className={cn(
        'rounded-lg font-medium transition-colors',
        variant === 'primary' && 'bg-primary text-white',
        size === 'md' && 'px-4 py-2',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled}
      onClick={handleClick}
    >
      {children}
    </button>
  );
}
```

#### Import Order

```typescript
// 1. React & Next.js
import React from 'react';
import { useRouter } from 'next/navigation';

// 2. External libraries
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';

// 3. Internal components
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 4. Hooks & utilities
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

// 5. Types
import type { User } from '@/types';

// 6. Styles (if any)
import styles from './Component.module.css';
```

## Component Patterns

### Design System Components

All UI components follow the Button2/Card2 pattern:

```typescript
// components/ui/Button2.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-white hover:bg-primary-600',
        secondary: 'bg-secondary text-white hover:bg-secondary-600',
        outline: 'border-2 border-primary text-primary hover:bg-primary-50',
        ghost: 'hover:bg-neutral-100',
        danger: 'bg-red-600 text-white hover:bg-red-700',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface Button2Props
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export function Button2({
  className,
  variant,
  size,
  isLoading,
  disabled,
  children,
  ...props
}: Button2Props) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? 'Loading...' : children}
    </button>
  );
}
```

### Form Components

Use React Hook Form with Zod validation:

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const applicationSchema = z.object({
  jobTitle: z.string().min(1, 'Job title is required'),
  company: z.string().min(1, 'Company is required'),
  status: z.enum(['applied', 'screening', 'interviewing', 'offer']),
  appliedDate: z.date(),
  notes: z.string().optional(),
});

type ApplicationFormData = z.infer<typeof applicationSchema>;

export function ApplicationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ApplicationFormData>({
    resolver: zodResolver(applicationSchema),
  });

  const onSubmit = async (data: ApplicationFormData) => {
    // Handle form submission
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input2
        label="Job Title"
        {...register('jobTitle')}
        error={errors.jobTitle?.message}
      />
      {/* More fields */}
      <Button2 type="submit" isLoading={isSubmitting}>
        Submit
      </Button2>
    </form>
  );
}
```

### Data Fetching Components

Use TanStack Query for server state:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsAPI } from '@/lib/api/endpoints/jobs';

export function JobsList() {
  const queryClient = useQueryClient();

  // Fetch jobs
  const { data: jobs, isLoading, error } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsAPI.getJobs(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Save job mutation
  const saveJobMutation = useMutation({
    mutationFn: (jobId: number) => jobsAPI.saveJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['saved-jobs'] });
    },
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div>
      {jobs?.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          onSave={() => saveJobMutation.mutate(job.id)}
        />
      ))}
    </div>
  );
}
```


## State Management

### Server State (TanStack Query)

Use TanStack Query for all server data:

```typescript
// lib/api/endpoints/applications.ts
export const applicationsAPI = {
  getApplications: () => apiClient.get<Application[]>('/applications'),
  getApplication: (id: number) => apiClient.get<Application>(`/applications/${id}`),
  createApplication: (data: ApplicationCreate) =>
    apiClient.post<Application>('/applications', data),
  updateApplication: (id: number, data: ApplicationUpdate) =>
    apiClient.patch<Application>(`/applications/${id}`, data),
  deleteApplication: (id: number) => apiClient.delete(`/applications/${id}`),
};

// hooks/useApplications.ts
export function useApplications() {
  return useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsAPI.getApplications(),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

export function useApplication(id: number) {
  return useQuery({
    queryKey: ['applications', id],
    queryFn: () => applicationsAPI.getApplication(id),
    enabled: !!id,
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ApplicationCreate) => applicationsAPI.createApplication(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}
```

### Client State (Zustand)

Use Zustand for client-side state:

```typescript
// stores/uiStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  density: 'comfortable' | 'compact';
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setDensity: (density: 'comfortable' | 'compact') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'system',
      density: 'comfortable',
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      setDensity: (density) => set({ density }),
    }),
    {
      name: 'ui-storage',
    }
  )
);

// Usage in components
function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <aside className={cn('sidebar', !sidebarOpen && 'hidden')}>
      {/* Sidebar content */}
    </aside>
  );
}
```

### Global Context

Use React Context for auth and theme:

```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '@/types';
import { authAPI } from '@/lib/api/endpoints/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load user on mount
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const user = await authAPI.getCurrentUser();
      setUser(user);
    } catch (error) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const { user, token } = await authAPI.login(email, password);
    localStorage.setItem('token', token);
    setUser(user);
  };

  const logout = async () => {
    await authAPI.logout();
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refreshUser: loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

## API Integration

### API Client Setup

```typescript
// lib/api/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError) => {
        this.handleError(error);
        return Promise.reject(error);
      }
    );
  }

  private handleError(error: AxiosError) {
    if (error.response) {
      const status = error.response.status;
      const message = (error.response.data as any)?.message || 'An error occurred';

      switch (status) {
        case 401:
          toast.error('Session expired. Please log in again.');
          // Redirect to login
          break;
        case 403:
          toast.error('You don\'t have permission for this action.');
          break;
        case 404:
          toast.error('Resource not found.');
          break;
        case 500:
          toast.error('Server error. Please try again later.');
          break;
        default:
          toast.error(message);
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
    }
  }

  async get<T>(url: string, config?: any): Promise<T> {
    return this.client.get(url, config);
  }

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    return this.client.post(url, data, config);
  }

  async patch<T>(url: string, data?: any, config?: any): Promise<T> {
    return this.client.patch(url, data, config);
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    return this.client.delete(url, config);
  }
}

export const apiClient = new APIClient();
```

### API Endpoints

```typescript
// lib/api/endpoints/jobs.ts
import { apiClient } from '../client';
import { Job, JobCreate, JobUpdate, JobFilters } from '@/types';

export const jobsAPI = {
  getJobs: (filters?: JobFilters) =>
    apiClient.get<Job[]>('/jobs', { params: filters }),

  getJob: (id: number) =>
    apiClient.get<Job>(`/jobs/${id}`),

  createJob: (data: JobCreate) =>
    apiClient.post<Job>('/jobs', data),

  updateJob: (id: number, data: JobUpdate) =>
    apiClient.patch<Job>(`/jobs/${id}`, data),

  deleteJob: (id: number) =>
    apiClient.delete(`/jobs/${id}`),

  saveJob: (id: number) =>
    apiClient.post(`/jobs/${id}/save`),

  unsaveJob: (id: number) =>
    apiClient.delete(`/jobs/${id}/save`),

  generateResume: (id: number) =>
    apiClient.post<{ resume: string }>(`/jobs/${id}/generate-resume`),

  generateCoverLetter: (id: number) =>
    apiClient.post<{ coverLetter: string }>(`/jobs/${id}/generate-cover-letter`),
};
```

## Testing Guidelines

### Backend Testing

#### Unit Tests

```python
# tests/test_services/test_application_service.py
import pytest
from app.services.application_service import ApplicationService
from app.schemas.application import ApplicationCreate

def test_create_application(db_session, test_user):
    """Test creating a new application."""
    service = ApplicationService(db_session)
    
    application_data = ApplicationCreate(
        job_title="Software Engineer",
        company="Tech Corp",
        status="applied",
        applied_date="2024-01-15"
    )
    
    application = service.create_application(
        user_id=test_user.id,
        application_in=application_data
    )
    
    assert application.id is not None
    assert application.job_title == "Software Engineer"
    assert application.company == "Tech Corp"
    assert application.status == "applied"
    assert application.user_id == test_user.id

def test_update_application_status(db_session, test_application):
    """Test updating application status."""
    service = ApplicationService(db_session)
    
    updated = service.update_status(
        application_id=test_application.id,
        status="interviewing",
        notes="Phone screen scheduled"
    )
    
    assert updated.status == "interviewing"
    assert "Phone screen scheduled" in updated.notes
```

#### Integration Tests

```python
# tests/test_api/test_applications.py
import pytest
from fastapi.testclient import TestClient

def test_create_application_endpoint(client: TestClient, auth_headers):
    """Test POST /api/v1/applications endpoint."""
    response = client.post(
        "/api/v1/applications",
        json={
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "status": "applied",
            "applied_date": "2024-01-15"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["job_title"] == "Software Engineer"
    assert data["company"] == "Tech Corp"
    assert "id" in data

def test_get_applications_endpoint(client: TestClient, auth_headers, test_applications):
    """Test GET /api/v1/applications endpoint."""
    response = client.get("/api/v1/applications", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
```

### Frontend Testing

#### Component Tests

```typescript
// components/ui/Button2.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button2 } from './Button2';

describe('Button2', () => {
  it('renders correctly', () => {
    render(<Button2>Click me</Button2>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button2 onClick={handleClick}>Click me</Button2>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button2 disabled>Click me</Button2>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });

  it('shows loading state', () => {
    render(<Button2 isLoading>Click me</Button2>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Button2 variant="primary">Button</Button2>);
    expect(screen.getByText('Button')).toHaveClass('bg-primary');

    rerender(<Button2 variant="secondary">Button</Button2>);
    expect(screen.getByText('Button')).toHaveClass('bg-secondary');
  });
});
```

#### E2E Tests

```typescript
// tests/e2e/applications.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Application Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('create new application', async ({ page }) => {
    await page.goto('/applications');
    await page.click('text=New Application');

    await page.fill('[name="jobTitle"]', 'Software Engineer');
    await page.fill('[name="company"]', 'Tech Corp');
    await page.selectOption('[name="status"]', 'applied');
    await page.fill('[name="appliedDate"]', '2024-01-15');

    await page.click('button[type="submit"]');

    await expect(page.locator('text=Application created successfully')).toBeVisible();
    await expect(page.locator('text=Software Engineer')).toBeVisible();
  });

  test('update application status', async ({ page }) => {
    await page.goto('/applications');
    await page.click('text=Software Engineer');

    await page.click('text=Change Status');
    await page.selectOption('[name="status"]', 'interviewing');
    await page.fill('[name="notes"]', 'Phone screen scheduled');
    await page.click('button:has-text("Save")');

    await expect(page.locator('text=Status updated successfully')).toBeVisible();
    await expect(page.locator('text=Interviewing')).toBeVisible();
  });
});
```


## Performance Optimization

### Code Splitting

```typescript
// Dynamic imports for heavy components
import dynamic from 'next/dynamic';

const ChartComponent = dynamic(() => import('./ChartComponent'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});

const AdvancedSearch = dynamic(() => import('./AdvancedSearch'), {
  loading: () => <Skeleton />,
});

// Use in component
export function Dashboard() {
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);

  return (
    <div>
      {showAdvancedSearch && <AdvancedSearch />}
      <ChartComponent data={data} />
    </div>
  );
}
```

### List Virtualization

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

export function VirtualJobList({ jobs }: { jobs: Job[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: jobs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Estimated row height
    overscan: 5, // Render 5 extra items above/below viewport
  });

  return (
    <div ref={parentRef} className="h-screen overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <JobCard job={jobs[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Image Optimization

```typescript
import Image from 'next/image';

export function JobCard({ job }: { job: Job }) {
  return (
    <div className="job-card">
      <Image
        src={job.companyLogo}
        alt={job.company}
        width={64}
        height={64}
        placeholder="blur"
        blurDataURL="data:image/png;base64,..."
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      />
      {/* Rest of card */}
    </div>
  );
}
```

### Caching Strategy

```typescript
// TanStack Query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

// Per-query configuration
export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsAPI.getJobs(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useApplications() {
  return useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsAPI.getApplications(),
    staleTime: 1 * 60 * 1000, // 1 minute (more frequent updates)
    refetchOnMount: true,
  });
}
```

### Optimistic Updates

```typescript
export function useUpdateApplicationStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      applicationsAPI.updateStatus(id, status),

    onMutate: async ({ id, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['applications'] });

      // Snapshot previous value
      const previousApplications = queryClient.getQueryData(['applications']);

      // Optimistically update
      queryClient.setQueryData(['applications'], (old: Application[]) =>
        old.map((app) => (app.id === id ? { ...app, status } : app))
      );

      return { previousApplications };
    },

    onError: (err, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['applications'], context?.previousApplications);
      toast.error('Failed to update status');
    },

    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}
```

## Deployment

### Environment Variables

#### Backend (.env)

```env
# Application
APP_NAME=Career Copilot
APP_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/career_copilot

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
CORS_ORIGINS=["http://localhost:3000","https://your-domain.com"]
```

#### Frontend (.env.local)

```env
# API
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com/ws

# Monitoring
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...
SENTRY_AUTH_TOKEN=...

# Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Feature Flags
NEXT_PUBLIC_ENABLE_WEBSOCKETS=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

### Build Process

#### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run tests
pytest

# Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend

```bash
# Install dependencies
npm install

# Type check
npm run type-check

# Lint
npm run lint

# Run tests
npm test

# Build for production
npm run build

# Start production server
npm start
```

### Docker Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm install
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm test
      
      - name: Build frontend
        run: |
          cd frontend
          npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to production
        run: |
          # Your deployment script here
          echo "Deploying to production..."
```

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## Getting Help

- **Documentation**: Check [docs/](.) directory
- **Issues**: [GitHub Issues](https://github.com/moatasim-KT/career-copilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/moatasim-KT/career-copilot/discussions)
- **Email**: moatasimfarooque@gmail.com

---

Happy coding! 🚀
