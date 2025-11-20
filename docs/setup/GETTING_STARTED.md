# Getting Started with Career Copilot

> **Consolidated Guide**: This document combines content from multiple setup guides for easier navigation.
> - Formerly: `FRONTEND_QUICK_START.md`, `FREE_TIER_SETUP.md`, `setup/getting-started.md`, `setup/INSTALLATION.md`, `setup/FREE_API_SETUP.md`, `setup/CONFIGURATION.md`

**Quick Links**: [[index|Documentation Hub]] | [[DEVELOPER_GUIDE|Developer Guide]] | [[USER_GUIDE|User Guide]] | [[ENVIRONMENT_CONFIGURATION|Environment Configuration]]

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [Free Tier Setup](#free-tier-setup)
3. [Docker Installation](#docker-installation)
4. [Local Development Setup](#local-development-setup)
5. [Frontend Development](#frontend-development)
6. [Configuration Reference](#configuration-reference)
7. [Free API Setup (Optional)](#free-api-setup-optional)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop (free): https://www.docker.com/products/docker-desktop/
- **OR** for local development:
  - Python 3.11+
  - Node.js 18.0+
  - PostgreSQL 14+
  - Redis 7+

### Step 1: Clone & Configure

```bash
# Clone repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# Copy free tier configuration
cp .env.free-tier-example .env
```

### Step 2: Get FREE Groq API Key (2 minutes)

1. Visit: https://console.groq.com/keys
2. Sign up (NO credit card required)
3. Click "Create API Key"
4. Copy the key (starts with `gsk_...`)

### Step 3: Generate Security Keys (1 minute)

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY  
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Edit .env File

Open `.env` and replace these 3 values:

```bash
# Paste your generated keys
SECRET_KEY=paste-generated-secret-key-here
JWT_SECRET_KEY=paste-generated-jwt-secret-key-here

# Paste your FREE Groq API key
GROQ_API_KEY=gsk_paste-your-groq-key-here
```

### Step 5: Start Services

```bash
# Start all services with Docker
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head

# Verify everything is running
docker-compose ps
```

### Step 6: Access Application ✅

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Free Tier Setup

**Total Monthly Cost: $0.00** 💰

### What You Get For Free

#### ✅ Core Features (100% Free)

1. **Job Tracking**
   - Track unlimited job applications
   - Organize by status (Applied, Interview, Offer, etc.)
   - Add notes, deadlines, and contacts

2. **AI-Powered Features** (14,400 requests/day via Groq)
   - AI-generated cover letters
   - Resume optimization suggestions
   - Job description analysis
   - Skill gap identification
   - Interview preparation tips

3. **Job Scraping** (12+ job boards + 5 FREE APIs)
   - **Web Scraping (No API Key Needed)**:
     - LinkedIn, Indeed, StepStone, Monster
     - Glassdoor, WeWorkRemotely
     - AngelList, Arbeitnow
     - Berlin Startup Jobs, AIJobs.net
   
   - **FREE APIs (Optional - Better Data Quality)**:
     - ✅ **Adzuna** - 1,000 calls/month (22 countries)
     - ✅ **RapidAPI JSearch** - 1,000 requests/month
     - ✅ **The Muse** - 500 requests/hour
     - ✅ **Remotive** - Unlimited (remote jobs only)
     - ✅ **RemoteOK** - Unlimited (100k+ remote jobs)

4. **Dashboard & Analytics**
   - Application pipeline visualization
   - Response rate tracking
   - Time-to-hire statistics
   - Success metrics

### Usage Limits (Free Tier)

| Feature | Limit | Typical Usage | More Than Enough? |
|---------|-------|---------------|-------------------|
| AI Requests | 14,400/day | 10-50/day | ✅ Yes (280x) |
| Job Scraping (Web) | Unlimited | N/A | ✅ Yes |
| Adzuna API | 1,000/month | 30/day | ✅ Yes |
| RapidAPI JSearch | 1,000/month | 30/day | ✅ Yes |
| The Muse API | 500/hour | 10/hour | ✅ Yes (50x) |
| Applications | Unlimited | N/A | ✅ Yes |
| Storage | Unlimited* | ~100MB | ✅ Yes |

*Limited only by your disk space

**Total**: Easily 50,000+ unique job postings per month for FREE!

---

## Docker Installation

The recommended way to run the application is with Docker Compose.

### Start All Services

```bash
docker-compose up -d
```

### Access the Application

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Verify Installation

```bash
# Check all services are running
docker-compose ps
# Should show: postgres, redis, backend, frontend, celery, celery-beat (all "Up")

# Test backend health
curl http://localhost:8000/health
# Should return: {"status":"healthy","database":"connected","redis":"connected"}

# Verify FREE Groq is enabled
docker-compose exec backend python -c "
from app.core.config import get_settings
s = get_settings()
print('✅ FREE TIER VERIFIED' if s.groq_api_key and not getattr(s, 'openai_api_key', None) else '⚠️ CHECK CONFIG')
"
# Should print: ✅ FREE TIER VERIFIED
```

---

## Local Development Setup

For local development without Docker, you'll need to set up the backend and frontend separately.

### Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your database and AI provider credentials.

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.local.example .env.local
   ```
   Edit the `.env.local` file with your API URL and WebSocket URL.

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Access the frontend at `http://localhost:3000`

---

## Frontend Development

See [[DEVELOPER_GUIDE#frontend-development|Frontend Development Guide]] for detailed information.

### Quick Start for Frontend Developers

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start Dev Server**:
   ```bash
   npm run dev
   ```

3. **Key Frontend Technologies**:
   - Next.js 14+ (App Router)
   - React 18+
   - TypeScript
   - Tailwind CSS v4
   - Framer Motion (animations)
   - TanStack React Table
   - React Hook Form

4. **Project Structure**:
   ```
   frontend/
   ├── src/
   │   ├── app/            # Next.js App Router pages
   │   ├── components/     # React components
   │   ├── lib/            # Utilities and services
   │   ├── hooks/          # Custom React hooks
   │   └── contexts/       # React Context providers
   ```

For comprehensive frontend setup including design system installation, see the original [[FRONTEND_QUICK_START|Frontend Quick Start Guide]].

---

## Configuration Reference

### Required Environment Variables

```bash
# Security (Required - Generate with commands above)
SECRET_KEY=your-generated-key
JWT_SECRET_KEY=your-generated-key

# AI Provider (Required - Get from https://console.groq.com/keys)
GROQ_API_KEY=gsk_your-groq-key

# Database (Docker handles these automatically)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot

# Redis (Docker handles this automatically)
REDIS_URL=redis://localhost:6379/0
```

### Optional Free APIs

```bash
# Adzuna API (Recommended - 1,000 calls/month)
# Get from: https://developer.adzuna.com/signup
ADZUNA_APP_ID=your-app-id
ADZUNA_APP_KEY=your-api-key

# RapidAPI JSearch (Recommended - 1,000 requests/month)
# Get from: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
RAPIDAPI_KEY=your-rapidapi-key

# Enable free public APIs (no signup needed)
THE_MUSE_ENABLED=true
REMOTIVE_ENABLED=true
REMOTEOK_ENABLED=true
```

### Services to Disable (Free Tier)

```bash
# Disable paid services
SMTP_ENABLED=false
OPENAI_API_KEY=  # Leave empty
ANTHROPIC_API_KEY=  # Leave empty
SENDGRID_API_KEY=  # Leave empty
SENTRY_DSN=  # Leave empty

# Disable restricted APIs (use web scraping instead)
INDEED_PUBLISHER_ID=  # Leave empty
LINKEDIN_API_KEY=  # Leave empty
GLASSDOOR_PARTNER_ID=  # Leave empty
```

For complete environment configuration details, see [[ENVIRONMENT_CONFIGURATION|Environment Configuration Guide]].

---

## Free API Setup (Optional)

These are **completely optional** but 100% free and improve data quality.

### 1. Adzuna API (2 minutes)

**Coverage**: 22 countries including UK, US, DE, FR, NL, BE, AT, CH  
**Limit**: 1,000 calls/month (free tier)  
**Credit Card**: NO

**Setup**:
1. Sign up: https://developer.adzuna.com/signup
2. Get your **App ID** and **API Key** from dashboard
3. Add to `.env`:
   ```bash
   ADZUNA_APP_ID=your-app-id-here
   ADZUNA_APP_KEY=your-api-key-here
   ```
4. Restart services: `docker-compose restart backend celery`

### 2. RapidAPI JSearch (2 minutes)

**Coverage**: Aggregates Google Jobs, LinkedIn, Indeed, Glassdoor  
**Limit**: 1,000 requests/month (free tier)  
**Credit Card**: NO

**Setup**:
1. Sign up: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Subscribe to free plan
3. Copy API key from dashboard
4. Add to `.env`:
   ```bash
   RAPIDAPI_KEY=your-rapidapi-key-here
   ```
5. Restart services: `docker-compose restart backend celery`

### 3. The Muse (No signup needed!)

**Coverage**: Curated jobs, company culture focus  
**Limit**: 500 requests/hour  
**Setup**: Just enable in `.env`:
```bash
THE_MUSE_ENABLED=true
```

### 4. Remotive (No signup needed!)

**Coverage**: Remote jobs only  
**Limit**: Unlimited  
**Setup**: Just enable in `.env`:
```bash
REMOTIVE_ENABLED=true
```

### 5. RemoteOK (No signup needed!)

**Coverage**: 100k+ remote jobs  
**Limit**: 1 request/second  
**Setup**: Just enable in `.env`:
```bash
REMOTEOK_ENABLED=true
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker --version

# View logs for errors
docker-compose logs backend
docker-compose logs frontend
```

### Database Connection Failed

```bash
# Wait for PostgreSQL to be ready (can take 10-30 seconds)
docker-compose logs postgres | grep "ready to accept connections"

# Restart backend after database is ready
docker-compose restart backend
```

### Invalid API Key (Groq)

1. Verify key starts with `gsk_`
2. Check no extra spaces in `.env`
3. Regenerate key at: https://console.groq.com/keys
4. Restart services: `docker-compose restart`

### Frontend Shows Blank Page

```bash
# Wait for build to complete (first time: 1-2 minutes)
docker-compose logs frontend | tail -20

# Look for: "ready - started server on 0.0.0.0:3000"
```

### AI Features Not Working

```bash
# Verify Groq configuration
docker-compose exec backend python -c "
from app.services.llm_service import LLMService
service = LLMService()
print('✅ Groq working' if service.groq_client else '❌ Check GROQ_API_KEY')
"
```

For more troubleshooting, see [[troubleshooting/COMMON_ISSUES|Common Issues Guide]].

---

## Next Steps

1. **Create Your Profile**
   - Go to http://localhost:3000
   - Sign up with email
   - Add your resume and preferences

2. **Browse Jobs**
   - Automatic scraping runs daily at 4 AM UTC
   - Or manually trigger: Settings → Scrape Jobs Now

3. **Track Applications**
   - Add applications manually
   - Or save directly from scraped jobs
   - Use AI to generate cover letters

4. **Explore Dashboard**
   - View application pipeline
   - Check analytics
   - Monitor response rates

---

## Additional Resources

- **User Guide**: [[USER_GUIDE|Complete User Guide]]
- **Developer Guide**: [[DEVELOPER_GUIDE|Developer Documentation]]
- **Architecture**: [[architecture/ARCHITECTURE|System Architecture]]
- **API Reference**: [[api/API|API Documentation]]
- **Troubleshooting**: [[troubleshooting/RUNBOOK|Operations Runbook]]

---

**Last Updated**: November 2025  
**Free Tier Configuration**: `.env.free-tier-example`
