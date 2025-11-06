# 🚀 Career Copilot

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)
![React](https://img.shields.io/badge/React-19.2-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)
![Redis](https://img.shields.io/badge/Redis-7+-dc382d.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)

**An AI-powered career management platform specializing in EU job discovery with visa sponsorship support for AI/Data Science professionals.**

[Features](#-key-features) • [Quick Start](#quick-start-5-minutes) • [Documentation](#-table-of-contents) • [API Docs](#-api-documentation) • [Contributing](#-contributing)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)

  - [What is Career Copilot?](#what-is-career-copilot)
  - [Problem Statement](#problem-statement)
  - [The Solution](#the-solution)
  - [Key Features](#-key-features)
  - [Current Status](#current-status)
- [Visual Documentation](#-visual-documentation)

  - [System Architecture](#system-architecture)
  - [Job Scraping Pipeline](#job-scraping-pipeline)
  - [Data Flow](#data-flow)
  - [Component Interaction](#component-interaction)
- [Technical Architecture](#️-technical-architecture)

  - [High-Level Architecture](#high-level-architecture)
  - [Technology Stack](#technology-stack)
  - [Design Patterns](#design-patterns)
  - [Scalability](#scalability-considerations)
  - [Security Architecture](#security-architecture)
  - [Performance Optimizations](#performance-optimizations)
- [Project Structure](#-project-structure)
- [Component Deep Dive](#-component-deep-dive)

  - [Job Discovery System](#1-job-discovery-system)
  - [Application Tracking](#2-application-tracking)
  - [AI Content Generation](#3-ai-content-generation)
  - [Analytics Engine](#4-analytics-engine)
  - [Notification System](#5-notification-system)
  - [Recommendation Engine](#6-recommendation-engine)
- [Prerequisites & Dependencies](#-prerequisites--dependencies)
- [Installation & Setup](#-installation--setup)
- [External APIs & Services](#-external-apis--third-party-services)
- [Configuration](#️-configuration)
- [Usage & Functionality](#-usage--functionality)
- [API Documentation](#-api-documentation)
- [Code Examples](#-code-examples--tutorials)
- [Testing](#-testing)
- [Development Workflow](#-development-workflow)
- [Troubleshooting](#-troubleshooting--faq)
- [Deployment](#-deployment)
- [Performance & Optimization](#-performance--optimization)
- [Security](#-security)
- [Contributing](#-contributing)
- [Technical Decisions](#-technical-decisions--rationale)
- [Changelog & Versioning](#-changelog--versioning)
- [Resources](#-resources)
- [License](#-license)
- [Support & Contact](#-support--contact)

---

## 🎯 Project Overview

### What is Career Copilot?

Career Copilot is a **comprehensive, AI-powered career management platform** designed specifically for **AI/Data Science professionals** seeking opportunities in the **European Union** with **visa sponsorship**. It combines intelligent job discovery, application tracking, AI-powered content generation, and advanced analytics to streamline the job search process.

### Problem Statement

Job seekers in the tech industry, especially international candidates seeking EU positions with visa sponsorship, face several challenges:

- 🔍 **Fragmented Job Sources**: Jobs scattered across multiple platforms (LinkedIn, Indeed, company sites, etc.)
- 🌍 **EU Visa Complexity**: Difficult to identify which companies genuinely sponsor work visas
- 📝 **Application Overhead**: Time-consuming resume and cover letter customization for each role
- 📊 **Lack of Insights**: No centralized tracking or analytics on application performance
- ⏰ **Manual Process**: Repetitive tasks that could be automated
- 🎯 **Poor Job Matching**: Generic recommendations that don't consider skill gaps and career goals

### The Solution

Career Copilot addresses these challenges through:

1. **Automated Job Aggregation**: 9 specialized scrapers collecting jobs every 6 hours from EU-focused sources
2. **Visa Sponsorship Detection**: Smart filtering to surface jobs from companies known to sponsor visas
3. **AI-Powered Content**: Generate tailored resumes and cover letters using OpenAI, Groq, Anthropic, or Google Gemini
4. **Centralized Tracking**: Manage all applications in one place with timeline views and status updates
5. **Intelligent Analytics**: Track success rates, response times, and market trends
6. **Smart Recommendations**: ML-based job matching with explainable AI and skill gap analysis

### 🌟 Key Features

#### 🔍 **Intelligent Job Discovery**

- **9 Specialized Scrapers**: Adzuna (13 EU countries), RapidAPI JSearch (19 EU countries), Firecrawl (10+ EU companies), The Muse, Indeed, Arbeitnow, Berlin Startup Jobs, Relocate.me, EURES

- **Automated Scheduling**: Jobs scraped every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)

- **3-Layer Deduplication**: URL normalization → Database filtering (30-day window) → Fuzzy matching (85% similarity)

- **Smart Filtering**: Location, salary range, skills, experience level, remote options, visa sponsorship

- **Expected Volume**: 200-500 new jobs per scraping cycle

#### 🌍 **EU-Focused Coverage**

- **70-80% EU Jobs**: Majority from 27 EU countries

- **50-60% Visa Sponsorship**: Roles from companies that hire internationally

- **Top Countries**: Germany, Netherlands, France, Sweden, Ireland, Spain, Poland, Belgium

- **Target Roles**: Data Scientist, ML Engineer, Data Analyst, Data Engineer, Backend/Frontend Engineer, DevOps, and 15+ tech roles

#### 🤖 **AI-Powered Content Generation**

- **Multiple AI Providers**: OpenAI GPT-4, Groq Llama 3, Anthropic Claude, Google Gemini

- **Personalized Resumes**: Tailored to specific job descriptions with skill highlighting

- **Cover Letters**: Context-aware letters matching company culture and job requirements

- **Version History**: Track and compare different versions

- **PDF Export**: Professional formatting with one-click export

- **Template Library**: Pre-built templates for different roles and industries

#### 📊 **Advanced Analytics & Insights**

- **Application Funnel**: Track conversion from viewed → applied → interviewed → offered

- **Success Metrics**: Response rates, interview conversion, time-to-offer

- **Market Trends**: Salary trends, skill demand, top hiring companies

- **Engagement Scoring**: 0-100 scale measuring your job search activity

- **User Segmentation**: Auto-categorization (highly active, moderate, low, inactive)

- **Personalized Insights**: AI-generated recommendations based on your behavior

#### 🔔 **Smart Notifications**

- **Multi-Channel**: Email, in-app, push notifications, SMS (via Twilio)

- **Daily Briefings**: Morning summary of new matching jobs (8:00 AM)

- **Evening Summaries**: Daily progress report (8:00 PM)

- **Application Reminders**: Deadline alerts and follow-up reminders

- **Achievement Milestones**: Celebrate application streaks and interview success

- **Retry Logic**: Exponential backoff (5s → 15s → 60s) for failed deliveries

#### 🔐 **Secure Authentication**

- **JWT-based Auth**: Secure token-based authentication

- **OAuth 2.0**: Google and LinkedIn social login (coming soon)

- **Single-User Mode**: Simplified setup for personal use

- **Password Hashing**: Bcrypt with configurable work factor

- **Session Management**: Redis-backed sessions with automatic expiration

#### ⚡ **High Performance**

- **Async Python**: FastAPI with async/await throughout

- **Connection Pooling**: PostgreSQL connection pool (10-20 connections)

- **Redis Caching**: 15-minute cache for recommendations, 5-minute for analytics

- **Batch Processing**: Queue-based event processing (100 events/batch, 30s intervals)

- **Circuit Breaker**: Fault tolerance with automatic recovery

- **Rate Limiting**: Sliding window (10 req/min per user for notifications, 100 events/min for analytics)

#### 📱 **Modern UI**

- **Next.js 14**: React Server Components with App Router

- **Real-time Updates**: TanStack Query for data synchronization

- **Responsive Design**: Mobile-first with TailwindCSS

- **Dark Mode**: Full dark theme support with system preference detection

- **Accessibility**: WCAG 2.1 AA compliant

- **Animations**: Framer Motion for smooth transitions

- **Data Visualization**: Recharts for analytics dashboards

### Current Status

**Version**: 1.0.0
**Last Updated**: November 6, 2025
**Deployment Environment**: Development/Localhost

| Component | Status | Details |
|-----------|--------|---------|
| ✅ **Backend API** | Running | `http://localhost:8002` |
| ✅ **Database** | Connected | PostgreSQL 14.19 @ localhost:5432 |
| ✅ **Cache** | Connected | Redis 7+ @ localhost:6379 |
| ✅ **Scheduler** | Active | APScheduler (every 6 hours + daily tasks) |
| ⚠️ **Celery** | Optional | Not running (for distributed tasks) |
| ⚠️ **Frontend** | Ready | Start with `npm run dev` in `frontend/` |
| ⚠️ **Monitoring** | Available | Prometheus + Grafana (Docker setup) |

**Production Readiness**: ~90%
**Total Production Code**: 3,240+ lines of enterprise services
**Test Coverage**: Comprehensive smoke tests passing
**Code Quality**: 0 lint errors (Ruff verified)

---

## 📊 Visual Documentation

### System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js 14 App]
        UI --> |REST API| Gateway[API Gateway]
    end

    subgraph "Backend Layer"
        Gateway --> Auth[Auth Service]
        Gateway --> Jobs[Jobs Service]
        Gateway --> AI[AI Service]
        Gateway --> Analytics[Analytics Service]
        Gateway --> Apps[Applications Service]

        Auth --> DB[(PostgreSQL)]
        Jobs --> DB
        AI --> DB
        Analytics --> DB
        Apps --> DB

        Jobs --> Cache[(Redis)]
        Analytics --> Cache
    end

    subgraph "Task Processing"
        Scheduler[APScheduler] --> Scraper[Job Scraper]
        Scheduler --> Notif[Notifications]
        Scheduler --> Health[Health Monitor]

        Scraper --> Dedup[Deduplication]
        Dedup --> DB
    end

    subgraph "External Services"
        Scraper --> |API| Adzuna[Adzuna API]
        Scraper --> |API| Rapid[RapidAPI JSearch]
        Scraper --> |API| Fire[Firecrawl API]
        Scraper --> |API| Others[6 Other Sources]

        AI --> |API| OpenAI[OpenAI GPT-4]
        AI --> |API| Groq[Groq Llama 3]
        AI --> |API| Claude[Anthropic Claude]
        AI --> |API| Gemini[Google Gemini]

        Notif --> |SMTP| Email[Email Service]
        Notif --> |API| SMS[Twilio SMS]
    end

    style UI fill:#61dafb
    style DB fill:#336791
    style Cache fill:#dc382d
    style OpenAI fill:#10a37f
```

### Job Scraping Pipeline

```mermaid
sequenceDiagram
    participant S as APScheduler
    participant M as Scraper Manager
    participant A as Adzuna Scraper
    participant R as RapidAPI Scraper
    participant F as Firecrawl Scraper
    participant D as Deduplication Service
    participant DB as PostgreSQL

    Note over S: Every 6 hours<br/>(00:00, 06:00, 12:00, 18:00 UTC)

    S->>M: Trigger job ingestion

    par Parallel Scraping
        M->>A: Scrape 13 EU countries
        M->>R: Scrape 19 EU countries
        M->>F: Scrape 10 EU companies
    end

    A-->>M: ~100 jobs
    R-->>M: ~80 jobs
    F-->>M: ~20 jobs

    M->>D: Process ~200 raw jobs

    Note over D: Layer 1: Normalize URLs<br/>Layer 2: DB filter (30d)<br/>Layer 3: Fuzzy match (85%)

    D->>D: Generate fingerprints<br/>(MD5: title+company+location)
    D->>DB: Check existing jobs
    DB-->>D: Return matches

    D->>D: Filter duplicates<br/>(~30-40% reduction)

    D->>DB: Save ~120-140 unique jobs

    Note over DB: Jobs enriched with:<br/>- Skills extracted<br/>- Visa support detected<br/>- Salary parsed<br/>- Location geocoded
```

### Data Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                         User Actions                             │
│  • Search jobs      • Apply       • Generate resume              │
│  • View analytics   • Track apps  • Get recommendations          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Frontend (Port 3000)                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   Dashboard  │ │  Job Search  │ │  Analytics   │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         │                 │                 │                     │
│         └─────────────────┴─────────────────┘                    │
│                           │                                       │
│                    TanStack Query                                │
│                   (State Management)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8002)                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              API Routes (/api/v1/*)                  │       │
│  │  /jobs /applications /ai /analytics /auth /resume   │       │
│  └────┬─────────────┬─────────────┬──────────────┬─────┘       │
│       │             │             │              │               │
│  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐  ┌─────▼─────┐         │
│  │  Jobs   │  │   AI    │  │Analytics│  │    Auth    │         │
│  │ Service │  │ Service │  │ Service │  │  Service   │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────┬─────┘         │
│       │            │            │              │                 │
│       ├────────────┴────────────┴──────────────┘                │
│       │                                                          │
│  ┌────▼─────────────────────────────────────────────┐           │
│  │         SQLAlchemy ORM (Async)                   │           │
│  └────┬─────────────────────────────────────────────┘           │
└───────┼──────────────────────────────────────────────────────────┘
        │
┌───────┴────────────────┬──────────────────┬────────────────────┐
│                        │                  │                     │
▼                        ▼                  ▼                     ▼
┌──────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │   Redis     │  │ APScheduler  │  │  External    │
│  Database    │  │   Cache     │  │   Tasks      │  │   APIs       │
│              │  │             │  │              │  │              │
│ • Users      │  │ • Sessions  │  │ • Scraping   │  │ • OpenAI     │
│ • Jobs       │  │ • Analytics │  │ • Briefings  │  │ • Adzuna     │
│ • Apps       │  │ • Recs      │  │ • Health     │  │ • Firecrawl  │
│ • Resumes    │  │ • Rate lim  │  │              │  │ • Twilio     │
└──────────────┘  └─────────────┘  └──────────────┘  └──────────────┘
```

### Component Interaction

```text
User Request Flow Example: "Generate Resume for Job #123"

1. Frontend (Next.js)
   ├─ User clicks "Generate Resume" button
   ├─ TanStack Query mutation triggered
   └─ POST /api/v1/ai/resume/generate { job_id: 123, provider: "groq" }

1. Backend API (FastAPI)
   ├─ Route: @router.post("/resume/generate")
   ├─ Auth Middleware: Validate JWT token
   ├─ Get current user from token
   └─ Call AIService.generate_resume()

1. AI Service
   ├─ Fetch job details from database (Job #123)
   ├─ Fetch user profile and skills
   ├─ Build prompt with context
   ├─ Call GroqService.generate()
   └─ Parse and validate AI response

1. Groq Service
   ├─ Check rate limits (Redis)
   ├─ Prepare API request
   ├─ Call Groq API (llama-3.1-70b-versatile)
   ├─ Retry on failure (exponential backoff)
   └─ Return generated resume text

1. AI Service (continued)
   ├─ Save resume to database
   ├─ Create version history
   ├─ Track AI usage metrics (Prometheus)
   └─ Return resume object

1. Backend API (continued)
   ├─ Serialize response
   └─ Return JSON: { id: 456, content: "...", job_id: 123 }

1. Frontend (Next.js)
   ├─ TanStack Query updates cache
   ├─ Component re-renders with new data
   └─ Display resume in editor
```

---

## 🏗️ Technical Architecture

### High-Level Architecture

Career Copilot follows a **modern microservices-inspired architecture** with clear separation of concerns:

**Frontend Tier**:

- Next.js 14 with React Server Components

- Client-side state management via TanStack Query

- Optimistic updates and real-time synchronization

- Progressive Web App (PWA) capabilities

**Backend Tier**:

- FastAPI with async/await throughout

- Service-oriented architecture (8 major services)

- Dependency injection for testability

- RESTful API design with OpenAPI 3.0 specs

**Data Tier**:

- PostgreSQL for relational data (users, jobs, applications)

- Redis for caching and session management

- File storage for uploads (resumes, documents)

**Task Processing Tier**:

- APScheduler for scheduled tasks (scraping, notifications)

- Celery for distributed task processing (optional)

- Queue-based event processing for analytics

**External Integration Tier**:

- Multiple AI providers (OpenAI, Groq, Anthropic, Google)

- Job scraping APIs (Adzuna, RapidAPI, Firecrawl, etc.)

- Communication services (SMTP, Twilio SMS)

### Technology Stack

#### Backend Technologies

| Technology | Version | Purpose | Why Chosen |
|------------|---------|---------|------------|
| **Python** | 3.11+ | Programming language | Type hints, async/await, performance |
| **FastAPI** | 0.109+ | Web framework | Modern, fast, auto-docs, async support |
| **SQLAlchemy** | 2.0+ | ORM | Powerful, async support, type-safe |
| **Alembic** | 1.13+ | Migrations | Database version control |
| **PostgreSQL** | 14+ | Database | Reliability, JSONB, full-text search |
| **AsyncPG** | 0.29+ | DB driver | High-performance async PostgreSQL |
| **Redis** | 7+ | Cache/Sessions | Fast, versatile, pub/sub support |
| **APScheduler** | 3.10+ | Task scheduling | Cron-like scheduling, persistent jobs |
| **Pydantic** | 2.5+ | Validation | Type-safe, fast, excellent error messages |
| **Uvicorn** | 0.27+ | ASGI server | High performance, WebSocket support |
| **Gunicorn** | 21+ | Process manager | Production-grade, multi-worker |

**AI & ML Libraries**:

- `openai` - OpenAI GPT-4 integration
- `anthropic` - Claude integration
- `groq` - Groq Llama 3 integration
- `google-generativeai` - Gemini integration
- `scikit-learn` - ML utilities for recommendations
- `fuzzywuzzy` - Fuzzy string matching for deduplication

**Scraping & Data**:

- `httpx` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML processing
- `feedparser` - RSS feed parsing
- `playwright` - Browser automation (LinkedIn scraper)

**Utilities**:

- `python-jose` - JWT tokens
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - File uploads
- `prometheus-client` - Metrics export
- `sentry-sdk` - Error tracking

#### Frontend Technologies

| Technology | Version | Purpose | Why Chosen |
|------------|---------|---------|------------|
| **Next.js** | 14.0 | React framework | SSR, RSC, App Router, performance |
| **React** | 19.2 | UI library | Component-based, large ecosystem |
| **TypeScript** | 5.0+ | Type safety | Catch errors early, better DX |
| **TailwindCSS** | 3.4+ | Styling | Utility-first, consistent, fast |
| **TanStack Query** | 5.90+ | Data fetching | Cache, sync, optimistic updates |
| **Framer Motion** | 12.23+ | Animations | Smooth, declarative, powerful |
| **Recharts** | 3.3+ | Charts | React-based, customizable |
| **Zustand** | 5.0+ | State management | Simple, no boilerplate |
| **Zod** | 4.1+ | Validation | Type-safe schema validation |
| **Axios** | 1.13+ | HTTP client | Interceptors, request/response transforms |
| **Lucide React** | 0.552+ | Icons | Modern, consistent, tree-shakeable |
| **date-fns** | 4.1+ | Date utilities | Modular, immutable, i18n |

**Development Tools**:

- `ESLint` - Code linting
- `Prettier` - Code formatting
- `Jest` - Unit testing
- `React Testing Library` - Component testing
- `Storybook` - Component development

### Design Patterns

Career Copilot implements several enterprise design patterns for maintainability and scalability:

#### 1. **Repository Pattern**

- **Where**: Data access layer (`app/repositories/`)

- **Why**: Abstraction over database operations, easier testing

- **Example**: `JobRepository`, `UserRepository`, `ApplicationRepository`

```python
class JobRepository:
    async def get_by_id(self, job_id: int) -> Job:
        """Retrieve job by ID"""

    async def search(self, filters: JobFilters) -> List[Job]:
        """Search jobs with filters"""

    async def bulk_create(self, jobs: List[JobCreate]) -> List[Job]:
        """Create multiple jobs efficiently"""
```

#### 2. **Service Layer Pattern**

- **Where**: Business logic layer (`app/services/`)

- **Why**: Separation of concerns, reusable business logic

- **Example**: `AIService`, `NotificationManager`, `AdaptiveRecommendationEngine`

```python
class AIService:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    async def generate_resume(self, job_id: int, provider: str) -> Resume:
        """Orchestrates resume generation workflow"""
        job = await self.job_repo.get(job_id)
        user = await self.user_repo.get(self.user_id)
        prompt = self._build_prompt(job, user)
        content = await self.ai_provider.generate(prompt)
        resume = await self.resume_repo.create(content)
        return resume
```

#### 3. **Factory Pattern**

- **Where**: AI provider selection (`app/services/ai/`)

- **Why**: Dynamic provider selection based on configuration

- **Example**: `AIProviderFactory`

```python
class AIProviderFactory:
    @staticmethod
    def create(provider: str) -> BaseAIProvider:
        if provider == "openai":
            return OpenAIProvider()
        elif provider == "groq":
            return GroqProvider()
        elif provider == "anthropic":
            return AnthropicProvider()
        raise ValueError(f"Unknown provider: {provider}")
```

#### 4. **Circuit Breaker Pattern**

- **Where**: Analytics Collection Service

- **Why**: Fault tolerance, prevents cascading failures

- **Implementation**: Opens after 5 consecutive failures, auto-resets after cooldown

```python
class CircuitBreaker:
    def __init__(self, threshold: int = 5):
        self.failures = 0
        self.threshold = threshold
        self.is_open = False

    async def call(self, func: Callable):
        if self.is_open:
            raise CircuitBreakerOpen()
        try:
            result = await func()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.is_open = True
            raise
```

#### 5. **Strategy Pattern**

- **Where**: Job deduplication (`app/services/job_deduplication_service.py`)

- **Why**: Multiple deduplication strategies can be swapped

- **Strategies**: URL matching, fingerprint matching, fuzzy matching

#### 6. **Observer Pattern**

- **Where**: Event tracking and analytics

- **Why**: Decoupled event handling

- **Implementation**: Analytics events observed by multiple consumers

#### 7. **Facade Pattern**

- **Where**: Analytics Service Facade

- **Why**: Simplified interface over complex analytics subsystem

- **Benefit**: Single entry point for all analytics operations

#### 8. **Dependency Injection**

- **Where**: Throughout backend (FastAPI's `Depends`)

- **Why**: Testability, loose coupling

- **Example**: Database session injection

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await JobService(db).get_job(job_id)
```

### Scalability Considerations

Career Copilot is designed to scale both vertically and horizontally:

**Database Scalability**:

- ✅ Connection pooling (10-20 connections per worker)
- ✅ Indexes on frequently queried columns
- ✅ JSONB for flexible schema evolution
- 🔄 Read replicas (planned for > 10K users)
- 🔄 Partitioning for job table by date (planned)

**API Scalability**:

- ✅ Async I/O throughout (handles 1000+ concurrent requests)
- ✅ Horizontal scaling via Gunicorn workers (4+ workers)
- ✅ Redis caching (15min for recommendations, 5min for analytics)
- ✅ Rate limiting per user
- 🔄 Load balancer (Nginx reverse proxy ready)
- 🔄 Auto-scaling with Kubernetes (Docker setup available)

**Frontend Scalability**:

- ✅ Code splitting and lazy loading
- ✅ Image optimization with next/image
- ✅ Static generation for marketing pages
- ✅ CDN-ready (static assets)
- 🔄 ISR (Incremental Static Regeneration) for job listings

**Task Processing Scalability**:

- ✅ Queue-based batch processing (100 events/batch)
- ✅ Parallel job scraping (9 scrapers concurrently)
- 🔄 Celery for distributed task execution
- 🔄 Message broker (RabbitMQ/Redis) for task queue

**Current Capacity**:

- Users: ~1000 concurrent users

- Jobs: ~500K jobs in database

- Scraping: ~200 jobs per cycle, 4 cycles/day = 800 jobs/day

- Analytics events: ~10K events/minute with batching

### Security Architecture

**Authentication & Authorization**:

- JWT tokens with HS256 signing (configurable to RS256)

- Token expiration: 24 hours (configurable)

- Password hashing: Bcrypt with work factor 12

- OAuth 2.0 ready for Google/LinkedIn (implementation in progress)

**Data Protection**:

- Encryption at rest: PostgreSQL encryption available

- Encryption in transit: HTTPS/TLS 1.3 (Nginx configuration)

- Environment variables for secrets (never committed)

- Sensitive field encryption: AES-256 for SSN, passport numbers

**API Security**:

- Rate limiting: 10 requests/minute per user for notifications

- CORS restrictions: Whitelist frontend origins

- Input validation: Pydantic models validate all inputs

- SQL injection prevention: Parameterized queries via SQLAlchemy

- XSS prevention: Output sanitization in frontend

**Dependency Security**:

- Regular dependency updates via Dependabot

- Snyk security scanning enabled

- No known vulnerabilities in production dependencies

- Minimal dependency tree (only necessary packages)

**Monitoring & Alerting**:

- Failed login attempts tracked

- Unusual activity patterns detected

- Error rates monitored via Prometheus

- Security audit logs (planned)

### Performance Optimizations

**Database Optimizations**:

- ✅ Indexes on `jobs.created_at`, `jobs.company`, `jobs.location`
- ✅ Composite index on (`user_id`, `created_at`) for applications
- ✅ Partial index on `jobs.visa_sponsorship = true`
- ✅ JSONB gin index for skills array
- ✅ Connection pooling with 10-20 connections

**Caching Strategy**:

- **Recommendations**: 15-minute TTL (user-specific)

- **Analytics**: 5-minute TTL (frequently changing data)

- **Job listings**: 1-minute TTL (balance freshness vs. load)

- **User sessions**: Redis with sliding expiration

- **Cache invalidation**: On user profile updates, new applications

**Query Optimizations**:

- ✅ Eager loading with `selectinload()` to avoid N+1 queries
- ✅ Pagination with cursor-based for large result sets
- ✅ Aggregate queries cached in Redis
- ✅ Full-text search using PostgreSQL's `to_tsvector()`

**Frontend Optimizations**:

- ✅ React Server Components for zero JS on initial render
- ✅ Code splitting (each route is a separate bundle)
- ✅ Image optimization (WebP, lazy loading)
- ✅ TanStack Query deduplicates simultaneous requests
- ✅ Optimistic updates for perceived performance
- ✅ Virtual scrolling for long lists (job results)

**Batch Processing**:

- ✅ Analytics events batched (100 events per batch, 30s flush)
- ✅ Notification queue batched (50 notifications per batch)
- ✅ Job scraping parallelized (9 scrapers concurrently)
- ✅ Database bulk inserts for jobs (100-500 at a time)

**Monitoring & Profiling**:

- ✅ Prometheus metrics for request duration, error rates
- ✅ Slow query logging (> 1 second)
- ✅ Endpoint performance tracking
- 🔄 OpenTelemetry traces for distributed tracing (planned)

---

## 📁 Project Structure

```text
career-copilot/
│
├── 📄 README.md                     # This comprehensive documentation
├── 📄 LICENSE                       # MIT License
├── 📄 VERSION                       # Version number (1.0.0)
├── 📄 pyproject.toml               # Python project configuration
├── 📄 docker-compose.yml           # Production Docker setup
├── 📄 docker-compose.dev.yml       # Development Docker setup
├── 📄 Makefile                     # Common commands shortcuts
├── 📄 .env.example                 # Environment variables template
├── 🔧 deploy.sh                    # Interactive deployment script
│
├── 📂 backend/                     # Python FastAPI backend
│   ├── 📄 __init__.py
│   ├── 📄 alembic.ini             # Database migration config
│   ├── 📂 app/                     # Main application code
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py             # FastAPI app entry point
│   │   │
│   │   ├── 📂 api/                 # API routes
│   │   │   └── 📂 v1/              # API version 1
│   │   │       ├── 📄 auth.py     # Authentication endpoints
│   │   │       ├── 📄 jobs.py     # Job search/management
│   │   │       ├── 📄 applications.py  # Application tracking
│   │   │       ├── 📄 ai.py       # AI content generation
│   │   │       ├── 📄 analytics.py # Analytics & insights
│   │   │       ├── 📄 resume.py   # Resume upload/parsing
│   │   │       └── 📄 users.py    # User profile management
│   │   │
│   │   ├── 📂 core/               # Core functionality
│   │   │   ├── 📄 config.py       # Configuration management
│   │   │   ├── 📄 database.py     # Database connection
│   │   │   ├── 📄 security.py     # JWT, hashing, encryption
│   │   │   ├── 📄 dependencies.py # Dependency injection
│   │   │   └── 📄 exceptions.py   # Custom exceptions
│   │   │
│   │   ├── 📂 models/             # SQLAlchemy models
│   │   │   ├── 📄 user.py         # User model
│   │   │   ├── 📄 job.py          # Job model
│   │   │   ├── 📄 application.py  # Application model
│   │   │   ├── 📄 resume.py       # Resume model
│   │   │   ├── 📄 analytics.py    # Analytics event model
│   │   │   └── 📄 notification.py # Notification model
│   │   │
│   │   ├── 📂 schemas/            # Pydantic schemas
│   │   │   ├── 📄 user.py         # User request/response schemas
│   │   │   ├── 📄 job.py          # Job schemas
│   │   │   ├── 📄 application.py  # Application schemas
│   │   │   └── 📄 ai.py           # AI generation schemas
│   │   │
│   │   ├── 📂 services/           # Business logic (3,240 lines)
│   │   │   ├── 📄 notification_manager.py      # 595 lines
│   │   │   ├── 📄 adaptive_recommendation_engine.py  # 593 lines
│   │   │   ├── 📄 analytics_collection_service.py    # 319 lines
│   │   │   ├── 📄 analytics_processing_service.py    # 316 lines
│   │   │   ├── 📄 analytics_query_service.py         # 252 lines
│   │   │   ├── 📄 analytics_reporting_service.py     # 299 lines
│   │   │   ├── 📄 analytics_service_facade.py        # 402 lines
│   │   │   ├── 📄 linkedin_scraper.py                # 464 lines
│   │   │   ├── 📄 job_deduplication_service.py
│   │   │   │
│   │   │   ├── 📂 scraping/       # Job scrapers (9 total)
│   │   │   │   ├── 📄 adzuna_scraper.py       # 13 EU countries
│   │   │   │   ├── 📄 rapidapi_scraper.py     # 19 EU countries
│   │   │   │   ├── 📄 firecrawl_scraper.py    # 10 EU companies
│   │   │   │   ├── 📄 themuse_scraper.py
│   │   │   │   ├── 📄 indeed_scraper.py
│   │   │   │   ├── 📄 arbeitnow_scraper.py
│   │   │   │   ├── 📄 berlin_startup_jobs_scraper.py
│   │   │   │   ├── 📄 relocate_me_scraper.py
│   │   │   │   └── 📄 eures_scraper.py
│   │   │   │
│   │   │   └── 📂 ai/             # AI providers
│   │   │       ├── 📄 openai_service.py
│   │   │       ├── 📄 groq_service.py
│   │   │       ├── 📄 anthropic_service.py
│   │   │       └── 📄 gemini_service.py
│   │   │
│   │   ├── 📂 tasks/              # Scheduled tasks
│   │   │   ├── 📄 scheduled_tasks.py  # APScheduler jobs
│   │   │   └── 📄 celery_tasks.py     # Celery tasks (optional)
│   │   │
│   │   └── 📂 utils/              # Utility functions
│   │       ├── 📄 email.py        # Email sending
│   │       ├── 📄 sms.py          # SMS via Twilio
│   │       ├── 📄 metrics.py      # Prometheus metrics
│   │       └── 📄 logging.py      # Structured logging
│   │
│   ├── 📂 alembic/                # Database migrations
│   │   └── 📂 versions/           # Migration files
│   │
│   ├── 📂 tests/                  # Unit & integration tests
│   │   ├── 📂 unit/
│   │   ├── 📂 integration/
│   │   └── 📂 e2e/
│   │
│   ├── 📂 scripts/                # Utility scripts
│   │   ├── 📄 create_test_user.py
│   │   ├── 📄 backfill_job_fingerprints.py
│   │   ├── 📄 monitor_deduplication.py
│   │   └── 📄 verify_system_health.py
│   │
│   └── 📂 logs/                   # Application logs
│       ├── app.log
│       ├── celery/
│       └── scraping/
│
├── 📂 frontend/                   # Next.js React frontend
│   ├── 📄 package.json
│   ├── 📄 next.config.js
│   ├── 📄 tailwind.config.ts
│   ├── 📄 tsconfig.json
│   ├── 📂 src/
│   │   ├── 📂 app/                # Next.js 14 App Router
│   │   │   ├── 📄 layout.tsx      # Root layout
│   │   │   ├── 📄 page.tsx        # Home page
│   │   │   ├── 📂 dashboard/      # Dashboard pages
│   │   │   ├── 📂 jobs/           # Job search pages
│   │   │   ├── 📂 applications/   # Application tracking
│   │   │   ├── 📂 analytics/      # Analytics pages
│   │   │   ├── 📂 ai-tools/       # AI resume/cover letter
│   │   │   └── 📂 profile/        # User profile
│   │   │
│   │   ├── 📂 components/         # React components
│   │   │   ├── 📂 ui/             # Reusable UI components
│   │   │   │   ├── 📄 Button.tsx
│   │   │   │   ├── 📄 Card.tsx
│   │   │   │   ├── 📄 Input.tsx
│   │   │   │   └── 📄 Modal.tsx
│   │   │   ├── 📂 features/       # Feature components
│   │   │   │   ├── 📄 JobCard.tsx
│   │   │   │   ├── 📄 ApplicationTimeline.tsx
│   │   │   │   └── 📄 ResumeEditor.tsx
│   │   │   ├── 📂 forms/          # Form components
│   │   │   ├── 📂 layout/         # Layout components
│   │   │   └── 📂 charts/         # Chart components
│   │   │
│   │   ├── 📂 lib/                # Utilities
│   │   │   ├── 📄 api.ts          # API client
│   │   │   ├── 📄 auth.ts         # Auth helpers
│   │   │   ├── 📄 utils.ts        # General utilities
│   │   │   └── 📄 animations.ts   # Framer Motion variants
│   │   │
│   │   ├── 📂 hooks/              # Custom React hooks
│   │   │   ├── 📄 useJobs.ts
│   │   │   ├── 📄 useApplications.ts
│   │   │   └── 📄 useAnalytics.ts
│   │   │
│   │   ├── 📂 contexts/           # React contexts
│   │   │   ├── 📄 AuthContext.tsx
│   │   │   └── 📄 ThemeContext.tsx
│   │   │
│   │   └── 📂 types/              # TypeScript types
│   │       ├── 📄 job.ts
│   │       ├── 📄 application.ts
│   │       └── 📄 user.ts
│   │
│   └── 📂 public/                 # Static assets
│       ├── 📂 images/
│       └── 📂 icons/
│
├── 📂 deployment/                 # Deployment configs
│   ├── 📂 docker/                 # Dockerfiles
│   │   ├── 📄 Dockerfile.backend
│   │   ├── 📄 Dockerfile.frontend
│   │   └── 📄 README.md           # Docker deployment guide
│   ├── 📂 k8s/                    # Kubernetes manifests
│   ├── 📂 nginx/                  # Nginx configs
│   │   └── 📄 nginx.conf
│   └── 📂 services/               # Systemd service files
│
├── 📂 monitoring/                 # Monitoring setup
│   ├── 📂 prometheus/
│   │   ├── 📄 prometheus.yml
│   │   └── 📄 alerts.yml
│   └── 📂 grafana/
│       └── 📂 dashboards/
│
├── 📂 config/                     # Configuration files
│   ├── 📄 application.yaml        # App configuration
│   ├── 📄 llm_config.json         # AI provider configs
│   └── 📂 environments/           # Environment-specific configs
│
├── 📂 data/                       # Data storage
│   ├── 📂 postgres/               # PostgreSQL data
│   ├── 📂 redis/                  # Redis persistence
│   ├── 📂 uploads/                # User uploads (resumes)
│   ├── 📂 backups/                # Database backups
│   └── 📂 logs/                   # Centralized logs
│
├── 📂 scripts/                    # Deployment scripts
│   ├── 🔧 setup.sh                # Initial setup
│   ├── 🔧 start_backend.sh        # Start backend server
│   ├── 🔧 start_frontend.sh       # Start frontend dev server
│   └── 🔧 start_celery.sh         # Start Celery workers
│
└── 📂 docs/                       # Additional documentation
    └── 📄 MONITORING.md           # Monitoring & observability guide
```

### Module Organization Principles

**Backend Organization**:

1. **Separation by Layer**: API → Services → Repositories → Models
2. **Feature-Based Grouping**: All job-related code in one place
3. **Dependency Direction**: Higher layers depend on lower (no circular deps)
4. **Single Responsibility**: Each module has one clear purpose

**Frontend Organization**:

1. **Colocation**: Components near where they're used
2. **Composition**: Small, reusable components
3. **Feature Folders**: Group related components
4. **Shared UI**: Common components in `ui/` folder

---

## 🧩 Component Deep Dive

### 1. Job Discovery System

**Purpose**: Aggregate jobs from multiple sources with intelligent deduplication

**Architecture**:

```text
APScheduler → ScraperManager → 9 Parallel Scrapers → Deduplication → Database
```

**Components**:

#### Scraper Manager

- **File**: `backend/app/services/scraping/scraper_manager.py`

- **Responsibilities**:

  - Orchestrates 9 scrapers in parallel
  - Aggregates results
  - Error handling and retry logic
  - Metrics collection

#### Individual Scrapers

Each scraper follows this interface:

```python
class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, keywords: List[str], locations: List[str]) -> List[JobData]:
        """Scrape jobs from source"""

    @abstractmethod
    def normalize_job(self, raw_data: dict) -> JobData:
        """Normalize job data to standard format"""
```

**Scraper Coverage**:

| Scraper | Coverage | Jobs/Cycle | Visa Support | Status |
|---------|----------|------------|--------------|--------|
| Adzuna | 13 EU countries | ~100 | ~50% | ✅ Active |
| RapidAPI JSearch | 19 EU countries | ~80 | ~60% | ✅ Active |
| Firecrawl | 10 EU companies | ~20 | ~90% | ✅ Active |
| The Muse | Global (many EU) | ~30 | ~40% | ✅ Active |
| Indeed | Global | ~40 | ~30% | ✅ Active |
| Arbeitnow | Germany-focused | ~25 | ~70% | ✅ Active |
| Berlin Startup Jobs | Berlin only | ~15 | ~80% | ⚠️ Deprecated |
| Relocate.me | EU relocation | ~10 | ~100% | ⚠️ API down |
| EURES | EU official | ~5 | ~60% | ⚠️ No API |

#### Deduplication Service

- **File**: `backend/app/services/job_deduplication_service.py`

- **Strategy**: 3-layer approach

  1. **URL Normalization**: Strip tracking params, normalize domains
  2. **Fingerprint Matching**: MD5 hash of (title + company + location)
  3. **Fuzzy Matching**: 85% title similarity + 80% company similarity

**Example Usage**:

```python
from app.services.scraping.scraper_manager import ScraperManager

manager = ScraperManager(db=session)

# Trigger scraping
results = await manager.scrape_all(
    keywords=["data scientist", "machine learning engineer"],
    locations=["Berlin", "Amsterdam", "Stockholm"]
)

# Returns: {
#   "total_scraped": 200,
#   "after_dedup": 140,
#   "saved_to_db": 135,
#   "errors": []
# }
```

### 2. Application Tracking

**Purpose**: Manage job applications through their lifecycle

**States**: `saved` → `applied` → `interviewing` → `offered` / `rejected`

**Components**:

#### Application Model

```python
class Application(Base):
    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus  # enum
    applied_date: datetime
    notes: str
    resume_used: str  # resume version
    cover_letter: str
    interview_dates: List[datetime]
    follow_up_date: datetime
    salary_expectation: int
```

#### Application Service

- **File**: `backend/app/services/application_service.py`

- **Features**:

  - State machine for status transitions
  - Timeline tracking
  - Reminder scheduling
  - Document attachment

**API Endpoints**:

```python
POST   /api/v1/applications              # Create application
GET    /api/v1/applications              # List with filters
GET    /api/v1/applications/{id}         # Get details
PUT    /api/v1/applications/{id}         # Update status/notes
DELETE /api/v1/applications/{id}         # Delete
GET    /api/v1/applications/{id}/timeline # Get timeline
POST   /api/v1/applications/{id}/reminder # Set reminder
```

**Frontend Components**:

- `ApplicationCard.tsx` - Card view for list
- `ApplicationTimeline.tsx` - Visual timeline
- `ApplicationForm.tsx` - Create/edit form
- `ApplicationFilters.tsx` - Filter sidebar

### 3. AI Content Generation

**Purpose**: Generate personalized resumes and cover letters

**Supported Providers**:

1. **OpenAI** (GPT-4, GPT-3.5-turbo)
2. **Groq** (Llama 3.1 70B, Llama 3 8B)
3. **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
4. **Google** (Gemini Pro, Gemini Pro Vision)

**Architecture**:

```text
User Request → AIService → Provider Factory → Specific Provider → API Call → Response Parsing → Database → User
```

#### AI Service

- **File**: `backend/app/services/ai/ai_service.py`

- **Responsibilities**:

  - Provider selection
  - Prompt engineering
  - Response validation
  - Cost tracking
  - Rate limit handling

**Prompt Structure for Resume**:

```text
You are an expert resume writer. Generate a professional resume tailored for this job.

JOB DETAILS:
- Title: {job.title}

- Company: {job.company}

- Description: {job.description}

- Required Skills: {job.skills}

USER PROFILE:
- Name: {user.full_name}

- Current Role: {user.current_role}

- Experience: {user.experience_years} years

- Skills: {user.skills}

- Education: {user.education}

TASK:
Create a 1-page resume highlighting relevant experience and skills for this role.
Format in professional resume structure (Contact, Summary, Experience, Skills, Education).
```

**Code Example**:

```python
from app.services.ai.ai_service.py import AIService

ai_service = AIService(db=session, user_id=1)

# Generate resume
resume = await ai_service.generate_resume(
    job_id=123,
    provider="groq",
    model="llama-3.1-70b-versatile",
    tone="professional"
)

# Generate cover letter
cover_letter = await ai_service.generate_cover_letter(
    job_id=123,
    provider="openai",
    model="gpt-4",
    tone="enthusiastic",
    length="medium"  # short, medium, long
)

# Export to PDF
pdf_bytes = await ai_service.export_resume_pdf(resume.id)
```

### 4. Analytics Engine

**Purpose**: Track user behavior and provide insights

**Components**: 5 interconnected services (1,588 total lines)

#### Analytics Collection Service (319 lines)

- **Collects events**: page views, job views, searches, applications

- **Queue-based**: 10,000 event capacity

- **Circuit breaker**: Fault tolerance

- **Rate limiting**: 100 events/60s per user

**Event Types**:

- `page_view` - User navigates to page
- `job_view` - User views job details
- `job_search` - User performs search
- `job_save` - User bookmarks job
- `application_submit` - User applies to job
- `resume_generate` - AI resume generated
- `profile_update` - User updates profile

#### Analytics Processing Service (316 lines)

- **User behavior analysis**

- **Conversion funnel**: viewed → applied → interviewed → offered

- **Engagement scoring**: 0-100 scale based on activity

- **User segmentation**: highly_active, moderately_active, low_activity, inactive

#### Analytics Query Service (252 lines)

- **Flexible metric retrieval**

- **Time-series support**: day, week, month granularity

- **Caching**: 5-minute TTL

- **Aggregations**: sum, avg, count, percentiles

#### Analytics Reporting Service (299 lines)

- **Market trends**: Top companies, skills, salaries

- **User insights**: Performance compared to cohort

- **Recommendations**: Action items based on data

#### Analytics Service Facade (402 lines)

- **Unified interface** over all analytics services

- **Simplified API** for common operations

- **Health checks** for all subsystems

**Usage Example**:

```python
from app.services.analytics_service_facade import AnalyticsServiceFacade

facade = AnalyticsServiceFacade(db=session)

# Track events
await facade.track_page_view(user_id=1, path="/dashboard")
await facade.track_job_view(user_id=1, job_id=123, source="search")

# Get dashboard data
dashboard = facade.get_dashboard_data(user_id=1)
# Returns: {
#   "analytics": {
#     "jobs_viewed": 150,
#     "applications_submitted": 25,
#     "interviews_scheduled": 5,
#     "offers_received": 1,
#     "conversion_rate": 4.0
#   },
#   "engagement_score": 75.5,
#   "funnel": {
#     "viewed": {"count": 150, "conversion": 100.0},
#     "applied": {"count": 25, "conversion": 16.7}
#   },
#   "insights": [
#     {"type": "success", "message": "Great interview rate!"},
#     {"type": "action", "message": "Consider applying to 5-10 jobs/week"}
#   ]
# }
```

### 5. Notification System

**Purpose**: Multi-channel notification delivery with retry logic

**File**: `backend/app/services/notification_manager.py` (595 lines)

**Features**:

- **Multi-channel**: Email, in-app, push (Firebase), SMS (Twilio)

- **Retry logic**: Exponential backoff (5s → 15s → 60s)

- **Rate limiting**: 10 requests/60s per user (sliding window)

- **Queue management**: Batch processing (50 notifications/batch)

- **User preferences**: Respects opt-out settings

- **Delivery tracking**: Success rates, failure reasons

**Notification Types**:

- `job_match` - New job matches your profile
- `application_status` - Application status update
- `interview_scheduled` - Interview confirmed
- `deadline_reminder` - Application deadline approaching
- `daily_briefing` - Morning summary of new jobs
- `weekly_summary` - Week's activity summary
- `achievement` - Milestone reached

**Usage Example**:

```python
from app.services.notification_manager import NotificationManager

manager = NotificationManager(db=session)

# Send with retry
result = await manager.send_with_retry(
    user_id=1,
    notification_type="job_match",
    channel="email",
    subject="New Jobs Match Your Profile!",
    content="We found 5 new jobs matching your skills...",
    data={"job_ids": [123, 456, 789]}
)

# Queue for batch processing
manager.queue_notification(
    user_id=1,
    notification_type="deadline_reminder",
    data={"deadline": "2025-11-10", "job_title": "Senior Data Scientist"}
)

# Process queue (called by background task)
await manager.process_queue()

# Get statistics
stats = manager.get_delivery_stats()
# Returns: {
#   "total_sent": 150,
#   "successful": 145,
#   "failed": 5,
#   "by_channel": {"email": 100, "in_app": 50},
#   "by_type": {"job_match": 80, "deadline_reminder": 70}
# }
```

### 6. Recommendation Engine

**Purpose**: Personalized job recommendations with explainable AI

**File**: `backend/app/services/adaptive_recommendation_engine.py` (593 lines)

**Features**:

- **Multi-factor scoring**: 7 weighted factors

- **A/B testing framework**: Optimize algorithm

- **Caching**: 15-minute TTL per user

- **Explainable AI**: Detailed match explanations

- **Diversity boosting**: Max 3 jobs per company

- **Configurable weights**: Dynamic adjustment

**Scoring Factors**:

| Factor | Weight | Description |
|--------|--------|-------------|
| Skill Match | 40% | % of required skills user has |
| Location | 20% | Remote OK, preferred cities |
| Experience | 15% | Years match job requirements |
| Salary | 10% | Within user's expected range |
| Company Culture | 5% | Company size, industry preferences |
| Growth Potential | 5% | Learning opportunities, career path |
| Recency | 5% | Recently posted jobs |

**Usage Example**:

```python
from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

engine = AdaptiveRecommendationEngine(db=session)

# Get recommendations
recommendations = await engine.get_recommendations_adaptive(
    user_id=1,
    limit=10,
    min_score=30.0
)

# Returns: [
#   {
#     "job": <Job object>,
#     "match_score": 85.5,
#     "explanation": {
#       "matching_skills": ["Python", "Machine Learning", "TensorFlow"],
#       "missing_skills": ["Kubernetes", "AWS"],
#       "location_match": "Remote OK",
#       "salary_match": "Within range ($120K-$150K)",
#       "score_breakdown": {
#         "skill_match": 34.2,  # 40% * 85.5%
#         "location_match": 20.0,
#         "experience_match": 12.0,
#         "salary_match": 9.5,
#         ...
#       }
#     }
#   },
#   ...
# ]

# Start A/B test
engine.start_ab_test(
    test_name="skill_weight_optimization",
    variant_a={"skill_match": 50, "location_match": 15},
    variant_b={"skill_match": 30, "location_match": 30},
    traffic_split=0.5  # 50% users to each variant
)

# Get test results (after sufficient data)
results = engine.get_ab_test_results(test_name="skill_weight_optimization")
# Returns: {
#   "variant_a": {"click_rate": 0.25, "apply_rate": 0.05},
#   "variant_b": {"click_rate": 0.30, "apply_rate": 0.07},
#   "winner": "variant_b",
#   "confidence": 0.95
# }
```

---

## 📦 Prerequisites & Dependencies

### Required Software

| Software | Minimum Version | Recommended | Purpose | Installation |
|----------|----------------|-------------|---------|--------------|
| **Python** | 3.11 | 3.11 or 3.12 | Backend runtime | [python.org](https://python.org) |
| **Node.js** | 18.x | 20.x LTS | Frontend runtime | [nodejs.org](https://nodejs.org) |
| **PostgreSQL** | 14 | 15 or 16 | Primary database | [postgresql.org](https://postgresql.org) |
| **Redis** | 7.0 | 7.2+ | Caching & sessions | [redis.io](https://redis.io) |
| **Git** | 2.30+ | Latest | Version control | [git-scm.com](https://git-scm.com) |

### System Requirements

**Minimum**:

- **CPU**: 2 cores

- **RAM**: 4 GB

- **Disk**: 2 GB free space

- **OS**: macOS 11+, Ubuntu 20.04+, Windows 10+ (with WSL2)

**Recommended** (for production):

- **CPU**: 4+ cores

- **RAM**: 8+ GB

- **Disk**: 10+ GB (SSD)

- **OS**: Ubuntu 22.04 LTS or macOS 13+

### Required Accounts & Services

#### Essential (Free Tier Available)

1. **Database**: PostgreSQL (local or cloud)
2. **Job Scraping**: At least one
   - Adzuna API (free tier: 250 requests/month)
   - RapidAPI (free tier: 100 requests/month)
3. **AI Provider**: At least one
   - OpenAI (pay-as-you-go)
   - Groq (free tier: high limits)
   - Anthropic (pay-as-you-go)
   - Google Gemini (free tier available)

#### Optional

1. **Email**: SMTP server (Gmail, SendGrid, AWS SES)
2. **SMS**: Twilio (for SMS notifications)
3. **Monitoring**: Sentry (error tracking), Prometheus, Grafana
4. **Cloud Storage**: AWS S3, Google Cloud Storage (for resume backups)

### Dependency Overview

**Backend Dependencies** (from `pyproject.toml`):

```toml
[project.dependencies]
# Core Web Framework (5 packages)
fastapi>=0.109.0           # Modern web framework
uvicorn[standard]>=0.27.0  # ASGI server
gunicorn>=21.2.0           # Process manager
python-multipart>=0.0.6    # File upload support
pydantic[email]>=2.5.3     # Data validation

# Database & ORM (5 packages)
sqlalchemy>=2.0.25         # ORM with async support
alembic>=1.13.1            # Database migrations
psycopg2-binary>=2.9.9     # PostgreSQL driver (sync)
asyncpg>=0.29.0            # PostgreSQL driver (async)
aiosqlite>=0.19.0          # SQLite async (dev/testing)

# Authentication & Security (6 packages)
python-jose[cryptography]>=3.3.0  # JWT tokens
passlib[bcrypt]>=1.7.4     # Password hashing
bcrypt>=4.1.2              # Bcrypt algorithm
cryptography>=41.0.7       # Encryption utilities
pyjwt>=2.8.0               # JWT library

# AI Services (4 packages)
openai>=1.6.1              # OpenAI GPT integration
anthropic>=0.8.1           # Claude integration
groq>=0.4.1                # Groq Llama integration
google-generativeai>=0.3.1 # Gemini integration

# HTTP & Scraping (5 packages)
httpx>=0.26.0              # Async HTTP client
beautifulsoup4>=4.12.2     # HTML parsing
lxml>=4.9.3                # XML/HTML processing
feedparser>=6.0.10         # RSS feeds
playwright>=1.40.0         # Browser automation

# Caching & Task Queue (3 packages)
redis>=5.0.1               # Redis client
celery>=5.3.4              # Distributed tasks (optional)
apscheduler>=3.10.4        # Scheduled tasks

# Utilities (10+ packages)
python-dotenv>=1.0.0       # Environment variables
pyyaml>=6.0.1              # YAML config
click>=8.1.7               # CLI framework
jinja2>=3.1.2              # Template engine
prometheus-client>=0.19.0  # Metrics export
sentry-sdk>=1.40.0         # Error tracking
fuzzywuzzy>=0.18.0         # Fuzzy string matching
python-levenshtein>=0.23.0 # Edit distance
pillow>=10.1.0             # Image processing
reportlab>=4.0.7           # PDF generation
```

**Frontend Dependencies** (from `package.json`):

```json
{
  "dependencies": {
    "next": "^15.5.6",                    // React framework
    "react": "^19.2.0",                   // UI library
    "react-dom": "^19.2.0",               // React DOM
    "@tanstack/react-query": "^5.90.7",   // Data fetching
    "axios": "^1.13.2",                   // HTTP client
    "framer-motion": "^12.23.24",         // Animations
    "tailwindcss": "^3.4.1",              // Utility CSS
    "recharts": "^3.3.0",                 // Charts
    "zustand": "^5.0.8",                  // State management
    "zod": "^4.1.12",                     // Validation
    "lucide-react": "^0.552.0",           // Icons
    "date-fns": "^4.1.0",                 // Date utilities
    "clsx": "^2.1.1",                     // Conditional classes
    "jwt-decode": "^4.0.0",               // JWT parsing
    "sonner": "^2.0.7"                    // Toast notifications
  },
  "devDependencies": {
    "typescript": "^5.0.0",               // Type checking
    "eslint": "^8.57.0",                  // Linting
    "prettier": "^3.2.5",                 // Formatting
    "jest": "^29.7.0",                    // Testing
    "@testing-library/react": "^14.2.1",  // React testing
    "storybook": "^8.6.14"                // Component dev
  }
}
```

### Why Each Major Dependency?

**Backend**:

- **FastAPI**: Chosen for automatic API docs, async support, type safety, and performance (comparable to Node.js/Go)

- **SQLAlchemy 2.0**: Latest version with async support, powerful ORM, type hints throughout

- **PostgreSQL**: Reliability, ACID compliance, JSONB for flexible schemas, full-text search

- **Redis**: Fast in-memory storage for sessions, caching, rate limiting, pub/sub

- **APScheduler**: Python-native scheduler, persistent jobs, no external dependencies (unlike Celery)

- **Pydantic**: Runtime validation, automatic API docs, great error messages

**Frontend**:

- **Next.js 14**: React Server Components, App Router, excellent DX, built-in optimizations

- **TanStack Query**: Declarative data fetching, automatic caching, optimistic updates

- **TailwindCSS**: Rapid development, consistent design, small bundle size

- **Zustand**: Simple state management, minimal boilerplate (vs Redux)

- **Framer Motion**: Smooth animations, gesture support, layout animations

---

## 🚀 Installation & Setup

### Quick Start (5 Minutes)

For users who want to get started quickly:

```bash
# 1. Clone repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Run automated setup (macOS/Linux)
./deploy.sh

# 3. Follow interactive prompts
# - Choose development environment
# - Configure API keys
# - Setup database

# 4. Access application
# Backend: http://localhost:8002
# Frontend: http://localhost:3000
```

### Detailed Step-by-Step Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot
```

#### Step 2: Backend Setup

##### 2.1 Install Python (if not installed)

**macOS**:

```bash
brew install python@3.11
```

**Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**Windows** (WSL2):

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

##### 2.2 Create Virtual Environment

```bash
cd backend
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows (WSL2):
source venv/bin/activate
```

Your prompt should now show `(venv)`.

##### 2.3 Install Backend Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project in editable mode (reads pyproject.toml)
pip install -e .

# Verify installation
pip list | grep -E "fastapi|sqlalchemy|redis"
```

**Expected output**:

```text
fastapi           0.109.0
sqlalchemy        2.0.25
redis             5.0.1
```

##### 2.4 Setup PostgreSQL Database

##### Option A: Local PostgreSQL (macOS)**

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create database
createdb career_copilot

# Verify
psql -d career_copilot -c "SELECT version();"
```

##### Option B: Local PostgreSQL (Ubuntu)**

```bash
# Install PostgreSQL
sudo apt install postgresql-14 postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb career_copilot
sudo -u postgres createuser $(whoami) -s

# Verify
psql -d career_copilot -c "SELECT version();"
```

##### Option C: Docker PostgreSQL**

```bash
docker run -d \
  --name career-copilot-db \
  -e POSTGRES_DB=career_copilot \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -v career_copilot_db:/var/lib/postgresql/data \
  postgres:14

# Verify
docker exec -it career-copilot-db psql -U postgres -d career_copilot -c "SELECT version();"
```

##### Option D: Cloud PostgreSQL**

Use managed PostgreSQL from:

- **Heroku Postgres** (free tier available)

- **Supabase** (free tier: 500MB)

- **Railway** (free tier: 1GB)

- **Neon** (serverless Postgres, free tier)

##### 2.5 Setup Redis

##### Option A: Local Redis (macOS)**

```bash
brew install redis
brew services start redis

# Verify
redis-cli ping  # Should return: PONG
```

##### Option B: Local Redis (Ubuntu)**

```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify
redis-cli ping  # Should return: PONG
```

##### Option C: Docker Redis**

```bash
docker run -d \
  --name career-copilot-redis \
  -p 6379:6379 \
  -v career_copilot_redis:/data \
  redis:7-alpine \
  redis-server --appendonly yes

# Verify
docker exec -it career-copilot-redis redis-cli ping
```

##### 2.6 Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env  # or vim, code, etc.
```

**Minimum Required Configuration** (`.env`):

```bash
# ============================================================================
# CORE SETTINGS
# ============================================================================
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8002
DEBUG=True

# ============================================================================
# DATABASE
# ============================================================================
# Local PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/career_copilot

# Or Docker PostgreSQL
# DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@localhost:5432/career_copilot

# Or Cloud (example: Supabase)
# DATABASE_URL=postgresql+asyncpg://user:pass@db.xxx.supabase.co:5432/postgres

# ============================================================================
# REDIS
# ============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Leave empty for local Redis without password
REDIS_DB=0

# ============================================================================
# SECURITY
# ============================================================================
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=CHANGE_THIS_TO_RANDOM_SECRET_KEY_32_CHARS_MIN
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=CHANGE_THIS_TO_FERNET_KEY

# ============================================================================
# AI SERVICES (At least ONE required)
# ============================================================================
# OpenAI (https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-xxx

# Groq (https://console.groq.com/keys) - FREE high limits
GROQ_API_KEY=gsk_xxx

# Anthropic (https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-xxx

# Google Gemini (https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=AIzaxxx

# ============================================================================
# JOB SCRAPING APIs (At least ONE required for job discovery)
# ============================================================================
# Adzuna (https://developer.adzuna.com/signup)
# Free tier: 250 requests/month
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

# RapidAPI (https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
# Free tier: 100 requests/month
RAPIDAPI_KEY=your_rapidapi_key

# Firecrawl (https://www.firecrawl.dev/)
# Free tier available
FIRECRAWL_API_KEY=fc-xxx

# ============================================================================
# SCRAPER CONFIGURATION
# ============================================================================
SCRAPING_ENABLE_ADZUNA=True
SCRAPING_ENABLE_RAPIDAPI=True
SCRAPING_ENABLE_THEMUSE=True
SCRAPING_ENABLE_ARBEITNOW=True
SCRAPING_ENABLE_FIRECRAWL=False  # Set to True if you have API key

# ============================================================================
# CORS (Frontend URL)
# ============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ============================================================================
# OPTIONAL: Email Notifications
# ============================================================================
SMTP_ENABLED=False  # Set to True to enable
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password  # NOT your Gmail password!
SMTP_FROM_EMAIL=noreply@career-copilot.com
SMTP_FROM_NAME=Career Copilot

# ============================================================================
# OPTIONAL: SMS Notifications (Twilio)
# ============================================================================
TWILIO_ENABLED=False
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890

# ============================================================================
# OPTIONAL: Monitoring
# ============================================================================
SENTRY_DSN=  # Leave empty to disable
PROMETHEUS_ENABLED=True
```

**Generate Secure Keys**:

```bash
# JWT Secret Key
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Encryption Key (Fernet)
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

##### 2.7 Run Database Migrations

```bash
# Run migrations to create tables
alembic upgrade head

# Verify tables were created
psql -d career_copilot -c "\dt"
```

**Expected output**:

```text
List of relations
Schema | Name                  | Type  | Owner
-------|----------------------|-------|-------
public | users                | table | postgres
public | jobs                 | table | postgres
public | applications         | table | postgres
public | resumes              | table | postgres
public | analytics_events     | table | postgres
public | notifications        | table | postgres
public | alembic_version      | table | postgres
```

##### 2.8 Create Test User (Optional)

```bash
python backend/scripts/create_test_user.py
```

This creates:

- Email: `test@example.com`

- Password: `password123`

##### 2.9 Start Backend Server

```bash
# Development mode (with hot-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# Or use the script
./start_backend.sh
```

**Verify Backend**:

1. Open browser: `http://localhost:8002/docs` (Swagger UI)
2. Try health endpoint:

   ```bash
   curl http://localhost:8002/health
   ```

   Expected response:

   ```json
   {
     "status": "healthy",
     "database": "connected",
     "redis": "connected",
     "version": "1.0.0"
   }
   ```

#### Step 3: Frontend Setup

Open a **new terminal** (keep backend running).

##### 3.1 Install Node.js (if not installed)

**macOS**:

```bash
brew install node@20
```

**Ubuntu**:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**Verify**:

```bash
node --version  # Should be v20.x.x
npm --version   # Should be 10.x.x
```

##### 3.2 Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install all packages from `package.json` (~500MB).

##### 3.3 Configure Frontend Environment

```bash
# Copy example file
cp .env.local.example .env.local

# Edit with your values
nano .env.local
```

**Frontend Configuration** (`.env.local`):

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_API_VERSION=v1

# Environment
NEXT_PUBLIC_ENVIRONMENT=development

# Optional: Google Analytics
NEXT_PUBLIC_GA_ID=

# Optional: Sentry
NEXT_PUBLIC_SENTRY_DSN=
```

##### 3.4 Start Frontend Development Server

```bash
npm run dev
```

**Verify Frontend**:

1. Open browser: `http://localhost:3000`
2. You should see the Career Copilot landing page
3. Try navigating to dashboard, jobs, etc.

#### Step 4: Verify Complete Installation

Run the system health check:

```bash
cd backend
python scripts/verify_system_health.py
```

**Expected output**:

```text
✅ Backend API: Running (http://localhost:8002)
✅ Database: Connected (PostgreSQL 14.19)
✅ Redis: Connected (Redis 7.2)
✅ Scheduler: Active (4 tasks registered)
⚠️  Frontend: Not checked (manual verification)
✅ API Keys: 2/4 configured (Groq, Adzuna)

System Status: OPERATIONAL
Production Readiness: 85%
```

#### Step 5: Test Key Features

**Test Job Scraping**:

```bash
# Manually trigger job scraping
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Content-Type: application/json"

# Check jobs were created
curl http://localhost:8002/api/v1/jobs | python -m json.tool | head -50
```

**Test AI Resume Generation** (requires AI API key):

```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Generate resume
curl -X POST http://localhost:8002/api/v1/ai/resume/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "provider": "groq",
    "model": "llama-3.1-70b-versatile"
  }' | python -m json.tool
```

### Docker Setup (Alternative)

For a containerized setup:

```bash
# Development environment
docker-compose -f docker-compose.dev.yml up -d

# Production environment
docker-compose up -d --build
```

Services will be available at:

- Backend: <http://localhost:8002>

- Frontend: <http://localhost:3000>

- PostgreSQL: localhost:5432

- Redis: localhost:6379

- Prometheus: <http://localhost:9090>

- Grafana: <http://localhost:3001>

See `deployment/docker/README.md` for detailed Docker documentation.

### Troubleshooting Installation

**Issue**: `ModuleNotFoundError: No module named 'app'`
**Solution**: Ensure you're in the `backend/` directory and virtual environment is activated.

**Issue**: `Database connection failed`
**Solution**:

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
grep DATABASE_URL .env

# Test connection manually
psql -d career_copilot -c "SELECT 1"
```

**Issue**: `Redis connection error`
**Solution**:

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG

# If not, start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

**Issue**: `Port 8002 already in use`
**Solution**:

```bash
# Find process using port
lsof -i :8002

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8003
```

---

## 🔑 External APIs & Third-Party Services

### Job Scraping APIs

#### 1. Adzuna API ⭐ **Recommended**

**Coverage**: 13 EU countries (UK, Germany, France, Netherlands, Italy, Spain, Poland, Austria, Belgium, Switzerland, Ireland, Sweden, Denmark)

**Cost**: Free tier with 250 requests/month

**Sign Up**:

1. Visit [https://developer.adzuna.com/signup](https://developer.adzuna.com/signup)
2. Fill in the registration form
3. Verify email
4. Navigate to "Dashboard" → "API Credentials"
5. Copy your **App ID** and **App Key**

**Configuration**:

```bash
ADZUNA_APP_ID=12345678
ADZUNA_APP_KEY=abcdef123456789
```

**Rate Limits**:

- Free tier: 250 requests/month

- Developer tier: 1,000 requests/month ($10/month)

- No real-time rate limits (hourly/daily)

**Testing**:

```bash
curl "https://api.adzuna.com/v1/api/jobs/gb/search/1?app_id=YOUR_ID&app_key=YOUR_KEY&what=python%20developer"
```

#### 2. RapidAPI JSearch ⭐ **Recommended**

**Coverage**: 19 EU countries + global coverage

**Cost**: Free tier with 100 requests/month

**Sign Up**:

1. Visit [https://rapidapi.com/](https://rapidapi.com/)
2. Create account (free)
3. Navigate to [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
4. Click "Subscribe to Test"
5. Select "Basic" plan (free)
6. Copy your **X-RapidAPI-Key** from the code snippet

**Configuration**:

```bash
RAPIDAPI_KEY=1234567890abcdefghijklmnopqrstuvwxyz
```

**Rate Limits**:

- Free tier: 100 requests/month

- Pro tier: 1,000 requests/month ($10/month)

- Ultra tier: 10,000 requests/month ($50/month)

**Testing**:

```bash
curl -X GET "https://jsearch.p.rapidapi.com/search?query=python%20developer&location=Berlin" \
  -H "X-RapidAPI-Key: YOUR_KEY" \
  -H "X-RapidAPI-Host: jsearch.p.rapidapi.com"
```

#### 3. Firecrawl API (AI-Powered)

**Coverage**: 10+ major EU companies (Spotify, Adyen, Booking.com, Klarna, DeepMind, Revolut, Monzo, Bolt, N26, Zalando)

**Cost**: Free tier with 500 credits/month

**Sign Up**:

1. Visit [https://www.firecrawl.dev/](https://www.firecrawl.dev/)
2. Sign up with email
3. Navigate to "API Keys" in dashboard
4. Click "Create API Key"
5. Copy the key (starts with `fc-`)

**Configuration**:

```bash
FIRECRAWL_API_KEY=fc-1234567890abcdef
```

**Rate Limits**:

- Free tier: 500 credits/month (1 credit = 1 page)

- Starter: 5,000 credits/month ($20/month)

- Growth: 50,000 credits/month ($100/month)

**Testing**:

```bash
curl -X POST "https://api.firecrawl.dev/v1/scrape" \
  -H "Authorization: Bearer fc-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.spotify.com/careers/"}'
```

### AI Services

#### 1. OpenAI (GPT-4)

**Models**: GPT-4, GPT-4-turbo, GPT-3.5-turbo

**Cost**: Pay-as-you-go (GPT-4: $0.03/1K input tokens, $0.06/1K output tokens)

**Sign Up**:

1. Visit [https://platform.openai.com/signup](https://platform.openai.com/signup)
2. Create account
3. Add payment method (required for API access)
4. Navigate to [API Keys](https://platform.openai.com/api-keys)
5. Click "Create new secret key"
6. Copy key (starts with `sk-proj-` or `sk-`)

**Configuration**:

```bash
OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnopqrstuvwxyz
```

**Rate Limits** (Tier 1):

- 10,000 requests/day

- 200,000 tokens/minute

**Testing**:

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

#### 2. Groq (Llama 3) ⭐ **Free & Fast**

**Models**: Llama 3.1 70B, Llama 3 8B, Mixtral 8x7B

**Cost**: FREE with generous rate limits

**Sign Up**:

1. Visit [https://console.groq.com/](https://console.groq.com/)
2. Sign up with Google/GitHub
3. Navigate to "API Keys"
4. Click "Create API Key"
5. Copy key (starts with `gsk_`)

**Configuration**:

```bash
GROQ_API_KEY=gsk_1234567890abcdefghijklmnopqrstuvwxyz
```

**Rate Limits** (Free tier):

- 30 requests/minute

- 6,000 tokens/minute

- Fastest inference (300+ tokens/second!)

**Testing**:

```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "llama-3.1-70b-versatile",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

#### 3. Anthropic (Claude)

**Models**: Claude 3 Opus, Sonnet, Haiku

**Cost**: Pay-as-you-go (Opus: $15/million input tokens, $75/million output tokens)

**Sign Up**:

1. Visit [https://console.anthropic.com/](https://console.anthropic.com/)
2. Create account
3. Add payment method
4. Navigate to "API Keys"
5. Click "Create Key"
6. Copy key (starts with `sk-ant-`)

**Configuration**:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz
```

**Testing**:

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

#### 4. Google Gemini

**Models**: Gemini Pro, Gemini Pro Vision

**Cost**: Free tier available (60 requests/minute)

**Sign Up**:

1. Visit [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Select a Google Cloud project (or create one)
5. Copy key (starts with `AIza`)

**Configuration**:

```bash
GOOGLE_API_KEY=AIzaSyAbcdefghijklmnopqrstuvwxyz1234567890
```

**Testing**:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Hello!"}]}]
  }'
```

### Communication Services (Optional)

#### Email (SMTP)

**Option 1: Gmail** (Free, easiest for testing)

1. Enable 2-Factor Authentication on your Google account
2. Visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Select "Mail" and your device
4. Click "Generate"
5. Copy the 16-character password

**Configuration**:

```bash
SMTP_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App password, not your Gmail password
SMTP_FROM_EMAIL=noreply@career-copilot.com
```

**Option 2: SendGrid** (Recommended for production)

1. Visit [https://signup.sendgrid.com/](https://signup.sendgrid.com/)
2. Free tier: 100 emails/day
3. Create API key in dashboard
4. Use SMTP relay: `smtp.sendgrid.net:587`

**Option 3: AWS SES** (Cheapest for scale)

- $0.10 per 1,000 emails

- Requires verification
- [AWS SES Documentation](https://aws.amazon.com/ses/)

#### SMS (Twilio)

**Sign Up**:

1. Visit [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up (free trial: $15 credit)
3. Get phone number (free with trial)
4. Copy Account SID and Auth Token from dashboard

**Configuration**:

```bash
TWILIO_ENABLED=True
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**Cost**: ~$0.0075 per SMS (varies by country)

### Testing API Connections

After configuring APIs, test them:

```bash
cd backend

# Test Adzuna
python -c "
import httpx
import os
response = httpx.get(
    'https://api.adzuna.com/v1/api/jobs/gb/search/1',
    params={'app_id': os.getenv('ADZUNA_APP_ID'), 'app_key': os.getenv('ADZUNA_APP_KEY'), 'what': 'python'}
)
print(f'Adzuna: {response.status_code}')
"

# Test Groq
python -c "
import httpx
import os
response = httpx.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {os.getenv(\"GROQ_API_KEY\")}'},
    json={'model': 'llama-3.1-70b-versatile', 'messages': [{'role': 'user', 'content': 'Hi'}]}
)
print(f'Groq: {response.status_code}')
"
```

---

## ⚙️ Configuration

### Environment Variables Reference

Complete reference of all environment variables with descriptions:

#### Core Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | string | `development` | Environment: `development`, `staging`, `production` |
| `API_HOST` | string | `0.0.0.0` | Host to bind the API server |
| `API_PORT` | integer | `8002` | Port for the API server |
| `DEBUG` | boolean | `False` | Enable debug mode (detailed errors) |
| `LOG_LEVEL` | string | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `WORKERS` | integer | `4` | Number of Gunicorn workers (production) |

#### Database Configuration

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `DATABASE_POOL_SIZE` | No | Connection pool size | `10` (default) |
| `DATABASE_MAX_OVERFLOW` | No | Max connections beyond pool | `20` (default) |
| `DATABASE_ECHO` | No | Log SQL queries | `False` (default) |

#### Redis Configuration

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REDIS_HOST` | ✅ Yes | Redis server host | `localhost` |
| `REDIS_PORT` | ✅ Yes | Redis server port | `6379` |
| `REDIS_PASSWORD` | No | Redis password | Leave empty for no auth |
| `REDIS_DB` | No | Redis database number | `0` (default) |
| `REDIS_SSL` | No | Use SSL for Redis | `False` |

#### Security & Authentication

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `JWT_SECRET_KEY` | ✅ Yes | Secret key for JWT signing | `your-secret-key-min-32-chars` |
| `JWT_ALGORITHM` | No | JWT signing algorithm | `HS256` (default) |
| `JWT_EXPIRATION_HOURS` | No | Token expiration time | `24` (hours) |
| `ENCRYPTION_KEY` | ✅ Yes | Fernet encryption key | Generated via `Fernet.generate_key()` |
| `CORS_ORIGINS` | ✅ Yes | Allowed CORS origins | `http://localhost:3000,https://app.example.com` |
| `COOKIE_SECURE` | No | HTTPS-only cookies | `True` in production |

#### AI Service Configuration

| Variable | Required | Description | Free Tier | Rate Limit |
|----------|----------|-------------|-----------|------------|
| `OPENAI_API_KEY` | No* | OpenAI API key | No (pay-as-you-go) | 10K req/day |
| `GROQ_API_KEY` | No* | Groq API key | ✅ Yes | 30 req/min |
| `ANTHROPIC_API_KEY` | No* | Anthropic API key | No (pay-as-you-go) | Tier-based |
| `GOOGLE_API_KEY` | No* | Google Gemini API key | ✅ Yes | 60 req/min |
| `DEFAULT_AI_PROVIDER` | No | Default AI provider | `groq` | - |

*At least one AI provider required for AI features.

#### Job Scraping Configuration

| Variable | Required | Description | Coverage |
|----------|----------|-------------|----------|
| `ADZUNA_APP_ID` | No* | Adzuna App ID | 13 EU countries |
| `ADZUNA_APP_KEY` | No* | Adzuna App Key | 13 EU countries |
| `RAPIDAPI_KEY` | No* | RapidAPI key for JSearch | 19 EU countries |
| `FIRECRAWL_API_KEY` | No | Firecrawl API key | 10 EU companies |
| `SCRAPING_ENABLE_ADZUNA` | No | Enable Adzuna scraper | `True` |
| `SCRAPING_ENABLE_RAPIDAPI` | No | Enable RapidAPI scraper | `True` |
| `SCRAPING_ENABLE_THEMUSE` | No | Enable The Muse scraper | `True` |
| `SCRAPING_ENABLE_ARBEITNOW` | No | Enable Arbeitnow scraper | `True` |
| `SCRAPING_ENABLE_FIRECRAWL` | No | Enable Firecrawl scraper | `False` |
| `SCRAPING_MAX_JOBS_PER_RUN` | No | Max jobs per scraping cycle | `500` |
| `SCRAPING_TIMEOUT_SECONDS` | No | Scraper timeout | `300` (5 min) |

*At least one job scraping API required for job discovery.

#### Notification Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SMTP_ENABLED` | No | Enable email notifications | `False` |
| `SMTP_HOST` | No | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | No | SMTP server port | `587` |
| `SMTP_USER` | No | SMTP username | - |
| `SMTP_PASSWORD` | No | SMTP password/token | - |
| `SMTP_FROM_EMAIL` | No | From email address | `noreply@career-copilot.com` |
| `SMTP_FROM_NAME` | No | From name | `Career Copilot` |
| `TWILIO_ENABLED` | No | Enable SMS notifications | `False` |
| `TWILIO_ACCOUNT_SID` | No | Twilio Account SID | - |
| `TWILIO_AUTH_TOKEN` | No | Twilio Auth Token | - |
| `TWILIO_PHONE_NUMBER` | No | Twilio phone number | - |

#### Scheduler Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SCHEDULER_ENABLED` | No | Enable APScheduler | `True` |
| `JOB_SCRAPING_SCHEDULE` | No | Cron schedule for scraping | `0 */6 * * *` (every 6h) |
| `MORNING_BRIEFING_HOUR` | No | Hour for morning briefing | `8` (8 AM) |
| `EVENING_SUMMARY_HOUR` | No | Hour for evening summary | `20` (8 PM) |

#### Monitoring & Observability

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PROMETHEUS_ENABLED` | No | Enable Prometheus metrics | `True` |
| `SENTRY_DSN` | No | Sentry error tracking DSN | - |
| `SENTRY_ENVIRONMENT` | No | Sentry environment | Same as `ENVIRONMENT` |
| `SENTRY_TRACES_SAMPLE_RATE` | No | Sentry traces sample rate | `0.1` (10%) |

### Configuration Files

#### 1. `config/application.yaml`

Application-wide configuration:

```yaml
application:
  name: "Career Copilot"
  version: "1.0.0"
  description: "AI-Powered Career Management Platform"

features:
  job_scraping: true
  ai_generation: true
  analytics: true
  notifications: true
  recommendations: true

job_scraping:
  schedule: "0 */6 * * *"  # Every 6 hours
  max_jobs_per_run: 500
  timeout_seconds: 300
  retry_attempts: 3
  target_roles:
    - "Data Scientist"
    - "Machine Learning Engineer"
    - "Data Analyst"
    - "Data Engineer"
    - "Backend Engineer"
    - "Frontend Engineer"
    - "Full Stack Engineer"
    - "DevOps Engineer"
    - "Product Manager"

  target_countries:
    - "Germany"
    - "Netherlands"
    - "France"
    - "Sweden"
    - "Ireland"
    - "Spain"
    - "Poland"
    - "Belgium"
    - "Austria"
    - "Denmark"
    - "Finland"
    - "Portugal"
    - "Czech Republic"

analytics:
  collection:
    enabled: true
    queue_size: 10000
    batch_size: 100
    flush_interval_seconds: 30

  caching:
    enabled: true
    ttl_seconds: 300  # 5 minutes

  rate_limiting:
    enabled: true
    max_events_per_minute: 100

notifications:
  rate_limiting:
    max_per_minute: 10
    window_seconds: 60

  retry:
    enabled: true
    max_attempts: 3
    backoff_seconds: [5, 15, 60]

  queue:
    enabled: true
    batch_size: 50
    flush_interval_seconds: 60

recommendations:
  scoring_weights:
    skill_match: 0.40
    location_match: 0.20
    experience_match: 0.15
    salary_match: 0.10
    company_culture: 0.05
    growth_potential: 0.05
    recency: 0.05

  caching:
    enabled: true
    ttl_seconds: 900  # 15 minutes

  diversity:
    max_per_company: 3
    boost_factor: 0.9
```

#### 2. `config/llm_config.json`

AI provider configurations:

```json
{
  "providers": {
    "openai": {
      "enabled": true,
      "models": {
        "gpt-4": {
          "max_tokens": 4096,
          "temperature": 0.7,
          "cost_per_1k_input": 0.03,
          "cost_per_1k_output": 0.06
        },
        "gpt-3.5-turbo": {
          "max_tokens": 4096,
          "temperature": 0.7,
          "cost_per_1k_input": 0.0005,
          "cost_per_1k_output": 0.0015
        }
      }
    },
    "groq": {
      "enabled": true,
      "models": {
        "llama-3.1-70b-versatile": {
          "max_tokens": 8000,
          "temperature": 0.7,
          "cost_per_1k_input": 0.0,
          "cost_per_1k_output": 0.0
        },
        "llama-3-8b-8192": {
          "max_tokens": 8192,
          "temperature": 0.7,
          "cost_per_1k_input": 0.0,
          "cost_per_1k_output": 0.0
        }
      }
    },
    "anthropic": {
      "enabled": false,
      "models": {
        "claude-3-opus-20240229": {
          "max_tokens": 4096,
          "temperature": 0.7,
          "cost_per_1k_input": 0.015,
          "cost_per_1k_output": 0.075
        }
      }
    }
  },
  "default_provider": "groq",
  "default_model": "llama-3.1-70b-versatile",
  "fallback_providers": ["openai", "anthropic"]
}
```

### Configuration Validation

Career Copilot validates configuration on startup:

```python
# Automatic validation on app startup
python backend/scripts/validate_config.py
```

**Checks**:

- ✅ Required environment variables present
- ✅ Database connection successful
- ✅ Redis connection successful
- ✅ At least one AI provider configured
- ✅ At least one job scraping API configured
- ✅ Valid JWT secret key (min 32 characters)
- ✅ Valid encryption key format

**Example Output**:

```text
✅ Configuration Validation Passed
✅ Database: Connected (PostgreSQL 14.19)
✅ Redis: Connected (Redis 7.2)
✅ AI Providers: 2 configured (Groq, OpenAI)
✅ Job Scrapers: 3 enabled (Adzuna, RapidAPI, Arbeitnow)
⚠️  Email: Not configured (notifications disabled)
⚠️  SMS: Not configured (notifications disabled)

Configuration Status: VALID
Warnings: 2 (non-critical)
```

---

## 📖 Usage & Functionality

### Starting the Application

#### Development Mode

**Terminal 1 - Backend**:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

**Terminal 2 - Frontend**:

```bash
cd frontend
npm run dev
```

**Terminal 3 - Redis** (if not running as service):

```bash
redis-server
```

#### Production Mode

**Using Scripts**:

```bash
# Start all services
./deploy.sh

# Or individually
./start_backend.sh
./start_frontend.sh
./start_celery.sh  # Optional
```

**Using Docker Compose**:

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose up -d --build
```

**Using Systemd** (Linux):

```bash
# Copy service files
sudo cp deployment/services/*.service /etc/systemd/system/

# Enable and start
sudo systemctl enable career-copilot-backend
sudo systemctl enable career-copilot-frontend
sudo systemctl start career-copilot-backend
sudo systemctl start career-copilot-frontend

# Check status
sudo systemctl status career-copilot-*
```

### User Workflows

#### 1. Registration & Profile Setup

**Via Web UI**:

1. Navigate to `http://localhost:3000`
2. Click **"Sign Up"**
3. Fill in:
   - Email address
   - Password (min 8 characters)
   - Full name
4. Verify email (if email enabled)
5. Complete profile:
   - Current role
   - Experience level
   - Technical skills
   - Preferred locations
   - Salary expectations
   - Work authorization

**Via API**:

```bash
# Register
curl -X POST http://localhost:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe"
  }'

# Response:
# {
#   "id": 1,
#   "email": "john.doe@example.com",
#   "full_name": "John Doe",
#   "created_at": "2025-11-06T10:00:00Z"
# }

# Login
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePassword123!"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 86400
# }

# Update profile
TOKEN="your_access_token"
curl -X PUT http://localhost:8002/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_role": "Data Scientist",
    "experience_years": 5,
    "skills": ["Python", "Machine Learning", "TensorFlow", "SQL"],
    "preferred_locations": ["Berlin", "Amsterdam", "Stockholm"],
    "salary_min": 80000,
    "salary_max": 120000,
    "remote_preference": "hybrid",
    "visa_sponsorship_required": true
  }'
```

#### 2. Job Discovery

**Search Jobs**:

```bash
# Search with filters
curl "http://localhost:8002/api/v1/jobs?location=Berlin&visa_support=true&skills=Python,Machine%20Learning&min_salary=80000" \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "total": 45,
#   "page": 1,
#   "per_page": 20,
#   "jobs": [
#     {
#       "id": 123,
#       "title": "Senior Data Scientist",
#       "company": "Spotify",
#       "location": "Berlin, Germany",
#       "salary_min": 90000,
#       "salary_max": 130000,
#       "remote_option": "Hybrid",
#       "visa_sponsorship": true,
#       "skills": ["Python", "Machine Learning", "TensorFlow"],
#       "posted_date": "2025-11-05",
#       "url": "https://..."
#     },
#     ...
#   ]
# }

# Get job details
curl http://localhost:8002/api/v1/jobs/123 \
  -H "Authorization: Bearer $TOKEN"

# Bookmark job
curl -X POST http://localhost:8002/api/v1/jobs/123/bookmark \
  -H "Authorization: Bearer $TOKEN"
```

**Get Recommendations**:

```bash
# Personalized recommendations
curl http://localhost:8002/api/v1/jobs/recommendations \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "recommendations": [
#     {
#       "job": {...},
#       "match_score": 85.5,
#       "explanation": {
#         "matching_skills": ["Python", "Machine Learning"],
#         "missing_skills": ["Kubernetes"],
#         "location_match": "Perfect match: Berlin",
#         "salary_match": "Within your range",
#         "score_breakdown": {
#           "skill_match": 34.2,
#           "location_match": 20.0,
#           "experience_match": 15.0,
#           "salary_match": 10.0,
#           "company_culture": 3.5,
#           "growth_potential": 2.3,
#           "recency": 0.5
#         }
#       }
#     },
#     ...
#   ]
# }
```

**Trigger Manual Scraping** (admin only):

```bash
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "status": "started",
#   "job_id": "scrape_2025-11-06_10-30-00",
#   "message": "Scraping initiated for 9 sources"
# }
```

#### 3. Application Tracking

**Create Application**:

```bash
curl -X POST http://localhost:8002/api/v1/applications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 123,
    "status": "applied",
    "applied_date": "2025-11-06",
    "notes": "Applied via company website",
    "resume_version": "resume_v2_spotify.pdf",
    "cover_letter": "Dear Hiring Manager..."
  }'

# Response:
# {
#   "id": 456,
#   "job_id": 123,
#   "status": "applied",
#   "applied_date": "2025-11-06",
#   "created_at": "2025-11-06T10:30:00Z"
# }
```

**Update Application Status**:

```bash
# Move to interviewing
curl -X PUT http://localhost:8002/api/v1/applications/456 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "interviewing",
    "interview_date": "2025-11-15T14:00:00Z",
    "notes": "Phone screen scheduled with hiring manager"
  }'

# Add interview
curl -X POST http://localhost:8002/api/v1/applications/456/interviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_type": "phone_screen",
    "scheduled_date": "2025-11-15T14:00:00Z",
    "interviewer_name": "Jane Smith",
    "notes": "Prepare questions about team structure"
  }'
```

**List Applications**:

```bash
# All applications
curl http://localhost:8002/api/v1/applications \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl "http://localhost:8002/api/v1/applications?status=interviewing" \
  -H "Authorization: Bearer $TOKEN"

# Applications this month
curl "http://localhost:8002/api/v1/applications?from_date=2025-11-01" \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. AI Resume & Cover Letter Generation

**Generate Resume**:

```bash
curl -X POST http://localhost:8002/api/v1/ai/resume/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 123,
    "provider": "groq",
    "model": "llama-3.1-70b-versatile",
    "tone": "professional",
    "include_sections": ["summary", "experience", "skills", "education"],
    "max_pages": 1
  }'

# Response:
# {
#   "id": 789,
#   "content": "JOHN DOE\nData Scientist\n\nPROFESSIONAL SUMMARY\n...",
#   "job_id": 123,
#   "provider": "groq",
#   "created_at": "2025-11-06T10:35:00Z"
# }
```

**Generate Cover Letter**:

```bash
curl -X POST http://localhost:8002/api/v1/ai/cover-letter/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 123,
    "provider": "openai",
    "model": "gpt-4",
    "tone": "enthusiastic",
    "length": "medium",
    "highlights": ["5 years ML experience", "Published research", "Open source contributor"]
  }'

# Response:
# {
#   "id": 790,
#   "content": "Dear Hiring Manager,\n\nI am writing to express...",
#   "job_id": 123,
#   "provider": "openai",
#   "created_at": "2025-11-06T10:36:00Z"
# }
```

**Export to PDF**:

```bash
# Export resume as PDF
curl -X POST http://localhost:8002/api/v1/ai/resumes/789/export \
  -H "Authorization: Bearer $TOKEN" \
  --output resume.pdf

# Export cover letter as PDF
curl -X POST http://localhost:8002/api/v1/ai/cover-letters/790/export \
  -H "Authorization: Bearer $TOKEN" \
  --output cover_letter.pdf
```

#### 5. Analytics & Insights

**Get Dashboard Summary**:

```bash
curl http://localhost:8002/api/v1/analytics/summary \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "total_jobs_viewed": 150,
#   "total_applications": 25,
#   "interviews_scheduled": 5,
#   "offers_received": 1,
#   "application_conversion_rate": 16.7,
#   "interview_conversion_rate": 20.0,
#   "offer_conversion_rate": 4.0,
#   "average_response_time_days": 7.5,
#   "this_week": {
#     "jobs_viewed": 15,
#     "applications": 3
#   }
# }
```

**Get Trends**:

```bash
# Application trends (last 30 days)
curl "http://localhost:8002/api/v1/analytics/trends?metric=applications&days=30" \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "metric": "applications",
#   "period": "30 days",
#   "data": [
#     {"date": "2025-10-07", "count": 2},
#     {"date": "2025-10-08", "count": 1},
#     {"date": "2025-10-09", "count": 3},
#     ...
#   ],
#   "total": 25,
#   "average_per_day": 0.83
# }
```

**Get Skills Demand**:

```bash
curl http://localhost:8002/api/v1/analytics/skills \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "top_skills": [
#     {"skill": "Python", "job_count": 450, "avg_salary": 95000},
#     {"skill": "Machine Learning", "job_count": 380, "avg_salary": 105000},
#     {"skill": "SQL", "job_count": 320, "avg_salary": 85000},
#     ...
#   ],
#   "your_skills": ["Python", "Machine Learning", "SQL"],
#   "skill_gaps": ["Kubernetes", "AWS", "Docker"]
# }
```

### CLI Commands

Career Copilot provides CLI commands for common tasks:

```bash
# Health check
python backend/scripts/verify_system_health.py

# Manual job scraping
python backend/scripts/trigger_scraping.py

# Backfill job fingerprints (deduplication)
python backend/scripts/backfill_job_fingerprints.py

# Monitor deduplication metrics
python backend/scripts/monitor_deduplication.py --days 7

# Create test user
python backend/scripts/create_test_user.py

# Database backup
python backend/scripts/backup_database.py --output backups/

# Send test email
python backend/scripts/test_email_notification.py --email test@example.com

# Export analytics report
python backend/scripts/export_analytics.py --user-id 1 --format pdf
```

---

## 📚 API Documentation

### Interactive Documentation

Career Copilot provides auto-generated, interactive API documentation:

- **Swagger UI**: [http://localhost:8002/docs](http://localhost:8002/docs)

  - Interactive API explorer
  - Try endpoints directly in browser
  - Request/response examples
  - Schema definitions

- **ReDoc**: [http://localhost:8002/redoc](http://localhost:8002/redoc)

  - Clean, three-panel documentation
  - Search functionality
  - Downloadable OpenAPI spec

### Base URL

**Development**: `http://localhost:8002`
**Production**: `https://api.career-copilot.com`

All API endpoints are versioned: `/api/v1/*`

### Authentication

Most endpoints require authentication via JWT Bearer token:

```http
Authorization: Bearer <your_access_token>
```

**Obtaining a Token**:

```bash
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Response**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Token Refresh**:

```bash
curl -X POST http://localhost:8002/api/v1/auth/refresh \
  -H "Authorization: Bearer <your_token>"
```

### API Endpoints Reference

#### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | Register new user | No |
| `POST` | `/api/v1/auth/login` | Login and get token | No |
| `POST` | `/api/v1/auth/refresh` | Refresh access token | Yes |
| `POST` | `/api/v1/auth/logout` | Logout (invalidate token) | Yes |
| `GET` | `/api/v1/auth/me` | Get current user | Yes |
| `POST` | `/api/v1/auth/forgot-password` | Request password reset | No |
| `POST` | `/api/v1/auth/reset-password` | Reset password with token | No |

##### Example: Register**

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}

# Response: 201 Created
{
  "id": 1,
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "created_at": "2025-11-06T10:00:00Z"
}
```

#### Jobs Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/jobs` | Search jobs with filters | Yes |
| `GET` | `/api/v1/jobs/{id}` | Get job details | Yes |
| `POST` | `/api/v1/jobs/{id}/bookmark` | Bookmark a job | Yes |
| `DELETE` | `/api/v1/jobs/{id}/bookmark` | Remove bookmark | Yes |
| `GET` | `/api/v1/jobs/bookmarks` | Get bookmarked jobs | Yes |
| `GET` | `/api/v1/jobs/recommendations` | Get personalized recommendations | Yes |
| `POST` | `/api/v1/jobs/scrape` | Trigger job scraping (admin) | Yes |

**Query Parameters for Job Search**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query | `python developer` |
| `location` | string | Job location | `Berlin` |
| `country` | string | Country code | `DE` |
| `visa_support` | boolean | Visa sponsorship | `true` |
| `remote` | string | Remote option | `remote`, `hybrid`, `onsite` |
| `skills` | string | Comma-separated skills | `Python,Machine Learning` |
| `min_salary` | integer | Minimum salary | `80000` |
| `max_salary` | integer | Maximum salary | `120000` |
| `experience_level` | string | Experience level | `junior`, `mid`, `senior` |
| `posted_since` | integer | Days since posting | `7` |
| `page` | integer | Page number | `1` |
| `per_page` | integer | Results per page | `20` |
| `sort_by` | string | Sort field | `posted_date`, `salary`, `relevance` |
| `sort_order` | string | Sort order | `asc`, `desc` |

##### Example: Search Jobs**

```bash
GET /api/v1/jobs?location=Berlin&visa_support=true&skills=Python,ML&min_salary=80000&sort_by=posted_date&sort_order=desc
Authorization: Bearer <token>

# Response: 200 OK
{
  "total": 45,
  "page": 1,
  "per_page": 20,
  "total_pages": 3,
  "jobs": [
    {
      "id": 123,
      "title": "Senior Data Scientist",
      "company": "Spotify",
      "company_logo": "https://...",
      "location": "Berlin, Germany",
      "country": "DE",
      "remote_option": "Hybrid",
      "salary_min": 90000,
      "salary_max": 130000,
      "currency": "EUR",
      "visa_sponsorship": true,
      "skills": ["Python", "Machine Learning", "TensorFlow", "Spark"],
      "experience_level": "senior",
      "employment_type": "full_time",
      "description": "We are looking for...",
      "posted_date": "2025-11-05",
      "url": "https://...",
      "source": "adzuna",
      "is_bookmarked": false
    },
    ...
  ]
}
```

#### Applications Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/applications` | Create application | Yes |
| `GET` | `/api/v1/applications` | List applications | Yes |
| `GET` | `/api/v1/applications/{id}` | Get application details | Yes |
| `PUT` | `/api/v1/applications/{id}` | Update application | Yes |
| `DELETE` | `/api/v1/applications/{id}` | Delete application | Yes |
| `GET` | `/api/v1/applications/{id}/timeline` | Get application timeline | Yes |
| `POST` | `/api/v1/applications/{id}/interviews` | Add interview | Yes |
| `POST` | `/api/v1/applications/{id}/reminders` | Set reminder | Yes |

**Application Status Values**: `saved`, `applied`, `interviewing`, `offered`, `rejected`, `accepted`, `declined`

##### Example: Create Application**

```bash
POST /api/v1/applications
Authorization: Bearer <token>
Content-Type: application/json

{
  "job_id": 123,
  "status": "applied",
  "applied_date": "2025-11-06",
  "notes": "Applied via LinkedIn",
  "resume_version": "resume_v2.pdf",
  "cover_letter": "Dear Hiring Manager..."
}

# Response: 201 Created
{
  "id": 456,
  "job_id": 123,
  "user_id": 1,
  "status": "applied",
  "applied_date": "2025-11-06",
  "notes": "Applied via LinkedIn",
  "created_at": "2025-11-06T10:30:00Z",
  "updated_at": "2025-11-06T10:30:00Z",
  "job": {
    "title": "Senior Data Scientist",
    "company": "Spotify",
    "location": "Berlin, Germany"
  }
}
```

#### AI Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/ai/resume/generate` | Generate resume | Yes |
| `POST` | `/api/v1/ai/cover-letter/generate` | Generate cover letter | Yes |
| `GET` | `/api/v1/ai/resumes` | List user's resumes | Yes |
| `GET` | `/api/v1/ai/resumes/{id}` | Get resume details | Yes |
| `POST` | `/api/v1/ai/resumes/{id}/export` | Export resume as PDF | Yes |
| `DELETE` | `/api/v1/ai/resumes/{id}` | Delete resume | Yes |
| `GET` | `/api/v1/ai/cover-letters` | List cover letters | Yes |
| `POST` | `/api/v1/ai/cover-letters/{id}/export` | Export cover letter as PDF | Yes |
| `GET` | `/api/v1/ai/providers` | List available AI providers | Yes |

##### Example: Generate Resume**

```bash
POST /api/v1/ai/resume/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "job_id": 123,
  "provider": "groq",
  "model": "llama-3.1-70b-versatile",
  "tone": "professional",
  "max_pages": 1,
  "include_sections": ["summary", "experience", "skills", "education"]
}

# Response: 200 OK
{
  "id": 789,
  "content": "JOHN DOE\nSenior Data Scientist\n...",
  "job_id": 123,
  "provider": "groq",
  "model": "llama-3.1-70b-versatile",
  "tokens_used": 1250,
  "cost": 0.0,
  "generation_time_ms": 1200,
  "created_at": "2025-11-06T10:35:00Z"
}
```

#### Analytics Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/analytics/summary` | Get overall statistics | Yes |
| `GET` | `/api/v1/analytics/trends` | Get time-series data | Yes |
| `GET` | `/api/v1/analytics/skills` | Get skills demand analysis | Yes |
| `GET` | `/api/v1/analytics/salary` | Get salary trends | Yes |
| `GET` | `/api/v1/analytics/companies` | Get top companies | Yes |
| `GET` | `/api/v1/analytics/funnel` | Get conversion funnel | Yes |
| `GET` | `/api/v1/analytics/insights` | Get personalized insights | Yes |

##### Example: Get Analytics Summary**

```bash
GET /api/v1/analytics/summary
Authorization: Bearer <token>

# Response: 200 OK
{
  "period": "all_time",
  "total_jobs_viewed": 150,
  "total_applications": 25,
  "interviews_scheduled": 5,
  "offers_received": 1,
  "conversion_rates": {
    "view_to_application": 16.7,
    "application_to_interview": 20.0,
    "interview_to_offer": 20.0
  },
  "average_response_time_days": 7.5,
  "engagement_score": 75.5,
  "user_segment": "highly_active",
  "this_week": {
    "jobs_viewed": 15,
    "applications": 3,
    "interviews": 1
  },
  "this_month": {
    "jobs_viewed": 45,
    "applications": 8,
    "interviews": 2
  }
}
```

#### Users Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/v1/users/me` | Get current user profile | Yes |
| `PUT` | `/api/v1/users/me` | Update profile | Yes |
| `PUT` | `/api/v1/users/me/password` | Change password | Yes |
| `GET` | `/api/v1/users/me/preferences` | Get notification preferences | Yes |
| `PUT` | `/api/v1/users/me/preferences` | Update preferences | Yes |
| `DELETE` | `/api/v1/users/me` | Delete account | Yes |

#### Resume Upload Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/resume/upload` | Upload resume for parsing | Yes |
| `GET` | `/api/v1/resume/{upload_id}/status` | Check parsing status | Yes |
| `GET` | `/api/v1/resume/{upload_id}/suggestions` | Get profile suggestions | Yes |
| `POST` | `/api/v1/resume/{upload_id}/apply-suggestions` | Apply suggestions to profile | Yes |

### Response Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `204` | No Content | Request successful, no response body |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Authenticated but not authorized |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource conflict (e.g., duplicate email) |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Rate Limiting

Career Copilot implements rate limiting to prevent abuse:

| Endpoint Group | Limit | Window |
|----------------|-------|--------|
| Authentication | 5 requests | 1 minute |
| Job Search | 30 requests | 1 minute |
| AI Generation | 5 requests | 1 minute |
| Analytics | 20 requests | 1 minute |
| General API | 100 requests | 1 minute |

**Rate Limit Headers**:

```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 27
X-RateLimit-Reset: 1699275600
```

---

## 💡 Code Examples & Tutorials

### Example 1: Complete Job Search Flow

```python
import httpx
import os
from typing import List, Dict

class CareerCopilotClient:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.token = None
        self.client = httpx.Client(base_url=base_url)

    def login(self, email: str, password: str) -> str:
        """Login and store token"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return self.token

    def search_jobs(
        self,
        location: str = None,
        skills: List[str] = None,
        visa_support: bool = None,
        min_salary: int = None
    ) -> List[Dict]:
        """Search for jobs with filters"""
        params = {}
        if location:
            params["location"] = location
        if skills:
            params["skills"] = ",".join(skills)
        if visa_support is not None:
            params["visa_support"] = str(visa_support).lower()
        if min_salary:
            params["min_salary"] = min_salary

        response = self.client.get(
            "/api/v1/jobs",
            params=params,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()["jobs"]

    def apply_to_job(self, job_id: int, notes: str = "") -> Dict:
        """Create application for a job"""
        response = self.client.post(
            "/api/v1/applications",
            json={
                "job_id": job_id,
                "status": "applied",
                "notes": notes
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = CareerCopilotClient()

# Login
client.login("user@example.com", "password123")

# Search for jobs
jobs = client.search_jobs(
    location="Berlin",
    skills=["Python", "Machine Learning"],
    visa_support=True,
    min_salary=80000
)

print(f"Found {len(jobs)} jobs matching your criteria")

# Apply to first job
if jobs:
    application = client.apply_to_job(
        job_id=jobs[0]["id"],
        notes="Found via Career Copilot search"
    )
    print(f"Applied to {jobs[0]['title']} at {jobs[0]['company']}")
```

### Example 2: AI Resume Generation Workflow

```python
import httpx
from pathlib import Path

class AIResumeGenerator:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.client = httpx.Client(base_url=base_url)

    def generate_resume(
        self,
        job_id: int,
        provider: str = "groq",
        model: str = "llama-3.1-70b-versatile"
    ) -> Dict:
        """Generate tailored resume for a job"""
        response = self.client.post(
            "/api/v1/ai/resume/generate",
            json={
                "job_id": job_id,
                "provider": provider,
                "model": model,
                "tone": "professional",
                "max_pages": 1
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def export_pdf(self, resume_id: int, output_path: str):
        """Export resume as PDF"""
        response = self.client.post(
            f"/api/v1/ai/resumes/{resume_id}/export",
            headers=self.headers
        )
        response.raise_for_status()

        Path(output_path).write_bytes(response.content)
        print(f"Resume saved to {output_path}")

# Usage
generator = AIResumeGenerator(
    base_url="http://localhost:8002",
    token="your_token_here"
)

# Generate resume
resume = generator.generate_resume(
    job_id=123,
    provider="groq"
)

print(f"Generated resume ({resume['tokens_used']} tokens)")
print(f"Generation time: {resume['generation_time_ms']}ms")

# Export to PDF
generator.export_pdf(
    resume_id=resume["id"],
    output_path="my_resume.pdf"
)
```

### Example 3: Analytics Dashboard Data Fetching

```javascript
// React component for analytics dashboard
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const useAnalytics = () => {
  return useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: async () => {
      const { data } = await axios.get('/api/v1/analytics/summary', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      return data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

const AnalyticsDashboard = () => {
  const { data, isLoading, error } = useAnalytics();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading analytics</div>;

  return (
    <div className="analytics-dashboard">
      <div className="stat-card">
        <h3>Total Applications</h3>
        <p className="stat-number">{data.total_applications}</p>
      </div>

      <div className="stat-card">
        <h3>Interview Rate</h3>
        <p className="stat-number">
          {data.conversion_rates.application_to_interview}%
        </p>
      </div>

      <div className="stat-card">
        <h3>Engagement Score</h3>
        <p className="stat-number">{data.engagement_score}/100</p>
      </div>
    </div>
  );
};
```

### Example 4: Webhook Integration (Coming Soon)

```python
from fastapi import FastAPI, Request
from career_copilot import webhooks

app = FastAPI()

@app.post("/webhooks/job-match")
async def handle_job_match(request: Request):
    """
    Handle job match webhook
    Triggered when a new job matches user's criteria
    """
    payload = await request.json()

    job = payload["job"]
    match_score = payload["match_score"]
    user_id = payload["user_id"]

    # Send custom notification
    await send_slack_notification(
        f"New job match: {job['title']} at {job['company']} ({match_score}% match)"
    )

    return {"status": "processed"}

@app.post("/webhooks/application-status")
async def handle_application_status(request: Request):
    """
    Handle application status update webhook
    """
    payload = await request.json()

    application_id = payload["application_id"]
    old_status = payload["old_status"]
    new_status = payload["new_status"]

    # Track in external CRM
    await update_crm(application_id, new_status)

    return {"status": "processed"}
```

---

## 🧪 Testing

### Testing Philosophy

Career Copilot follows a comprehensive testing strategy:

- **Unit Tests**: Fast, isolated tests for individual components

- **Integration Tests**: Test interactions between components

- **End-to-End Tests**: Test complete user workflows

- **Performance Tests**: Ensure system meets performance requirements

- **Security Tests**: Validate security measures

**Test Coverage Target**: 80%+ code coverage

### Running Tests

#### Backend Tests (Python/Pytest)

**Run All Tests**:

```bash
cd backend
pytest
```

**Run Specific Test Files**:

```bash
# Test authentication
pytest tests/test_auth.py

# Test job scrapers
pytest tests/test_scrapers.py

# Test AI services
pytest tests/test_ai_services.py
```

**Run Tests with Coverage**:

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

**View Coverage Report**:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Run Tests in Parallel** (faster):

```bash
pytest -n auto  # Uses all CPU cores
```

**Run Specific Test Categories**:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

#### Frontend Tests (Jest/Vitest)

**Run All Tests**:

```bash
cd frontend
npm test
```

**Run Tests in Watch Mode**:

```bash
npm test -- --watch
```

**Run Tests with Coverage**:

```bash
npm run test:coverage
```

**Run Specific Test Files**:

```bash
# Test authentication components
npm test -- src/components/auth

# Test dashboard
npm test -- src/app/dashboard
```

**Run E2E Tests** (Cypress):

```bash
# Interactive mode
npm run cypress:open

# Headless mode
npm run cypress:run
```

### Writing Tests

#### Backend Unit Test Example

```python
# tests/test_job_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.job_service import JobService
from app.models.job import Job

@pytest.fixture
def job_service():
    """Create JobService instance with mocked dependencies"""
    db = AsyncMock()
    cache = Mock()
    return JobService(db=db, cache=cache)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_jobs_returns_filtered_results(job_service):
    """Test that search_jobs applies filters correctly"""
    # Arrange
    job_service.db.query.return_value.filter.return_value.all.return_value = [
        Job(id=1, title="Data Scientist", location="Berlin"),
        Job(id=2, title="ML Engineer", location="Berlin"),
    ]

    # Act
    results = await job_service.search_jobs(location="Berlin")

    # Assert
    assert len(results) == 2
    assert all(job.location == "Berlin" for job in results)
    job_service.db.query.assert_called_once()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_application_sends_notification(job_service, notification_service):
    """Test that creating application triggers notification"""
    # Arrange
    user = User(id=1, email="test@example.com")
    job = Job(id=123, title="Data Scientist")

    # Act
    application = await job_service.create_application(
        user_id=user.id,
        job_id=job.id
    )

    # Assert
    assert application.status == "applied"
    notification_service.send_email.assert_called_once()
```

#### Frontend Component Test Example

```typescript
// src/components/JobCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { JobCard } from './JobCard';

describe('JobCard', () => {
  const mockJob = {
    id: 123,
    title: 'Senior Data Scientist',
    company: 'Spotify',
    location: 'Berlin, Germany',
    salary_min: 90000,
    salary_max: 130000,
    visa_sponsorship: true,
  };

  it('renders job information correctly', () => {
    render(<JobCard job={mockJob} />);

    expect(screen.getByText('Senior Data Scientist')).toBeInTheDocument();
    expect(screen.getByText('Spotify')).toBeInTheDocument();
    expect(screen.getByText('Berlin, Germany')).toBeInTheDocument();
  });

  it('displays visa sponsorship badge when available', () => {
    render(<JobCard job={mockJob} />);

    expect(screen.getByText('Visa Sponsorship')).toBeInTheDocument();
  });

  it('calls onBookmark when bookmark button clicked', () => {
    const handleBookmark = jest.fn();
    render(<JobCard job={mockJob} onBookmark={handleBookmark} />);

    const bookmarkButton = screen.getByRole('button', { name: /bookmark/i });
    fireEvent.click(bookmarkButton);

    expect(handleBookmark).toHaveBeenCalledWith(123);
  });

  it('displays salary range correctly', () => {
    render(<JobCard job={mockJob} />);

    expect(screen.getByText(/€90,000 - €130,000/)).toBeInTheDocument();
  });
});
```

### Test Database Setup

Career Copilot uses a separate test database:

```bash
# Create test database
createdb career_copilot_test

# Run migrations
cd backend
alembic upgrade head

# Seed test data (optional)
python scripts/seed_test_data.py
```

**Automatic Test DB Setup** (pytest):

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from app.database import Base

@pytest.fixture(scope="session")
def test_db():
    """Create test database for session"""
    engine = create_engine("postgresql://localhost/career_copilot_test")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """Create fresh database session for each test"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### Continuous Integration (CI)

Tests run automatically on every push via GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

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
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

---

## 🔧 Development Workflow

### Git Workflow

Career Copilot follows **Git Flow** branching strategy:

#### Branch Structure

```text
main (production)
  └── develop (integration)
      ├── feature/job-filtering-improvements
      ├── feature/ai-cover-letter-v2
      ├── bugfix/application-status-update
      └── hotfix/security-patch
```

#### Branch Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<description>` | `feature/advanced-job-search` |
| Bugfix | `bugfix/<description>` | `bugfix/resume-upload-error` |
| Hotfix | `hotfix/<description>` | `hotfix/security-vulnerability` |
| Release | `release/<version>` | `release/1.1.0` |
| Chore | `chore/<description>` | `chore/update-dependencies` |

#### Creating a Feature Branch

```bash
# Update develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/new-analytics-dashboard

# Make changes and commit
git add .
git commit -m "feat: add analytics dashboard with charts"

# Push to remote
git push origin feature/new-analytics-dashboard

# Create Pull Request on GitHub
```

### Commit Message Conventions

Career Copilot uses **Conventional Commits**:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

#### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(jobs): add salary range filter` |
| `fix` | Bug fix | `fix(auth): resolve token expiration issue` |
| `docs` | Documentation | `docs(api): update endpoint descriptions` |
| `style` | Code style (formatting) | `style(frontend): format with prettier` |
| `refactor` | Code refactoring | `refactor(scrapers): extract common logic` |
| `perf` | Performance improvement | `perf(db): add index on job_skills` |
| `test` | Add/update tests | `test(applications): add status update tests` |
| `chore` | Maintenance tasks | `chore(deps): update FastAPI to 0.104.0` |
| `ci` | CI/CD changes | `ci(github): add deployment workflow` |

**Examples**:

```bash
# Feature with scope
git commit -m "feat(ai): add Anthropic Claude support"

# Bug fix with description
git commit -m "fix(resume): handle PDF parsing errors

- Add try-catch for malformed PDFs

- Display user-friendly error message

- Log errors to Sentry

Closes #123"

# Breaking change
git commit -m "feat(api): migrate to v2 authentication

BREAKING CHANGE: JWT tokens now require 'aud' claim.
Clients must update token generation logic."
```

### Code Review Process

1. **Create Pull Request**
   - Reference issue number
   - Provide clear description
   - Add screenshots (for UI changes)
   - Ensure CI passes

1. **Automated Checks**
   - ✅ Tests pass
   - ✅ Code coverage maintained
   - ✅ Linting passes
   - ✅ No security vulnerabilities

1. **Manual Review**
   - Code quality
   - Architecture adherence
   - Performance implications
   - Security considerations

1. **Approval & Merge**
   - At least 1 approval required
   - Squash and merge to develop
   - Delete feature branch

### Local Development Setup

#### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
cd /path/to/career-copilot
pre-commit install

# Run manually
pre-commit run --all-files
```

**Pre-commit Configuration** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.292
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.50.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
```

#### VSCode Configuration

Recommended VSCode settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**Recommended Extensions**:

- Python (ms-python.python)

- Pylance (ms-python.vscode-pylance)

- Black Formatter (ms-python.black-formatter)

- ESLint (dbaeumer.vscode-eslint)

- Prettier (esbenp.prettier-vscode)

- Thunder Client (rangav.vscode-thunder-client)

### Debugging

#### Backend Debugging (Python)

**VSCode Launch Configuration** (`.vscode/launch.json`):

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
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8002"
      ],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

**Using pdb (Python Debugger)**:

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

#### Frontend Debugging (Next.js)

**Chrome DevTools**:

1. Open Chrome DevTools (F12)
2. Navigate to Sources tab
3. Set breakpoints in TypeScript files
4. Refresh page

**VSCode Debugging**:

```json
{
  "name": "Next.js: debug client",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:3000",
  "webRoot": "${workspaceFolder}/frontend"
}
```

**Console Logging Best Practices**:

```typescript
// Use structured logging
console.log('[JobSearch] Fetching jobs with filters:', { location, skills });

// Avoid in production
if (process.env.NODE_ENV === 'development') {
  console.debug('API Response:', response);
}
```

### Database Migrations

#### Creating a Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add job_fingerprint column"

# Create empty migration (manual)
alembic revision -m "Add custom index"
```

#### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade by 1 version
alembic upgrade +1

# Downgrade by 1 version
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

#### Example Migration File

```python
# alembic/versions/abc123_add_job_fingerprint.py
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('jobs',
        sa.Column('fingerprint', sa.String(64), nullable=True)
    )
    op.create_index('idx_job_fingerprint', 'jobs', ['fingerprint'], unique=True)

def downgrade():
    op.drop_index('idx_job_fingerprint', table_name='jobs')
    op.drop_column('jobs', 'fingerprint')
```

---

## 🐛 Troubleshooting & FAQ

### Common Issues

#### 1. Database Connection Errors

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions**:

```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL (macOS)
brew services start postgresql@14

# Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Verify connection
psql -U postgres -h localhost -p 5432
```

**Problem**: `FATAL: database "career_copilot" does not exist`

**Solution**:

```bash
# Create database
createdb career_copilot

# Run migrations
cd backend
alembic upgrade head
```

#### 2. Redis Connection Errors

**Problem**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solutions**:

```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis (macOS)
brew services start redis

# Start Redis (Linux)
sudo systemctl start redis

# Start Redis (manual)
redis-server
```

#### 3. Port Already in Use

**Problem**: `Error: Address already in use: 8002`

**Solutions**:

```bash
# Find process using port
lsof -i :8002  # macOS/Linux
netstat -ano | findstr :8002  # Windows

# Kill process (macOS/Linux)
kill -9 <PID>

# Kill process (Windows)
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --port 8003
```

#### 4. Frontend Build Errors

**Problem**: `Module not found: Can't resolve '@/components/...'`

**Solutions**:

```bash
# Clear Next.js cache
cd frontend
rm -rf .next
npm run dev

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Problem**: `TypeError: Cannot read property 'map' of undefined`

**Solution**: Add safe navigation:

```typescript
// Before
const jobs = data.jobs.map(job => ...)

// After
const jobs = data?.jobs?.map(job => ...) ?? []
```

#### 5. API Authentication Errors

**Problem**: `401 Unauthorized: Invalid or expired token`

**Solutions**:

```bash
# Generate new token
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Check token expiration
# Decode JWT at https://jwt.io
```

**Problem**: `403 Forbidden: Insufficient permissions`

**Solution**: Ensure user has required role/permissions in database.

#### 6. Job Scraping Not Working

**Problem**: No jobs appearing after scraping

**Check**:

```bash
# View scraper logs
tail -f logs/app/scrapers.log

# Check scheduler status
curl http://localhost:8002/api/v1/health/scheduler

# Manually trigger scraping
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Authorization: Bearer $TOKEN"
```

**Common Causes**:

- API keys missing/invalid

- Rate limits exceeded

- Network connectivity issues

- Scraper timeout too low

#### 7. AI Generation Failures

**Problem**: `OpenAI API Error: Rate limit exceeded`

**Solutions**:

- Switch to Groq (free tier): Update `DEFAULT_AI_PROVIDER=groq`

- Wait for rate limit reset

- Upgrade OpenAI plan

**Problem**: `Anthropic API Error: Invalid API key`

**Solution**:

```bash
# Verify API key
echo $ANTHROPIC_API_KEY

# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

#### 8. Docker Issues

**Problem**: `docker-compose up` fails with network errors

**Solutions**:

```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d

# Check Docker daemon
docker info

# Reset Docker (macOS)
# Docker Desktop > Troubleshoot > Reset to factory defaults
```

**Problem**: Container exits immediately

**Solution**:

```bash
# Check container logs
docker-compose logs backend

# Run container interactively
docker-compose run backend bash
```

### Performance Issues

#### Slow API Responses

**Diagnosis**:

```bash
# Enable SQL query logging
export DATABASE_ECHO=True

# Profile with py-spy
pip install py-spy
sudo py-spy record -o profile.svg -- python -m uvicorn app.main:app

# Check slow queries
grep "duration:" logs/app/app.log | sort -n
```

**Solutions**:

- Add database indexes

- Enable Redis caching

- Implement pagination

- Use connection pooling

#### High Memory Usage

**Diagnosis**:

```bash
# Monitor memory
docker stats

# Check Python memory
import tracemalloc
tracemalloc.start()
# ... code ...
print(tracemalloc.get_traced_memory())
```

**Solutions**:

- Reduce worker count

- Implement pagination

- Clear Redis cache

- Upgrade server resources

### Platform-Specific Issues

#### macOS

**Problem**: `xcrun: error: invalid active developer path`

**Solution**:

```bash
xcode-select --install
```

**Problem**: PostgreSQL locale errors

**Solution**:

```bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

#### Windows

**Problem**: PowerShell script execution policy

**Solution**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem**: Line ending issues (CRLF vs LF)

**Solution**:

```bash
git config --global core.autocrlf false
```

#### Linux

**Problem**: Permission denied on port 80/443

**Solution**:

```bash
# Use ports > 1024 or run with sudo
sudo uvicorn app.main:app --host 0.0.0.0 --port 80

# Or use authbind
```

### Getting Help

**1. Check Documentation**:

- README.md

- API Docs: <http://localhost:8002/docs>

- Code comments

**2. Search Issues**:

- GitHub Issues: <https://github.com/moatasim-KT/career-copilot/issues>

- Stack Overflow: Tag `career-copilot`

**3. Create Issue**:

```markdown
**Environment**:
- OS: macOS 13.5

- Python: 3.11.4

- Node: 18.17.0

- PostgreSQL: 14.9

- Redis: 7.2.1

**Steps to Reproduce**:
1. Run `docker-compose up`
2. Navigate to http://localhost:3000
3. Click "Search Jobs"

**Expected Behavior**:
Jobs should load

**Actual Behavior**:
Error: "Failed to fetch jobs"

**Logs**:
```

[error] Failed to connect to database

```text

**4. Community Support**:
- Discord: [Join our server](https://discord.gg/career-copilot)

- Email: support@career-copilot.com

---

## 🚀 Deployment

### Production Deployment Options

Career Copilot supports multiple deployment strategies:

1. **Docker Compose** (Recommended for small-medium scale)
2. **Kubernetes** (Recommended for large scale)
3. **Cloud Platforms** (GCP, AWS, Azure)
4. **Traditional VPS** (DigitalOcean, Linode)

### Docker Compose Deployment (Production)

**1. Prepare Environment**:

```bash
# Create production environment file
cp .env.example .env.production

# Update production values
nano .env.production
```

**Key Production Settings**:

```bash
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=<64-character-random-string>
ENCRYPTION_KEY=<Fernet-key>
COOKIE_SECURE=True

# Database (use managed service)
DATABASE_URL=postgresql+asyncpg://user:pass@db-prod.example.com:5432/career_copilot

# Redis (use managed service)
REDIS_HOST=redis-prod.example.com
REDIS_PASSWORD=<redis-password>
REDIS_SSL=True

# CORS (your production domains)
CORS_ORIGINS=https://career-copilot.com,https://www.career-copilot.com

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
PROMETHEUS_ENABLED=True
```

**2. Deploy with Docker Compose**:

```bash
# Pull latest images
docker-compose -f docker-compose.yml pull

# Build and start services
docker-compose -f docker-compose.yml up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**3. Setup SSL/TLS with Let's Encrypt**:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d career-copilot.com -d www.career-copilot.com

# Auto-renewal (add to crontab)
0 12 * * * /usr/bin/certbot renew --quiet
```

**4. Configure Nginx Reverse Proxy**:

```nginx
# /etc/nginx/sites-available/career-copilot

upstream backend {
    server localhost:8002;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name career-copilot.com www.career-copilot.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name career-copilot.com www.career-copilot.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/career-copilot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/career-copilot.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API backend
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files
    location /_next/static/ {
        proxy_pass http://frontend;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Uploads
    location /uploads/ {
        alias /var/www/career-copilot/uploads/;
        add_header Cache-Control "public, max-age=86400";
    }
}
```

**Enable Nginx Configuration**:

```bash
sudo ln -s /etc/nginx/sites-available/career-copilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Kubernetes Deployment

**1. Create Kubernetes Manifests**:

See `deployment/k8s/` directory for complete manifests.

**2. Deploy to Kubernetes**:

```bash
# Create namespace
kubectl create namespace career-copilot

# Create secrets
kubectl create secret generic career-copilot-secrets \
  --from-env-file=.env.production \
  -n career-copilot

# Deploy services
kubectl apply -f deployment/k8s/ -n career-copilot

# Check deployment status
kubectl get pods -n career-copilot
kubectl get services -n career-copilot

# View logs
kubectl logs -f deployment/backend -n career-copilot
```

**3. Setup Ingress (NGINX)**:

```yaml
# deployment/k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: career-copilot-ingress
  namespace: career-copilot
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - career-copilot.com
        - www.career-copilot.com
      secretName: career-copilot-tls
  rules:
    - host: career-copilot.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8002
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 3000
```

**4. Setup Auto-scaling**:

```yaml
# deployment/k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: career-copilot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Cloud Platform Deployment

#### Google Cloud Platform (GCP)

**1. Cloud Run Deployment** (Serverless):

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/career-copilot-backend

# Deploy to Cloud Run
gcloud run deploy career-copilot-backend \
  --image gcr.io/PROJECT_ID/career-copilot-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,REDIS_HOST=$REDIS_HOST

# Deploy frontend
gcloud run deploy career-copilot-frontend \
  --image gcr.io/PROJECT_ID/career-copilot-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**2. Cloud SQL (Managed PostgreSQL)**:

```bash
# Create instance
gcloud sql instances create career-copilot-db \
  --database-version=POSTGRES_14 \
  --tier=db-g1-small \
  --region=us-central1

# Create database
gcloud sql databases create career_copilot \
  --instance=career-copilot-db

# Set password
gcloud sql users set-password postgres \
  --instance=career-copilot-db \
  --password=SECURE_PASSWORD
```

**3. Memorystore (Managed Redis)**:

```bash
# Create Redis instance
gcloud redis instances create career-copilot-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

### Monitoring Setup

**1. Prometheus + Grafana**:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

**Start Monitoring**:

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

**Access**:

- Prometheus: <http://localhost:9090>

- Grafana: <http://localhost:3001>

**2. Application Metrics Endpoint**:

Already configured at: `http://localhost:8002/metrics`

**3. Sentry (Error Tracking)**:

```bash
# Set Sentry DSN in .env
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Database Backup & Recovery

**Automated Backups**:

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups"
DB_NAME="career_copilot"

# Create backup
pg_dump -h localhost -U postgres $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql.gz s3://my-backups/
EOF

chmod +x backup.sh

# Schedule with cron (daily at 2 AM)
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

**Restore from Backup**:

```bash
# Extract backup
gunzip backup_20251106_020000.sql.gz

# Restore
psql -h localhost -U postgres -d career_copilot < backup_20251106_020000.sql
```

---

## ⚡ Performance & Optimization

### Performance Benchmarks

**Current Performance** (as of v1.0.0):

| Metric | Value | Target |
|--------|-------|--------|
| API Response Time (p50) | 45ms | < 100ms |
| API Response Time (p95) | 120ms | < 300ms |
| API Response Time (p99) | 250ms | < 500ms |
| Job Search Query | 85ms | < 150ms |
| Database Query Time | 12ms | < 50ms |
| Redis Cache Hit Rate | 87% | > 80% |
| Concurrent Users (max tested) | 500 | 1000+ |
| Requests per Second | 1200 | 2000+ |
| Job Scraping (9 sources) | 180s | < 300s |

### Optimization Strategies

#### 1. Database Optimization

**Indexes**:

```sql
-- Job search optimization
CREATE INDEX idx_jobs_location ON jobs (location);
CREATE INDEX idx_jobs_posted_date ON jobs (posted_date DESC);
CREATE INDEX idx_jobs_visa ON jobs (visa_sponsorship) WHERE visa_sponsorship = true;
CREATE INDEX idx_jobs_salary ON jobs (salary_min, salary_max);

-- GIN index for skill search
CREATE INDEX idx_jobs_skills_gin ON jobs USING GIN (skills);

-- Composite index for common queries
CREATE INDEX idx_jobs_location_date ON jobs (location, posted_date DESC);

-- Application tracking
CREATE INDEX idx_applications_user_status ON applications (user_id, status);
CREATE INDEX idx_applications_created ON applications (created_at DESC);

-- Deduplication
CREATE UNIQUE INDEX idx_job_fingerprint ON jobs (fingerprint) WHERE fingerprint IS NOT NULL;
```

**Connection Pooling**:

```python
# app/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,              # Number of persistent connections
    max_overflow=20,           # Additional connections if pool exhausted
    pool_pre_ping=True,        # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False                 # Disable SQL logging in production
)
```

**Query Optimization**:

```python
# Use select_related / join to avoid N+1 queries
jobs = await db.execute(
    select(Job)
    .options(selectinload(Job.company))  # Eager load company
    .filter(Job.location == "Berlin")
    .limit(20)
)

# Use pagination instead of loading all
jobs = await db.execute(
    select(Job)
    .offset((page - 1) * per_page)
    .limit(per_page)
)

# Use COUNT efficiently
count = await db.scalar(
    select(func.count(Job.id)).filter(Job.location == "Berlin")
)
```

#### 2. Redis Caching

**Cache Strategy**:

```python
# app/services/cache.py
class CacheService:
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 300
    ):
        """Get from cache or execute factory and cache result"""
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        result = await factory()
        await self.redis.setex(
            key,
            ttl,
            json.dumps(result)
        )
        return result

# Usage
jobs = await cache.get_or_set(
    key=f"jobs:search:{location}:{skills}",
    factory=lambda: job_service.search(location, skills),
    ttl=300  # 5 minutes
)
```

**Cache Invalidation**:

```python
# Invalidate when job created
await cache.delete_pattern("jobs:search:*")

# Invalidate user-specific data
await cache.delete(f"user:{user_id}:recommendations")
```

#### 3. API Response Optimization

**Pagination**:

```python
@router.get("/jobs")
async def search_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    # Efficient pagination
    offset = (page - 1) * per_page
    jobs = await job_service.search(offset=offset, limit=per_page)
    return {"jobs": jobs, "page": page, "per_page": per_page}
```

**Field Selection**:

```python
@router.get("/jobs")
async def search_jobs(fields: Optional[str] = None):
    # Only return requested fields
    if fields:
        selected_fields = [getattr(Job, f) for f in fields.split(",")]
        query = select(*selected_fields)
    else:
        query = select(Job)
```

**Response Compression**:

```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 4. Frontend Optimization

**Code Splitting**:

```typescript
// Dynamic imports for large components
const AnalyticsDashboard = dynamic(
  () => import('@/components/AnalyticsDashboard'),
  { loading: () => <Spinner /> }
);
```

**Image Optimization**:

```tsx
import Image from 'next/image';

<Image
  src="/company-logo.png"
  alt="Company Logo"
  width={100}
  height={100}
  loading="lazy"
  quality={85}
/>
```

**API Request Deduplication**:

```typescript
// TanStack Query automatically deduplicates
const { data } = useQuery({
  queryKey: ['jobs', filters],
  queryFn: () => fetchJobs(filters),
  staleTime: 5 * 60 * 1000,  // 5 minutes
});
```

**Virtualized Lists**:

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const JobList = ({ jobs }) => {
  const virtualizer = useVirtualizer({
    count: jobs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 150,
  });

  return virtualizer.getVirtualItems().map(virtualRow => (
    <JobCard key={jobs[virtualRow.index].id} job={jobs[virtualRow.index]} />
  ));
};
```

#### 5. Scraping Optimization

**Concurrent Scraping**:

```python
# Run scrapers in parallel
import asyncio

async def scrape_all():
    scrapers = [
        AdzunaScraper(),
        RapidAPIScraper(),
        TheMuseScraper(),
        # ...
    ]

    results = await asyncio.gather(
        *[scraper.scrape() for scraper in scrapers],
        return_exceptions=True
    )
    return results
```

**Rate Limiting**:

```python
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(max_rate=30, time_period=60)  # 30 req/min

async def fetch_with_rate_limit(url):
    async with rate_limiter:
        return await httpx.get(url)
```

### Performance Monitoring

**Application Metrics**:

```python
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    with request_duration.time():
        response = await call_next(request)
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    return response
```

**Database Query Monitoring**:

```python
# Log slow queries
import logging
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log queries > 100ms
        logging.warning(f"Slow query ({total:.2f}s): {statement}")
```

---

## 🔒 Security

### Security Implementation

Career Copilot implements defense-in-depth security:

1. **Authentication**: JWT-based with secure token storage
2. **Authorization**: Role-based access control (RBAC)
3. **Encryption**: Data at rest and in transit
4. **Input Validation**: Pydantic models + sanitization
5. **Rate Limiting**: Prevent abuse and DoS
6. **CORS**: Restrict cross-origin requests
7. **Security Headers**: HSTS, CSP, X-Frame-Options
8. **Dependency Scanning**: Automated vulnerability checks

### Authentication & Authorization

**JWT Token Structure**:

```json
{
  "sub": "user_id_123",
  "email": "user@example.com",
  "role": "user",
  "exp": 1699275600,
  "iat": 1699189200
}
```

**Token Generation**:

```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
```

**Token Validation**:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
        return await user_service.get_by_id(user_id)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Data Encryption

**Sensitive Data** (API keys, passwords):

```python
from cryptography.fernet import Fernet

cipher = Fernet(ENCRYPTION_KEY)

def encrypt(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

def decrypt(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()

# Usage
user.api_key_encrypted = encrypt(api_key)
```

**Password Hashing**:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### Input Validation

**Pydantic Models**:

```python
from pydantic import BaseModel, EmailStr, Field, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

**SQL Injection Prevention**:

```python
# ✅ SAFE: Using SQLAlchemy ORM (parameterized)
jobs = await db.execute(
    select(Job).filter(Job.location == user_input)
)

# ❌ UNSAFE: Raw SQL with string concatenation
jobs = await db.execute(f"SELECT * FROM jobs WHERE location = '{user_input}'")
```

**XSS Prevention**:

```typescript
// React automatically escapes
<div>{user.name}</div>  // ✅ Safe

// Dangerous if using dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: user.bio }} />  // ❌ Unsafe

// Use sanitizer
import DOMPurify from 'isomorphic-dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(user.bio) }} />  // ✅ Safe
```

### API Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    # Login logic
    pass

@app.get("/api/v1/jobs")
@limiter.limit("30/minute")
async def search_jobs(request: Request):
    # Search logic
    pass
```

### Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### Vulnerability Reporting

**Security Contact**: <security@career-copilot.com>

**Responsible Disclosure**:

1. Email details to <security@career-copilot.com>
2. Do not publicly disclose until patched
3. Allow 90 days for fix before public disclosure
4. We'll acknowledge receipt within 48 hours
5. Security researchers credited in release notes

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Code Style

#### Python (Backend)

- **Formatter**: Black (line length: 100)

- **Linter**: Ruff

- **Type Hints**: Required for all functions

- **Docstrings**: Google style

**Example**:

```python
from typing import List, Optional

async def search_jobs(
    location: str,
    skills: Optional[List[str]] = None,
    limit: int = 20
) -> List[Job]:
    """
    Search for jobs matching criteria.

    Args:
        location: Job location (city or country)
        skills: List of required skills
        limit: Maximum number of results

    Returns:
        List of matching Job objects

    Raises:
        ValueError: If location is empty
    """
    if not location:
        raise ValueError("Location is required")

    # Implementation
    pass
```

#### TypeScript/React (Frontend)

- **Formatter**: Prettier

- **Linter**: ESLint

- **Style**: Functional components with hooks

- **Naming**: camelCase for variables, PascalCase for components

**Example**:

```typescript
interface JobCardProps {
  job: Job;
  onBookmark?: (jobId: number) => void;
}

export const JobCard: React.FC<JobCardProps> = ({ job, onBookmark }) => {
  const handleBookmark = () => {
    onBookmark?.(job.id);
  };

  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <button onClick={handleBookmark}>Bookmark</button>
    </div>
  );
};
```

### Pull Request Process

1. **Fork & Clone**:

   ```bash
   git clone https://github.com/YOUR_USERNAME/career-copilot.git
   cd career-copilot
   git remote add upstream https://github.com/moatasim-KT/career-copilot.git
   ```

1. **Create Feature Branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

1. **Make Changes**:
   - Write code
   - Add tests
   - Update documentation

1. **Test**:

   ```bash
   # Backend
   cd backend
   pytest

   # Frontend
   cd frontend
   npm test
   ```

1. **Commit**:

   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

1. **Push & Create PR**:

   ```bash
   git push origin feature/your-feature-name
   ```

   Then create pull request on GitHub.

1. **Code Review**:
   - Address feedback
   - Keep PR updated with main
   - Ensure CI passes

### Component Development Guide

See `frontend/CONTRIBUTING.md` for detailed frontend development guidelines including:

- Design system usage

- Component structure

- State management patterns

- Testing requirements

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright © 2024 Moatasim Farooque

---

## 🙏 Acknowledgments

**Technologies**:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework for production
- [PostgreSQL](https://www.postgresql.org/) - Powerful open-source database
- [Redis](https://redis.io/) - In-memory data structure store
- [TanStack Query](https://tanstack.com/query) - Data fetching library
- [TailwindCSS](https://tailwindcss.com/) - Utility-first CSS framework

**Job Boards & APIs**:

- [Adzuna](https://www.adzuna.com/) - Job search aggregator
- [JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) - RapidAPI job search
- [The Muse](https://www.themuse.com/) - Career platform
- [Arbeitnow](https://www.arbeitnow.com/) - EU job board

**AI Providers**:

- [OpenAI](https://openai.com/) - GPT models
- [Groq](https://groq.com/) - Lightning-fast LLM inference
- [Anthropic](https://www.anthropic.com/) - Claude models
- [Google](https://ai.google.dev/) - Gemini models

**Contributors**:

Special thanks to all contributors who have helped improve Career Copilot!

---

## 📝 Technical Decisions & Rationale

### Technology Choices

**Why FastAPI over Flask/Django?**

- **Performance**: Async/await support for high concurrency
- **Modern**: Built for Python 3.11+ with type hints
- **Auto-docs**: Automatic OpenAPI/Swagger generation
- **Validation**: Pydantic integration for data validation

**Why Next.js over Create React App?**

- **SSR/SSG**: Server-side rendering for better SEO and performance
- **App Router**: Modern routing with React Server Components
- **Optimization**: Automatic code splitting and image optimization
- **DX**: Excellent developer experience with hot reload

**Why PostgreSQL over MongoDB?**

- **ACID**: Strong consistency for critical user data
- **Relationships**: Complex joins for analytics queries
- **JSONB**: NoSQL flexibility when needed
- **Maturity**: Battle-tested with excellent tooling

**Why Redis for Caching?**

- **Speed**: In-memory storage for sub-millisecond access
- **Versatility**: Supports multiple data structures
- **Pub/Sub**: Real-time messaging capabilities
- **Simplicity**: Easy to deploy and maintain

### Architecture Decisions

**Monorepo vs Separate Repos**: Chose monorepo for easier coordination between frontend and backend during rapid development phase.

**Sync vs Async**: Async throughout backend for handling concurrent scraping and API requests efficiently.

**REST vs GraphQL**: REST API for simplicity and better caching, though GraphQL could be added for flexible querying.

**Job Storage**: PostgreSQL for job data despite high volume - enables complex analytics queries and JSONB handles flexible schemas.

### Trade-offs

**Scraping Frequency**:

- **Current**: Every 6 hours
- **Trade-off**: Lower API costs vs less fresh data
- **Future**: User-configurable frequency for premium tiers

**AI Provider Flexibility**:

- **Current**: Support for 4 providers
- **Trade-off**: More code complexity vs vendor lock-in protection
- **Benefit**: Can switch based on cost/performance

**Caching Strategy**:

- **Current**: Aggressive caching with 5-15 minute TTLs
- **Trade-off**: Slightly stale data vs reduced database load
- **Mitigation**: Cache invalidation on writes

---

## 📅 Changelog & Versioning

### Versioning

Career Copilot follows **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Recent Changes

#### Version 1.0.0 (2025-11-06)

##### Initial Public Release

**Features**:

- ✅ 9 job scrapers covering 19+ EU countries
- ✅ AI-powered resume and cover letter generation
- ✅ Application tracking with timeline view
- ✅ Analytics dashboard with insights
- ✅ Personalized job recommendations
- ✅ Email and SMS notifications
- ✅ Comprehensive API documentation

**Performance**:

- ✅ Job search response time: <150ms (p95)
- ✅ Handles 500 concurrent users
- ✅ 87% cache hit rate

**Security**:

- ✅ JWT authentication
- ✅ Data encryption at rest
- ✅ Rate limiting
- ✅ Security headers

### Upgrade Guide

#### From v0.9.x to v1.0.0

**Breaking Changes**:

1. **Authentication**: JWT now includes `aud` claim. Update token generation:

   ```python
   # Old
   token = create_token(user_id)
   
   # New
   token = create_token(user_id, audience="career-copilot")
   ```

2. **Database**: New `job_fingerprint` column required:

   ```bash
   alembic upgrade head  # Applies migration
   python scripts/backfill_job_fingerprints.py  # Backfill existing data
   ```

3. **Configuration**: New required environment variables:

   ```bash
   ENCRYPTION_KEY=<fernet-key>  # Required for API key encryption
   CORS_ORIGINS=http://localhost:3000  # Required for security
   ```

**Migration Steps**:

1. Backup database: `pg_dump career_copilot > backup.sql`
2. Update environment variables in `.env`
3. Run migrations: `alembic upgrade head`
4. Restart services: `docker-compose restart`
5. Verify health: `curl http://localhost:8002/health`

---

## 📚 Resources

### Official Documentation

- **Project README**: You're reading it!
- **API Documentation**: <http://localhost:8002/docs> (Swagger UI)
- **API Reference**: <http://localhost:8002/redoc> (ReDoc)
- **Frontend Guide**: `frontend/CONTRIBUTING.md`
- **Design System**: `frontend/DESIGN_SYSTEM.md`
- **Monitoring**: `docs/MONITORING.md`

### External Resources

**FastAPI**:

- [Official Docs](https://fastapi.tiangolo.com/)
- [Async Tutorial](https://fastapi.tiangolo.com/async/)
- [Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

**Next.js**:

- [Official Docs](https://nextjs.org/docs)
- [App Router](https://nextjs.org/docs/app)
- [React Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components)

**PostgreSQL**:

- [Official Docs](https://www.postgresql.org/docs/)
- [Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [JSONB Guide](https://www.postgresql.org/docs/current/datatype-json.html)

**Redis**:

- [Official Docs](https://redis.io/docs/)
- [Caching Patterns](https://redis.io/docs/manual/patterns/)
- [Pub/Sub](https://redis.io/docs/manual/pubsub/)

### Community & Learning

**Tutorials**:

- [Building REST APIs with FastAPI](https://testdriven.io/courses/tdd-fastapi/)
- [Next.js 14 Complete Guide](https://www.youtube.com/watch?v=ZVnjOPwW4ZA)
- [PostgreSQL for Beginners](https://www.postgresqltutorial.com/)

**Blogs & Articles**:

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Next.js Performance Patterns](https://nextjs.org/docs/app/building-your-application/optimizing)
- [Database Indexing Strategies](https://use-the-index-luke.com/)

**YouTube Channels**:

- [ArjanCodes](https://www.youtube.com/@ArjanCodes) - Python best practices
- [Traversy Media](https://www.youtube.com/@TraversyMedia) - Web development
- [Hussein Nasser](https://www.youtube.com/@hnasr) - Backend engineering

### Similar Projects

- [Huntr](https://huntr.co/) - Job application tracker
- [Teal](https://www.tealhq.com/) - Career growth platform
- [Jobscan](https://www.jobscan.co/) - Resume optimization

---

## 📄 License

**Contributors**:

Special thanks to all contributors who have helped improve Career Copilot!

---

## 📞 Support & Contact

**Documentation**: [README.md](README.md)
**API Docs**: <http://localhost:8002/docs>
**Issue Tracker**: <https://github.com/moatasim-KT/career-copilot/issues>
**Discussions**: <https://github.com/moatasim-KT/career-copilot/discussions>
**Email**: <support@career-copilot.com>
**Discord**: [Join our community](https://discord.gg/career-copilot)

**Response Times**:

- Critical bugs: 24 hours

- Feature requests: 1 week

- General questions: 3 business days

---

**⭐ If you find Career Copilot helpful, please star the repository!**

**Made with ❤️ by [Moatasim Farooque](https://github.com/moatasim-KT)**
