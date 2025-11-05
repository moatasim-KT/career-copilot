# 🚀 Career Copilot

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**An AI-powered career management platform specializing in EU job discovery with visa sponsorship support for AI/Data Science professionals.**

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture & Design](#-architecture--design)
3. [Key Components](#-key-components)
4. [Prerequisites](#-prerequisites)
5. [Installation](#-installation)
6. [External APIs](#-external-apis)
7. [Configuration](#-configuration)
8. [Usage](#-usage)
9. [API Documentation](#-api-documentation)
10. [Development](#-development)
11. [Troubleshooting](#-troubleshooting)
12. [Production Deployment](#-production-deployment)
13. [Resources](#-resources)

---

## 🎯 Project Overview

### What is Career Copilot?

Career Copilot is a comprehensive career management system that helps AI/Data Science professionals discover jobs in the EU with visa sponsorship, track applications, generate AI-powered resumes and cover letters, and gain insights through advanced analytics.

### Key Features

- **🔍 Intelligent Job Discovery**: 9 specialized scrapers collecting jobs every 6 hours
- **🌍 EU-Focused**: 70-80% of jobs from 27 EU countries with visa sponsorship
- **🤖 AI-Powered Content**: Generate tailored resumes and cover letters using OpenAI, Groq, Anthropic, or Google Gemini
- **📊 Advanced Analytics**: Track applications, analyze trends, and get personalized insights
- **🔔 Smart Notifications**: Daily briefings and application reminders via email/SMS
- **🔐 Secure Authentication**: JWT-based auth with OAuth 2.0 (Google, LinkedIn)
- **⚡ High Performance**: Async Python, Redis caching, PostgreSQL database
- **📱 Modern UI**: Next.js 14 with React 18, TailwindCSS, and real-time updates

### Current Status

✅ **Backend**: Running on `http://localhost:8002`  
✅ **Database**: PostgreSQL connected  
✅ **Cache**: Redis running  
✅ **Scheduler**: APScheduler active (every 6 hours: 00:00, 06:00, 12:00, 18:00 UTC)  
⚠️ **Celery**: Not running (optional for distributed tasks)  
❌ **Frontend**: Not running (start with `npm run dev` in `frontend/`)

### Tech Stack

**Backend:**
- FastAPI 0.109+ (Python 3.11+)
- SQLAlchemy 2.0+ with AsyncPG
- PostgreSQL 14+
- Redis 7+ (caching)
- APScheduler (job scheduling)

**Frontend:**
- Next.js 14.0
- React 18.2
- TypeScript
- TailwindCSS
- Recharts (analytics)

**AI Services:**
- OpenAI GPT-4
- Groq (Llama 3)
- Anthropic Claude
- Google Gemini

**Job Scraping:**
- 9 scrapers: Adzuna, RapidAPI JSearch, The Muse, Indeed, Arbeitnow, Berlin Startup Jobs, Relocate.me, EURES, Firecrawl
- Firecrawl v2 API (AI-powered extraction from 10 EU companies)
- 3-layer deduplication system

---

## 🏗️ Architecture & Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Dashboard │  │Analytics │  │ AI Tools │  │  Jobs    │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │ REST API (HTTPS)
┌─────────────────────▼─────────────────────────────────────────┐
│                    Backend (FastAPI)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   Auth   │  │   Jobs   │  │   AI     │  │Analytics │      │
│  │  Service │  │  Service │  │  Service │  │  Service │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │              │
│  ┌────▼─────────────▼─────────────▼─────────────▼────┐        │
│  │           Database Layer (SQLAlchemy 2.0)         │        │
│  └────┬──────────────────────────────────────────────┘        │
└───────┼────────────────────────────────────────────────────────┘
        │
┌───────▼──────────┐  ┌──────────────┐  ┌───────────────────┐
│   PostgreSQL     │  │    Redis     │  │   APScheduler     │
│   (Database)     │  │   (Cache)    │  │  (Job Scheduler)  │
└──────────────────┘  └──────────────┘  └───────────────────┘
        │                                        │
┌───────▼────────────────────────────────────────▼──────────────┐
│                  External Services                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Adzuna  │  │ RapidAPI │  │Firecrawl │  │  OpenAI  │     │
│  │   API    │  │  JSearch │  │   API    │  │   API    │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└────────────────────────────────────────────────────────────────┘
```

### Job Scraping Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  APScheduler (Every 6 Hours)                 │
│                  Trigger: 00:00, 06:00, 12:00, 18:00 UTC     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Scraper Manager                           │
│  Coordinates 9 scrapers in parallel                         │
└──────┬───────┬────────┬────────┬────────┬───────┬──────────┘
       │       │        │        │        │       │
┌──────▼─┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼──┐ ┌─▼──────┐
│Adzuna │ │RapidAPI│TheMuse││Indeed│ │Arbeit│ │Firecrawl│ ...
│(13 EU)│ │(19 EU) │(Global)││(API) │ │now  │ │(10 Cos)│
└───┬───┘ └───┬────┘ └──┬───┘ └──┬───┘ └──┬──┘ └───┬────┘
    │         │          │        │        │        │
    └─────────┴──────────┴────────┴────────┴────────┘
                         │
            ┌────────────▼────────────┐
            │  3-Layer Deduplication  │
            │  1. Normalization       │
            │  2. DB Filtering (30d)  │
            │  3. Fuzzy Match (85%)   │
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │  Job Enrichment         │
            │  - Extract skills       │
            │  - Detect visa support  │
            │  - Parse salary         │
            │  - Geocode location     │
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │   PostgreSQL Storage    │
            │   ~200 jobs/run         │
            │   70-80% EU coverage    │
            │   50-60% visa support   │
            └─────────────────────────┘
```

---

## 🧩 Key Components

### 1. Job Discovery & Tracking

**Purpose**: Find and track relevant job opportunities

**Features**:
- 9 specialized scrapers (4 EU-focused + 1 AI-powered)
- Automatic scraping every 6 hours
- Advanced filtering (location, salary, skills, visa)
- Bookmark favorite jobs
- Smart recommendations

**Key Endpoints**:
- `GET /api/v1/jobs` - Search jobs with filters
- `GET /api/v1/jobs/{id}` - Get job details
- `POST /api/v1/jobs/{id}/bookmark` - Bookmark job
- `GET /api/v1/jobs/recommendations` - Get personalized jobs

### 2. Application Tracking

**Purpose**: Manage job applications through the entire lifecycle

**Features**:
- Track application status (applied, interview, offer, rejected)
- Upload resumes and cover letters
- Add notes and reminders
- Application timeline view

**Key Endpoints**:
- `POST /api/v1/applications` - Create application
- `GET /api/v1/applications` - List applications
- `PUT /api/v1/applications/{id}` - Update application

### 3. Analytics & Insights

**Purpose**: Gain insights from application data

**Features**:
- Application success rate
- Response time analysis
- Top companies and skills
- Salary trends
- Location distribution

**Key Endpoints**:
- `GET /api/v1/analytics/summary` - Overall stats
- `GET /api/v1/analytics/trends` - Time-series data
- `GET /api/v1/analytics/skills` - Skills demand

### 4. AI Resume & Cover Letter Generation

**Purpose**: Create tailored application documents using AI

**Features**:
- Multiple AI providers (OpenAI, Groq, Anthropic, Gemini)
- Job-specific customization
- PDF export
- Version history
- Template library

**Key Endpoints**:
- `POST /api/v1/ai/resume/generate` - Generate resume
- `POST /api/v1/ai/cover-letter/generate` - Generate cover letter
- `POST /api/v1/ai/resumes/{id}/export` - Export as PDF

---

## 📦 Prerequisites

### Required Software

- **Python**: 3.11 or 3.12
- **Node.js**: 18.x or 20.x
- **PostgreSQL**: 14+ (database)
- **Redis**: 7+ (caching)
- **Git**: Latest version

### System Requirements

- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk**: 2GB free space
- **OS**: macOS, Linux, or Windows (WSL2)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/career-copilot.git
cd career-copilot
```

### 2. Backend Setup

#### 2.1 Create Python Virtual Environment

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2.2 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -e .  # Installs from pyproject.toml
```

#### 2.3 Setup PostgreSQL Database

**Option A: Use existing PostgreSQL installation**

```bash
# Create database
createdb career_copilot

# Or using psql
psql -U postgres
CREATE DATABASE career_copilot;
\q
```

**Option B: Use Docker**

```bash
docker run -d \
  --name career-copilot-db \
  -e POSTGRES_DB=career_copilot \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:14
```

#### 2.4 Setup Redis

**Option A: Use existing Redis installation**

```bash
redis-server  # Start Redis on default port 6379
```

**Option B: Use Docker**

```bash
docker run -d \
  --name career-copilot-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 2.5 Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Minimum required variables**:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/career_copilot

# Security
JWT_SECRET_KEY=<generate-random-secret>
ENCRYPTION_KEY=<generate-random-secret>

# AI Services (at least one)
OPENAI_API_KEY=sk-...
# OR
GROQ_API_KEY=gsk_...

# Job Scraping (at least Adzuna)
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key
```

#### 2.6 Run Database Migrations

```bash
alembic upgrade head
```

#### 2.7 Create Test User

```bash
python create_test_user.py
# Creates user: test@example.com / password123
```

#### 2.8 Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

**Verify backend**: Visit `http://localhost:8002/docs` for Swagger UI

### 3. Frontend Setup

#### 3.1 Install Node Dependencies

```bash
cd ../frontend
npm install
```

#### 3.2 Configure Environment

```bash
# Copy example file
cp .env.local.example .env.local

# Edit .env.local
nano .env.local
```

**Required variables**:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_API_VERSION=v1
```

#### 3.3 Start Frontend Server

```bash
npm run dev
```

**Verify frontend**: Visit `http://localhost:3000`

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8002/health

# Test authentication
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

---

## 🔑 External APIs

### Job Scraping APIs

#### 1. Adzuna (Required)

**Coverage**: 13 EU countries  
**Cost**: Free tier available  
**Sign up**: https://developer.adzuna.com/signup

```bash
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

#### 2. RapidAPI JSearch (Recommended)

**Coverage**: 19 EU countries  
**Cost**: Free tier (100 requests/month)  
**Sign up**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

```bash
RAPIDAPI_KEY=your_rapidapi_key
```

#### 3. Firecrawl (AI-Powered) (Recommended)

**Coverage**: 10 EU companies with international hiring  
**Cost**: Free tier available  
**Sign up**: https://www.firecrawl.dev/

```bash
FIRECRAWL_API_KEY=fc-...
```

**Targeted companies**: Spotify, Adyen, Booking.com, Klarna, DeepMind, Revolut, Monzo, Bolt, N26, Zalando

### AI Services (Choose at least one)

#### 1. OpenAI (Recommended)

**Models**: GPT-4, GPT-3.5-turbo  
**Cost**: Pay-per-use  
**Sign up**: https://platform.openai.com/signup

```bash
OPENAI_API_KEY=sk-proj-...
```

#### 2. Groq (Fast & Free)

**Models**: Llama 3, Mixtral  
**Cost**: Free tier (high limits)  
**Sign up**: https://console.groq.com/

```bash
GROQ_API_KEY=gsk_...
```

---

## ⚙️ Configuration

### Environment Variables

#### Core Settings

```bash
# Application
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8002
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/career_copilot

# Security
JWT_SECRET_KEY=<random-secret-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENCRYPTION_KEY=<random-encryption-key>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
CORS_ORIGINS=http://localhost:3000
```

#### Job Scraping

```bash
# Adzuna (13 EU countries)
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key

# RapidAPI JSearch (19 EU countries)
RAPIDAPI_KEY=your_key

# Firecrawl (AI-powered, 10 EU companies)
FIRECRAWL_API_KEY=fc-...

# Scraper Flags
SCRAPING_ENABLE_ADZUNA=True
SCRAPING_ENABLE_RAPIDAPI=True
SCRAPING_ENABLE_THEMUSE=True
SCRAPING_ENABLE_ARBEITNOW=True
SCRAPING_ENABLE_BERLINSTARTUPJOBS=True
SCRAPING_ENABLE_RELOCATEME=True
SCRAPING_ENABLE_EURES=True
SCRAPING_ENABLE_FIRECRAWL=True
```

#### AI Services

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Groq
GROQ_API_KEY=gsk_...

# Gemini (Optional)
GEMINI_API_KEY=AI...

# Anthropic (Optional)
ANTHROPIC_API_KEY=sk-ant-...
```

### Scheduler Configuration

**File**: `backend/app/tasks/scheduled_tasks.py`

```python
# Job scraping (every 6 hours)
@scheduler.scheduled_job(
    trigger=CronTrigger(hour="*/6", minute=0, timezone=utc),
    id="ingest_jobs"
)
```

**To modify schedule**: Edit `hour="*/6"` to desired interval

---

## 📖 Usage

### Starting the Application

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Redis (if not running as service)
redis-server
```

### User Workflows

#### 1. Register and Login

**Via Frontend**:
1. Visit `http://localhost:3000`
2. Click "Register" and create account
3. Login with email/password

**Via API**:
```bash
# Register
curl -X POST http://localhost:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

#### 2. Search for Jobs

**Via API**:
```bash
# Search jobs in Germany with visa support
curl "http://localhost:8002/api/v1/jobs?location=Germany&visa_support=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by skills
curl "http://localhost:8002/api/v1/jobs?skills=Python,Machine%20Learning" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. Generate AI Resume

**Via API**:
```bash
curl -X POST http://localhost:8002/api/v1/ai/resume/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 123,
    "provider": "groq",
    "model": "llama-3.1-70b-versatile",
    "base_resume": "My name is John...",
    "target_role": "Senior Data Scientist"
  }'
```

### Manual Job Scraping

```bash
# Via API
curl -X POST http://localhost:8002/api/v1/jobs/scrape \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test scrapers
cd backend
python test_eu_scrapers.py
python test_firecrawl_simple.py
```

### Monitoring Logs

```bash
cd backend

# Realtime logs
tail -f logs/app.log

# Filter for errors
tail -f logs/app.log | grep ERROR

# View scraping activity
tail -f logs/app.log | grep -i "scraping\|job"
```

---

## 📚 API Documentation

### Interactive API Docs

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

### Authentication

All protected endpoints require JWT token:

```bash
Authorization: Bearer <your_token>
```

### Core Endpoints

#### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register` | Create new user | No |
| POST | `/login` | Login | No |
| GET | `/me` | Get current user | Yes |
| PUT | `/me` | Update profile | Yes |

#### Jobs (`/api/v1/jobs`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | Search jobs | Yes |
| GET | `/{id}` | Get job details | Yes |
| POST | `/{id}/bookmark` | Bookmark job | Yes |
| GET | `/recommendations` | Get recommendations | Yes |
| POST | `/scrape` | Trigger scraping | Yes |

#### Applications (`/api/v1/applications`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/` | Create application | Yes |
| GET | `/` | List applications | Yes |
| PUT | `/{id}` | Update application | Yes |
| DELETE | `/{id}` | Delete application | Yes |

#### AI Tools (`/api/v1/ai`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/resume/generate` | Generate resume | Yes |
| POST | `/cover-letter/generate` | Generate cover letter | Yes |
| GET | `/resumes` | List resumes | Yes |
| POST | `/resumes/{id}/export` | Export as PDF | Yes |

#### Analytics (`/api/v1/analytics`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/summary` | Overall statistics | Yes |
| GET | `/trends` | Time-series data | Yes |
| GET | `/skills` | Skills demand | Yes |
| GET | `/salary` | Salary trends | Yes |

---

## 🛠️ Development

### Project Structure

```
career-copilot/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API endpoints
│   │   ├── core/             # Config, database, security
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   │   ├── scraping/     # 9 job scrapers
│   │   │   ├── ai/           # AI services
│   │   │   └── analytics/    # Analytics
│   │   ├── tasks/            # Scheduled tasks
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   └── tests/                # Unit tests
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts
│   │   └── lib/              # Utilities
│   └── public/               # Static assets
└── README.md
```

### Code Style

**Python**: Ruff + Black  
**TypeScript**: ESLint + Prettier

```bash
# Format Python
cd backend
ruff format .

# Lint Python
ruff check . --fix

# Lint TypeScript
cd frontend
npm run lint
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error**: `could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL (macOS)
brew services start postgresql@14

# Verify DATABASE_URL in .env
```

#### 2. Redis Connection Error

**Error**: `Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Start Redis (macOS)
brew services start redis
```

#### 3. Frontend API Calls Fail (401)

**Solution**:
- Re-login to get fresh token
- Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`

#### 4. Job Scraping Returns No Results

**Solution**:
```bash
# Check if scrapers are enabled
grep "SCRAPING_ENABLE" backend/.env

# Verify API keys
grep "_API_KEY" backend/.env

# Test individual scraper
cd backend
python test_eu_scrapers.py
```

---

## 🚢 Production Deployment

### Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Use HTTPS
- [ ] Set secure `CORS_ORIGINS`
- [ ] Enable rate limiting
- [ ] Configure backups
- [ ] Set up monitoring

### Docker Deployment

```bash
# Build images
docker build -t career-copilot-backend:latest -f deployment/docker/Dockerfile.backend .
docker build -t career-copilot-frontend:latest -f deployment/docker/Dockerfile.frontend .

# Run with Docker Compose
docker-compose -f deployment/docker/docker-compose.yml up -d
```

---

## 🏭 Production Services

Career Copilot includes **3,240 lines of production-grade services** with enterprise features including error handling, logging, monitoring, caching, rate limiting, retry logic, and analytics tracking.

### Notification Manager (595 lines)

**Location**: `backend/app/services/notification_manager.py`

Multi-channel notification delivery system with intelligent routing and delivery tracking.

**Features:**
- **Multi-Channel Delivery**: Email, in-app, push notifications, SMS
- **Retry Logic**: Exponential backoff (5s → 15s → 60s)
- **Rate Limiting**: Sliding window (10 requests/60s per user)
- **Queue Management**: Batch processing for performance
- **User Preferences**: Enforces user notification preferences
- **Delivery Analytics**: Success rates, channel breakdown, queue status

**API Usage:**
```python
from app.services.notification_manager import NotificationManager

# Initialize
manager = NotificationManager(db=session)

# Send notification with retry
result = await manager.send_with_retry(
    user_id=1,
    notification_type="job_match",
    channel="email",
    subject="New Job Match!",
    content="We found a perfect match for your profile..."
)

# Queue for batch processing
manager.queue_notification(
    user_id=1,
    notification_type="deadline_reminder",
    data={"deadline": "2025-11-10"}
)

# Get delivery statistics
stats = manager.get_delivery_stats()
# Returns: {
#   "total_sent": 150,
#   "successful": 145,
#   "failed": 5,
#   "by_channel": {"email": 100, "in_app": 50}
# }

# Health check
health = await manager.health_check()
```

**Configuration:**
- `SMTP_ENABLED`: Enable email notifications
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`: SMTP settings
- `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`: Push notifications
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`: SMS notifications

### Adaptive Recommendation Engine (593 lines)

**Location**: `backend/app/services/adaptive_recommendation_engine.py`

Advanced job recommendation system with A/B testing and explainable AI.

**Features:**
- **Multi-Factor Scoring**: 7 weighted factors (skill 40%, location 20%, experience 15%, etc.)
- **A/B Testing**: Framework for algorithm optimization
- **Caching**: 15-minute TTL for performance
- **Explainable AI**: Detailed match explanations with skill gap analysis
- **Diversity Boosting**: Prevents same-company domination (max 3 per company)
- **Configurable Weights**: Dynamic weight adjustment based on user feedback

**Scoring Factors:**
- Skill matching (40%)
- Location matching (20%)
- Experience matching (15%)
- Salary matching (10%)
- Company culture (5%)
- Growth potential (5%)
- Recency (5%)

**API Usage:**
```python
from app.services.adaptive_recommendation_engine import AdaptiveRecommendationEngine

# Initialize
engine = AdaptiveRecommendationEngine(db=session)

# Get personalized recommendations
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
#       "matching_skills": ["Python", "Machine Learning"],
#       "missing_skills": ["Kubernetes"],
#       "location_match": "Remote OK",
#       "score_breakdown": {...}
#     }
#   },
#   ...
# ]

# Start A/B test
engine.start_ab_test(
    test_name="skill_weight_optimization",
    variant_a={"skill_match": 50, "location_match": 15},
    variant_b={"skill_match": 30, "location_match": 30},
    traffic_split=0.5
)

# Get test results
results = engine.get_ab_test_results(test_name="skill_weight_optimization")
```

### Analytics Suite (1,588 lines total)

Comprehensive analytics system for tracking user behavior, application funnels, and market trends.

#### Analytics Collection Service (319 lines)

**Location**: `backend/app/services/analytics_collection_service.py`

Event tracking with fault tolerance and performance optimization.

**Features:**
- **Event Queue**: 10,000 event capacity with batch processing
- **Circuit Breaker**: 5-failure threshold for fault tolerance
- **Rate Limiting**: 100 events/60s per user
- **Batch Processing**: 100 events per batch, 30s flush interval
- **Data Sanitization**: Removes sensitive data (passwords, tokens, etc.)

**API Usage:**
```python
from app.services.analytics_collection_service import AnalyticsCollectionService

service = AnalyticsCollectionService(db=session)

# Track single event
success = service.collect_event(
    user_id=1,
    event_type="job_view",
    event_data={"job_id": 123, "source": "search"},
    session_id="abc-123"
)

# Track batch
events = [
    {"user_id": 1, "event_type": "page_view", "event_data": {"path": "/jobs"}},
    {"user_id": 1, "event_type": "job_save", "event_data": {"job_id": 456}}
]
service.collect_batch(events)

# Get statistics
stats = service.get_stats()
# Returns: {
#   "queue_size": 50,
#   "queue_capacity": 10000,
#   "circuit_breaker": {"open": False, "failures": 0}
# }
```

#### Analytics Processing Service (316 lines)

**Location**: `backend/app/services/analytics_processing_service.py`

User behavior analysis, funnel tracking, and segmentation.

**Features:**
- **User Analytics**: Jobs viewed, applications, interviews, conversion rates
- **Funnel Analysis**: 4-stage funnel (viewed → applied → interviews → offers)
- **Engagement Scoring**: 0-100 scale based on activity
- **User Segmentation**: Auto-categorization (highly_active, moderately_active, low_activity, inactive)

**API Usage:**
```python
from app.services.analytics_processing_service import AnalyticsProcessingService

service = AnalyticsProcessingService(db=session)

# Get user analytics
analytics = service.get_user_analytics(user_id=1)
# Returns: {
#   "jobs_viewed": 150,
#   "applications_submitted": 25,
#   "interviews_scheduled": 5,
#   "offers_received": 1,
#   "conversion_rate": 4.0
# }

# Get conversion funnel
funnel = service.process_user_funnel(user_id=1)
# Returns: {
#   "viewed": {"count": 150, "conversion": 100.0},
#   "applied": {"count": 25, "conversion": 16.7},
#   "interviewed": {"count": 5, "conversion": 3.3},
#   "offered": {"count": 1, "conversion": 0.7}
# }

# Calculate engagement score
score = service.calculate_engagement_score(user_id=1)
# Returns: 75.5 (0-100 scale)
```

#### Analytics Query Service (252 lines)

**Location**: `backend/app/services/analytics_query_service.py`

Flexible metric retrieval with time-series support and caching.

**API Usage:**
```python
from app.services.analytics_query_service import AnalyticsQueryService

service = AnalyticsQueryService(db=session)

# Get metrics
metrics = service.get_metrics(
    user_id=1,
    metric_types=["jobs_saved", "applications_submitted"],
    timeframe="week"
)

# Get time-series data
time_series = service.get_time_series(
    user_id=1,
    metric_type="applications_submitted",
    granularity="day"
)
# Returns: [
#   {"date": "2025-11-01", "count": 3},
#   {"date": "2025-11-02", "count": 5},
#   ...
# ]
```

#### Analytics Reporting Service (299 lines)

**Location**: `backend/app/services/analytics_reporting_service.py`

Market trends, user insights, and comprehensive reporting.

**API Usage:**
```python
from app.services.analytics_reporting_service import AnalyticsReportingService

service = AnalyticsReportingService(db=session)

# Analyze market trends
trends = service.analyze_market_trends(user_id=1, days=30)
# Returns: {
#   "market_overview": {"total_jobs_posted": 500},
#   "top_companies": [{"company": "Google", "job_count": 50}],
#   "skill_demand": {"top_skills": [{"skill": "Python", "demand": 250}]}
# }

# Generate user insights
insights = service.generate_user_insights(user_id=1, days=30)
# Returns: {
#   "metrics": {"applications": 25, "interviews": 5},
#   "insights": [
#     {"type": "success", "message": "Great interview rate!"},
#     {"type": "action", "message": "Consider applying to 5-10 jobs/week"}
#   ]
# }
```

#### Analytics Service Facade (402 lines)

**Location**: `backend/app/services/analytics_service_facade.py`

Unified interface over all analytics services for simplified usage.

**API Usage:**
```python
from app.services.analytics_service_facade import AnalyticsServiceFacade

facade = AnalyticsServiceFacade(db=session)

# Track events (simplified)
await facade.track_page_view(user_id=1, path="/dashboard")
await facade.track_job_search(user_id=1, query="Python Developer", filters={"location": "Berlin"})
await facade.track_job_view(user_id=1, job_id=123, source="search")
await facade.track_application_submitted(user_id=1, job_id=123, application_id=456)

# Get complete dashboard data
dashboard = facade.get_dashboard_data(user_id=1)
# Returns: {
#   "analytics": {...},
#   "engagement_score": 75.5,
#   "funnel": {...},
#   "metrics": {...},
#   "insights": [...]
# }

# Health check all services
health = await facade.health_check()
```

### LinkedIn Scraper (464 lines)

**Location**: `backend/app/services/linkedin_scraper.py`

Production-grade LinkedIn job scraper with anti-detection and rate limiting.

**Features:**
- **Session Management**: Cookie persistence across requests
- **Rate Limiting**: Configurable requests per window with automatic backoff
- **Anti-Detection**: User agent rotation, random delays (2-5s)
- **Proxy Support**: IP rotation for distributed scraping
- **Error Recovery**: Exponential backoff retry logic
- **Job Extraction**: Comprehensive job data parsing

**API Usage:**
```python
from app.services.linkedin_scraper import LinkedInScraper

# Initialize with configuration
scraper = LinkedInScraper(
    cookies_file="cookies.json",
    proxy="http://proxy:8080",
    rate_limit_requests=10,
    rate_limit_window=60,
    min_delay=2.0,
    max_delay=5.0
)

# Search jobs
jobs = await scraper.search_jobs(
    keywords="Python Developer",
    location="Berlin, Germany",
    experience_level="mid-senior",
    job_type="full-time",
    max_pages=5
)
# Returns: [
#   {
#     "job_id": "123456",
#     "title": "Senior Python Developer",
#     "company": "Google",
#     "location": "Berlin, Germany",
#     "url": "https://linkedin.com/jobs/view/123456",
#     "posted_date": "2025-11-01"
#   },
#   ...
# ]

# Get detailed job info
details = await scraper.get_job_details(job_url="https://linkedin.com/jobs/view/123456")
# Returns: {
#   "description": "We are looking for...",
#   "criteria": {"experience_level": "Mid-Senior level", "job_type": "Full-time"}
# }

# Get scraper statistics
stats = scraper.get_stats()
# Returns: {
#   "requests_made": 150,
#   "jobs_scraped": 125,
#   "errors": 3,
#   "rate_limit_hits": 2
# }
```

**Configuration:**
- `min_delay`, `max_delay`: Random delay range (anti-detection)
- `rate_limit_requests`, `rate_limit_window`: Rate limiting settings
- `cookies_file`: Cookie persistence path
- `proxy`: Proxy URL for IP rotation

### Service Health Checks

All production services implement health check endpoints:

```python
# Check individual service
health = await notification_manager.health_check()
health = await recommendation_engine.health_check()
health = await analytics_facade.health_check()
health = await linkedin_scraper.health_check()

# Health response format
{
    "status": "healthy" | "degraded" | "unhealthy",
    "services": {...},  # Sub-service status
    "stats": {...}      # Service-specific statistics
}
```

### Enterprise Patterns Implemented

1. **Circuit Breaker Pattern** (Analytics Collection)
   - Prevents cascading failures
   - Auto-opens after threshold failures (5 failures)
   - Manual reset capability

2. **Event Queue with Batching** (Notifications, Analytics)
   - Reduces database load
   - Improves performance
   - Configurable batch sizes (100 events) and intervals (30s)

3. **Rate Limiting with Sliding Windows**
   - Per-user/per-identifier limits
   - Prevents abuse
   - Configurable thresholds

4. **Retry with Exponential Backoff** (Notifications, Scraper)
   - Improves reliability
   - 3 retry attempts with 5s, 15s, 60s delays
   - Prevents overwhelming external services

5. **Caching with TTL** (Recommendations, Analytics)
   - Reduces computation (15min for recommendations, 5min for analytics)
   - Improves response times
   - Automatic cache invalidation

6. **A/B Testing Framework** (Recommendations)
   - Data-driven optimization
   - Statistical analysis
   - Deterministic user assignment (MD5-based)

7. **Facade Pattern** (Analytics)
   - Simplified API for common operations
   - Unified interface over multiple services
   - Backward compatibility

### Service Statistics

- **Total Production Code**: 3,240 lines
- **Services**: 8 major services
- **Average Lines per Service**: 405
- **Code Quality**: 0 lint errors (Ruff verified)
- **Test Coverage**: Comprehensive smoke tests passing
- **Architecture**: Async/await, dependency injection, type hints throughout

---

## 📚 Resources

### Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/docs/

### API Documentation

- **Adzuna**: https://developer.adzuna.com/docs
- **Firecrawl**: https://docs.firecrawl.dev/
- **OpenAI**: https://platform.openai.com/docs
- **Groq**: https://console.groq.com/docs

### License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for AI/Data Science professionals seeking opportunities in the EU**

**Last Updated**: November 2, 2025  
**Version**: 1.0.0
