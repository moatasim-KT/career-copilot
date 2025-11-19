# 🚀 Local Development Setup Guide

> **Welcome to Career Copilot!** This guide will help you set up a complete local development environment for the Career Copilot platform - an AI-powered job application tracking system targeting EU tech markets.

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

## 📚 Navigation

### Quick Links
- [[./README.md|Main README]] - Project overview and features
- [[PROJECT_STATUS.md]] - Current development status
- [[docs/index.md]] - Complete documentation index
- [[./CONTRIBUTING.md|Contributing Guidelines]] - How to contribute

### Detailed Guides
- [[docs/setup/INSTALLATION.md]] - Step-by-step installation guide
- [[docs/setup/CONFIGURATION.md]] - Advanced configuration options
- [[docs/development/DEVELOPMENT.md]] - Development workflow best practices
- [[docs/troubleshooting/COMMON_ISSUES.md]] - Common issues and solutions

### Component-Specific Documentation
- [[backend/README.md]] - Backend (FastAPI) development guide
- [[frontend/README.md]] - Frontend (Next.js) development guide
- [[backend/tests/TESTING_NOTES.md]] - Testing strategies and patterns

---

## ⚡ Quick Start (3 Minutes)

Get Career Copilot running locally with these three simple commands. This will start all services using Docker Compose, which handles all dependencies automatically.

### 🆓 Free Tier Setup (Recommended - Zero Cost)

```bash
# 1. Copy the free tier configuration template
cp .env.free-tier-example .env

# 2. Edit .env and add your FREE Groq API key
# Get key from: https://console.groq.com/keys (no credit card required)
nano .env  # or use your preferred editor

# Generate security keys and add to .env:
openssl rand -hex 32  # Copy this to SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"  # Copy to JWT_SECRET_KEY

# 3. Start all services (PostgreSQL, Redis, Backend, Frontend, Celery)
docker-compose up -d

# 4. Initialize database schema (creates all tables)
docker-compose exec backend alembic upgrade head

# 5. Login with default credentials (single-user mode)
# Email: user@career-copilot.local
# Password: changeme123

# 6. Access the application
open http://localhost:3000  # Frontend - Main application UI
open http://localhost:8002/docs  # Backend - Interactive API documentation
```

**💰 Total Cost: $0.00/month** - This configuration uses only free services!

**🔐 Single-User Mode (Default)**: The application runs in single-user mode by default, perfect for personal use. Login with:
- **Email**: `user@career-copilot.local`
- **Password**: `changeme123`
- **Note**: Registration is disabled in single-user mode. Change the password in `.env` via `DEFAULT_USER_PASSWORD`

---

### 💳 Full-Featured Setup (With Paid Services)

If you want to use paid AI providers (OpenAI, Claude) or enhanced services:

```bash
# 1. Copy the full configuration template
cp .env.example .env

# 2. Edit .env and add your API keys (see Configuration section below)
nano .env

# 3. Start services and initialize
docker-compose up -d
docker-compose exec backend alembic upgrade head

# 4. Access the application
open http://localhost:3000
open http://localhost:8002/docs
```

---

**What's happening behind the scenes:**
- PostgreSQL database starts and creates the `career_copilot` database
- Redis starts for caching and background job management
- Backend API (FastAPI) starts on port 8002
- Frontend (Next.js) starts on port 3000
- Celery workers start for background job scraping and AI processing

**First time setup?** After starting services with the free tier config:
1. Verify Groq API key is in `.env` (get free key from https://console.groq.com/keys)
2. Check all services are running: `docker-compose ps`
3. Test the setup: `curl http://localhost:8002/health`

---

## 📋 Prerequisites

Before you begin, ensure your system meets these requirements:

### Required Software
- **Docker 20.10+** and **Docker Compose 2.0+**
  - Why: Simplifies dependency management and ensures consistent environments
  - Install: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes both)
  - Verify: `docker --version && docker-compose --version`

### System Requirements
- **4GB+ RAM available**
  - PostgreSQL: ~500MB
  - Redis: ~100MB
  - Backend + Celery: ~1GB
  - Frontend: ~500MB
  - Additional: ~2GB for Docker overhead and other services

- **10GB+ free disk space**
  - Docker images: ~3GB
  - Application data: ~2GB
  - Logs and temporary files: ~1GB
  - Development buffer: ~4GB

### Optional (for local development without Docker)
- **Python 3.11+** - Backend development
- **Node.js 18+** - Frontend development
- **PostgreSQL 14+** - Local database
- **Redis 7+** - Local cache

---

## 📁 Project Structure

Understanding the project layout will help you navigate the codebase effectively. Career Copilot follows a **monorepo structure** with clear separation between frontend, backend, and infrastructure.

```
career-copilot/
├── 🔧 [[backend/]]                           # FastAPI Backend (Python 3.11+)
│   ├── [[backend/app/]]                      # Main application code
│   │   ├── [[backend/app/api/]]              # REST API endpoints (versioned)
│   │   │   └── v1/                           # API v1 routes (jobs, applications, users, etc.)
│   │   ├── [[backend/app/core/]]             # Core functionality
│   │   │   ├── config.py                     # Configuration management
│   │   │   ├── database.py                   # Database connection & session management
│   │   │   ├── security.py                   # JWT authentication & authorization
│   │   │   └── celery_app.py                 # Celery configuration for background jobs
│   │   ├── [[backend/app/models/]]           # SQLAlchemy ORM models
│   │   │   ├── user.py                       # User accounts & profiles
│   │   │   ├── job.py                        # Job postings (scraped data)
│   │   │   ├── application.py                # Job applications tracking
│   │   │   └── notification.py               # User notifications
│   │   ├── [[backend/app/services/]]         # Business logic layer (100+ services)
│   │   │   ├── job_service.py                # Job management & matching
│   │   │   ├── llm_service.py                # Multi-provider AI integration
│   │   │   ├── scraping/                     # Job board scrapers (12+ boards)
│   │   │   └── job_deduplication_service.py  # Duplicate detection (MinHash + Jaccard)
│   │   └── [[backend/app/tasks/]]            # Celery background tasks
│   │       ├── job_ingestion_tasks.py        # Scheduled job scraping (daily 4 AM UTC)
│   │       └── notification_tasks.py         # Email & push notifications
│   ├── [[backend/tests/]]                    # Comprehensive test suite
│   │   ├── [[backend/tests/TESTING_NOTES.md]] # Testing best practices & async patterns
│   │   ├── [[backend/tests/conftest.py]]     # Shared pytest fixtures (test DB, users)
│   │   ├── unit/                             # Unit tests (fast, isolated)
│   │   ├── integration/                      # Integration tests (DB, services)
│   │   └── e2e/                              # End-to-end tests (full workflows)
│   ├── [[backend/.env.example]]              # Environment variable template
│   └── [[backend/alembic/]]                  # Database migrations (Alembic)
│       └── versions/                         # Migration history
│
├── 🎨 [[frontend/]]                          # Next.js 15 Frontend (React 18, TypeScript)
│   ├── [[frontend/src/app/]]                 # App Router (Next.js 15 file-based routing)
│   │   ├── page.tsx                          # Landing page
│   │   ├── dashboard/                        # Main dashboard (job tracking)
│   │   ├── jobs/                             # Job browsing & search
│   │   └── applications/                     # Application management
│   ├── [[frontend/src/components/]]          # React components
│   │   ├── ui/                               # Reusable UI primitives (shadcn/ui + Radix)
│   │   ├── forms/                            # Form components (applications, profiles)
│   │   ├── jobs/                             # Job-related components
│   │   └── applications/                     # Application tracking components
│   └── [[frontend/src/lib/]]                 # Utilities & shared logic
│       ├── api/client.ts                     # Unified API client (type-safe)
│       ├── hooks/                            # Custom React hooks
│       └── utils/                            # Helper functions
│
├── 🐳 [[docker-compose.yml]]                 # Local development environment (6 services)
├── 🛠️ [[Makefile]]                           # Development commands (test, lint, format, deploy)
│
└── ⚙️ [[config/]]                            # Application configuration
    ├── [[config/llm_config.json]]            # AI provider settings (OpenAI, Groq, Claude)
    ├── [[config/feature_flags.json]]         # Feature toggles (A/B testing, rollouts)
    └── [[config/application.yaml]]           # General app configuration
```

### Key Directories Explained

**Backend (`backend/`)**
- **Purpose**: REST API, business logic, data persistence, background jobs
- **Technology**: FastAPI (async Python), SQLAlchemy (ORM), PostgreSQL
- **Key Features**: Multi-provider AI integration, intelligent job deduplication, scheduled scraping

**Frontend (`frontend/`)**
- **Purpose**: User interface, client-side state management, API consumption
- **Technology**: Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS
- **Key Features**: Server components, optimistic UI updates, real-time WebSocket connections

**Configuration (`config/`)**
- **Purpose**: Centralized configuration for all services
- **Key Files**: 
  - `llm_config.json`: Controls AI provider selection, fallback logic, rate limits
  - `feature_flags.json`: Enable/disable features without code changes
  - `application.yaml`: App-wide settings (CORS, rate limiting, logging)

---

## ⚙️ Configuration

### 💰 Cost Overview - What's Free vs Paid

**TL;DR for free deployment**: Use `.env.free-tier-example` and get a free Groq API key. Everything else is optional.

| Service                   | Free Option Available | Cost If Paid              | Required? | Recommendation              |
| ------------------------- | --------------------- | ------------------------- | --------- | --------------------------- |
| **PostgreSQL**            | ✅ Yes (Docker)        | N/A                       | ✅ Yes     | Use Docker (free)           |
| **Redis**                 | ✅ Yes (Docker)        | N/A                       | ✅ Yes     | Use Docker (free)           |
| **Groq AI**               | ✅ Yes (14k/day)       | N/A                       | ✅ Yes     | **USE THIS** (free forever) |
| **OpenAI GPT**            | ❌ No                  | $0.50-$15 per 1M tokens   | ❌ No      | Skip for free tier          |
| **Anthropic Claude**      | ❌ No                  | $3-$15 per 1M tokens      | ❌ No      | Skip for free tier          |
| **Job Scraping**          | ✅ Yes (web scraping)  | N/A                       | ✅ Yes     | Use free web scraping       |
| **Email (Gmail SMTP)**    | ✅ Yes (personal use)  | N/A                       | ❌ No      | Free for <500 emails/day    |
| **Email (SendGrid)**      | ⚠️ Requires CC         | Free tier 100/day         | ❌ No      | Skip for free tier          |
| **Notifications (Slack)** | ✅ Yes                 | N/A                       | ❌ No      | Completely free             |
| **Calendar (Google)**     | ✅ Yes                 | N/A                       | ❌ No      | Completely free             |
| **Monitoring (Sentry)**   | ⚠️ Requires CC         | Free tier 5k events/month | ❌ No      | Skip for free tier          |

**Legend:**
- ✅ = Completely free, no credit card
- ⚠️ = Free tier exists but requires credit card
- ❌ = Paid only
- **Bold** = Recommended for free tier

---

### Environment Variables - Complete Setup Guide

Career Copilot integrates with multiple external services to provide its full feature set. This section provides **step-by-step instructions** for obtaining and configuring each credential.

**What you'll learn:**
- Which credentials are required vs. optional
- Exactly where to get each API key
- How to configure for 100% free deployment
- Troubleshooting common configuration issues

**Time estimate:** 
- **Free tier setup**: 5-10 minutes (just Groq + security keys)
- **Full setup with all features**: 1-2 hours

#### 🎯 Required Credentials (Must Have)

These are essential for the core platform features to work:

---

#### **1. 🗄️ Database Credentials (PostgreSQL)** - REQUIRED

**Where to configure**: `.env` file in root directory

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot
```

**For Docker Compose** (recommended):
- Uses default credentials: `postgres:postgres`
- Database automatically created as `career_copilot`
- No external setup needed - handled by docker-compose.yml

**For Local PostgreSQL Installation**:
1. Install PostgreSQL 14+: https://www.postgresql.org/download/
2. Create database: `createdb career_copilot`
3. Create user (if needed): `createuser -P postgres`
4. Update DATABASE_URL with your credentials

---

#### **2. ⚡ Redis Credentials** - REQUIRED

**Where to configure**: `.env` file

```bash
REDIS_URL=redis://localhost:6379/0
```

**For Docker Compose** (recommended):
- No authentication required
- Automatically configured

**For Local Redis Installation**:
1. Install Redis 7+: https://redis.io/download/
2. Start Redis: `redis-server`
3. Test connection: `redis-cli ping` (should return "PONG")

---

#### **3. 🔐 Security Keys (JWT & Encryption)** - REQUIRED

**Where to configure**: `.env` file

```bash
# Generate with: openssl rand -hex 32
SECRET_KEY=your-generated-secret-key-min-32-chars

# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-generated-jwt-secret-key-min-32-chars
```

**How to generate**:
```bash
# Method 1: Using OpenSSL (for SECRET_KEY)
openssl rand -hex 32

# Method 2: Using Python (for JWT_SECRET_KEY)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

⚠️ **CRITICAL**: Never commit real secrets to git! Always regenerate for production.

---

#### **4. 🤖 AI/LLM API Key (At Least One)** - REQUIRED

The platform requires at least ONE AI provider for resume generation, job recommendations, and skill analysis.

##### **Option A: Groq (100% FREE - RECOMMENDED FOR SINGLE USER)** ⭐

**Why Groq first?** Completely free tier with 14,400 requests/day - perfect for personal use!

**Where to get**: https://console.groq.com/keys

**Setup steps**:
1. Create account at https://console.groq.com/ (no credit card required)
2. Navigate to API Keys section
3. Generate new API key
4. Copy the key (starts with `gsk_...`)
5. Add to `.env`:
   ```bash
   GROQ_API_KEY=gsk_your-key-here
   GROQ_MODEL=llama-3.1-8b-instant
   GROQ_ENABLED=true
   ```

**Pricing**: 🎁 **FREE** tier with 14,400 requests/day (no credit card needed)
- **Perfect for**: Personal job tracking, quick analysis, skill extraction, high-volume tasks
- **Limitations**: None for typical single-user usage

---

##### **Option B: OpenAI (Paid - Skip if Using Free Tier Only)** 💳

**Where to get**: https://platform.openai.com/api-keys

**⚠️ WARNING**: Requires credit card and charges per API call. **Skip this if you want free-only deployment.**

**Setup steps** (only if you want to pay):
1. Create account at https://platform.openai.com/signup
2. **Add payment method** (required even for trial credits)
3. Navigate to API Keys: https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-proj-...`)
6. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-your-key-here
   OPENAI_MODEL=gpt-3.5-turbo  # Cheapest option
   ```

**Pricing**: https://openai.com/pricing
- GPT-3.5-Turbo: $0.50 / 1M input tokens, $1.50 / 1M output (~$0.002 per request)
- GPT-4: $5.00 / 1M input tokens, $15.00 / 1M output (~$0.02 per request)

---

##### **Option C: Anthropic Claude (Paid - Skip if Using Free Tier Only)** 💳

**Where to get**: https://console.anthropic.com/account/keys

**⚠️ WARNING**: Requires credit card. **Skip this if you want free-only deployment.**

**Setup steps** (only if you want to pay):
1. Sign up at https://console.anthropic.com/
2. **Add payment method** (required)
3. Go to Account → API Keys
4. Create new key
5. Copy the key (starts with `sk-ant-...`)
6. Add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ANTHROPIC_MODEL=claude-3-sonnet-20240229
   ```

**Pricing**: https://www.anthropic.com/pricing
- Claude 3 Sonnet: $3.00 / 1M input tokens, $15.00 / 1M output

---

**💡 For Free Deployment**: Use **Groq only** - it's completely free and handles all AI features perfectly for single-user deployments!

---

#### 🆓 Free Tier Only Configuration (Zero Cost Deployment)

**Want to run Career Copilot without ANY paid services?** Here's your complete free configuration:

##### ✅ What You Get for Free:

1. **Database & Cache** (via Docker): PostgreSQL + Redis - 100% free
2. **AI Provider**: Groq - 14,400 requests/day FREE (no credit card)
3. **Job Scraping**: 12+ job boards via web scraping - 100% free
4. **All Core Features**: Job tracking, applications, AI recommendations - 100% free

##### 🚫 What to DISABLE to Avoid Charges:

Add these to your `.env` file to disable all paid services:

```bash
# ============================================
# FREE TIER ONLY CONFIGURATION
# ============================================

# ✅ ENABLE: Free AI Provider (Groq)
GROQ_API_KEY=gsk_your-groq-key-here
GROQ_MODEL=llama-3.1-8b-instant
GROQ_ENABLED=true

# ❌ DISABLE: Paid AI Providers (leave commented or empty)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=

# ❌ DISABLE: Paid Job Board APIs (use free web scraping instead)
# ADZUNA_APP_ID=
# ADZUNA_APP_KEY=
# INDEED_PUBLISHER_ID=
# RAPIDAPI_KEY=

# ❌ DISABLE: Paid Email Services (use console logging instead)
SMTP_ENABLED=false
# SENDGRID_API_KEY=

# ❌ DISABLE: Paid Monitoring Services
# SENTRY_DSN=

# ✅ ENABLE: Free Notifications (if you have a Slack workspace)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL  # Optional
```

##### 📋 Free Tier Setup Checklist:

1. ✅ **Docker Compose** - Free, includes PostgreSQL + Redis
2. ✅ **Groq API Key** - Sign up at https://console.groq.com/ (no credit card)
3. ✅ **Generate Security Keys** - Run: `openssl rand -hex 32`
4. ❌ **Skip OpenAI** - Leave `OPENAI_API_KEY` blank
5. ❌ **Skip Anthropic** - Leave `ANTHROPIC_API_KEY` blank
6. ❌ **Skip SendGrid** - Set `SMTP_ENABLED=false`
7. ❌ **Skip Sentry** - Leave `SENTRY_DSN` blank
8. ❌ **Skip Paid Job APIs** - Leave Adzuna, Indeed, RapidAPI blank

##### 🎯 Free Tier Performance:

**What you can do with Groq's 14,400 free requests/day:**
- Generate 50+ AI-powered resumes per day
- Analyze 100+ job postings per day
- Extract skills from 200+ job descriptions per day
- Get AI recommendations for 300+ applications per day

**For a single user, this is MORE than enough!** Most users make 10-50 AI requests per day.

##### 🔧 Verify Free Configuration:

After setup, verify no paid services are enabled:

```bash
# Check configuration
cd backend
python -c "
from app.core.config import get_settings
settings = get_settings()

print('=== FREE TIER VERIFICATION ===')
print(f'✅ Groq enabled: {bool(settings.groq_api_key)}')
print(f'❌ OpenAI enabled: {bool(getattr(settings, \"openai_api_key\", None))}')
print(f'❌ Anthropic enabled: {bool(getattr(settings, \"anthropic_api_key\", None))}')
print(f'❌ SendGrid enabled: {bool(getattr(settings, \"sendgrid_api_key\", None))}')
print(f'❌ Sentry enabled: {bool(getattr(settings, \"sentry_dsn\", None))}')
print('')
print('✅ Configuration is FREE TIER ONLY!' if bool(settings.groq_api_key) else '⚠️ Missing Groq API key')
"
```

Expected output:
```
=== FREE TIER VERIFICATION ===
✅ Groq enabled: True
❌ OpenAI enabled: False
❌ Anthropic enabled: False
❌ SendGrid enabled: False
❌ Sentry enabled: False

✅ Configuration is FREE TIER ONLY!
```

---

#### 🎨 Optional Credentials (Enhanced Features)

**Note**: These credentials enable additional features but **aren't required** for basic functionality. Most are free, but some may require payment.

---

#### **5. 🔍 Job Board API Keys (Enhanced Scraping)** - OPTIONAL

The platform includes scrapers for 12+ job boards. **All work for FREE via web scraping**, and several boards offer FREE API access for even better data quality (no credit card required).

##### **Free Tier APIs (Recommended - No Credit Card)**

---

###### **Adzuna Job Search API** - 🆓 FREE (1,000 calls/month)

**Where to get**: https://developer.adzuna.com/signup

**Setup steps**:
1. Register for developer account (no credit card)
2. Confirm email and login
3. Find your App ID and API Key in dashboard
4. Add to `.env`:
   ```bash
   ADZUNA_APP_ID=your-app-id
   ADZUNA_APP_KEY=your-api-key
   ```

**Limits**: 1,000 calls/month (free tier)  
**Coverage**: UK, US, DE, FR, and 18 other countries  
**Free Tier Users**: ✅ **Recommended** - Instant approval, no credit card

---

###### **RapidAPI JSearch** - 🆓 FREE (1,000 requests/month)

**Where to get**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

**Setup steps**:
1. Create RapidAPI account (no credit card for free tier)
2. Subscribe to JSearch API free tier
3. Get API key from dashboard
4. Add to `.env`:
   ```bash
   RAPIDAPI_KEY=your-rapidapi-key
   ```

**Limits**: 1,000 requests/month (free tier)  
**Coverage**: Jobs from Google for Jobs, LinkedIn, Indeed, Glassdoor  
**Free Tier Users**: ✅ **Recommended** - Aggregates multiple sources

---

###### **The Muse API** - 🆓 FREE (500 requests/hour, unlimited)

**Where to get**: https://www.themuse.com/developers/api/v2

**Setup steps**:
1. No signup required!
2. Add to `.env`:
   ```bash
   THE_MUSE_ENABLED=true
   ```

**Limits**: 500 requests/hour (rate limit only, no monthly cap)  
**Coverage**: Curated jobs from top companies, strong focus on company culture  
**Free Tier Users**: ✅ **Recommended** - No API key needed!

---

###### **Remotive API** - 🆓 FREE (Unlimited)

**Where to get**: https://remotive.com/api

**Setup steps**:
1. No signup required!
2. Add to `.env`:
   ```bash
   REMOTIVE_ENABLED=true
   ```

**Limits**: None - completely free public API  
**Coverage**: Remote jobs only (perfect for EU remote work)  
**Free Tier Users**: ✅ **Recommended** - No API key, no limits!

---

###### **RemoteOK API** - 🆓 FREE (Unlimited)

**Where to get**: https://remoteok.com/api

**Setup steps**:
1. No signup required!
2. Add to `.env`:
   ```bash
   REMOTEOK_ENABLED=true
   ```

**Limits**: Rate limit: 1 request per second  
**Coverage**: 100,000+ remote jobs  
**Free Tier Users**: ✅ **Recommended** - No API key needed!

---

##### **APIs to Skip (No Free Tier)**

These APIs require approval, enterprise access, or payment. The platform uses web scraping for these sources instead.

---

###### **Indeed Publisher API** - ⏳ REQUIRES APPROVAL (Skip for Free Tier)

**Where to get**: https://www.indeed.com/publisher

**⚠️ WARNING**: 
- Approval process takes 1-2 weeks
- Requires business justification and website
- May be rejected for personal projects
- **Free Tier Users**: **Skip this** - web scraping works without approval

---

###### **LinkedIn API** - 🚫 ENTERPRISE ONLY (Not Available)

**Note**: LinkedIn API requires approved partnership program and is restricted to enterprise customers only. Not available for individual projects or startups.

**Free Tier Users**: **Skip this** - the scraper uses web scraping instead (requires authentication cookies for best results)

---

###### **Glassdoor API** - 🚫 RESTRICTED PARTNERS ONLY (Not Available)

**Where to get**: https://www.glassdoor.com/developer/index.htm

**Note**: Glassdoor API is restricted to approved partners only. Very difficult to get access.

**Free Tier Users**: **Skip this** - web scraping works for job listings (reviews require API access)

---

#### **6. 📧 Email & Notifications** - OPTIONAL

Enable email notifications for job alerts, application reminders, and weekly summaries.

##### **Console Logging (100% FREE)** - ⭐ RECOMMENDED FOR FREE TIER

**Where to configure**: `.env` file

```bash
SMTP_ENABLED=false  # Notifications logged to console instead
```

**What happens**: All notifications are printed to terminal/logs instead of being emailed. Perfect for single-user deployments!

**View notifications**:
```bash
# Watch notification logs
docker-compose logs -f backend | grep "Notification:"
```

---

##### **Gmail SMTP** - 🆓 FREE (for personal use)

**Where to get**: Use your existing Gmail account

**Setup steps**:
1. Enable 2-Factor Authentication: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`:
   ```bash
   SMTP_ENABLED=true
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

**Pricing**: 🆓 FREE for personal use (Gmail's daily send limit: 500 emails)

---

##### **SendGrid API** - 💳 FREE TIER (100 emails/day)

**Where to get**: https://app.sendgrid.com/settings/api_keys

**⚠️ WARNING**: Requires credit card verification even for free tier.

**Free Tier Users**: Use Gmail SMTP or console logging instead.

---

##### **Slack Notifications** - 🆓 FREE

**Where to get**: https://api.slack.com/messaging/webhooks

**Setup steps**:
1. Create Slack workspace (free) or use existing
2. Create incoming webhook: https://api.slack.com/apps
3. Add to `.env`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SLACK_CHANNEL=#job-alerts
   ```

**Pricing**: 🆓 Completely free

---

#### **7. 🔗 OAuth Integrations (Calendar Sync)** - OPTIONAL (100% FREE)

Connect calendar services to auto-add interview dates and deadlines.

##### **Google Calendar OAuth** - 🆓 FREE

**Where to get**: https://console.cloud.google.com/apis/credentials

**Setup steps**:
1. Create Google Cloud project (free): https://console.cloud.google.com/
2. Enable Google Calendar API (free)
3. Create OAuth 2.0 credentials (no credit card required)
4. Add redirect URI: `http://localhost:8002/api/v1/calendar/google/callback`
5. Add to `.env`:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

**Pricing**: 🆓 Completely free

---

##### **Microsoft Outlook Calendar OAuth** - 🆓 FREE

**Where to get**: https://portal.azure.com/

**Setup steps**:
1. Create Azure account (free): https://portal.azure.com/
2. Register app (free, no credit card)
3. Add to `.env`:
   ```bash
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-client-secret
   ```

**Pricing**: 🆓 Completely free

---

##### **GitHub OAuth** - 🆓 FREE

**Where to get**: https://github.com/settings/developers

**Setup steps**:
1. Create OAuth App (free)
2. Add to `.env`:
   ```bash
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   ```

**Pricing**: 🆓 Completely free

---

#### **8. 📊 Monitoring & Error Tracking** - OPTIONAL

##### **Sentry Error Tracking** - 💳 FREE TIER (5,000 events/month)

**Where to get**: https://sentry.io/

**⚠️ WARNING**: Requires credit card for free tier.

**Free Tier Users**: **Skip this** - use console logs instead:
```bash
# Monitor errors in logs
docker-compose logs -f backend | grep ERROR
```

---

### 📂 Configuration File Locations

Career Copilot uses **multiple configuration files** to separate concerns and improve security. Understanding where each configuration belongs is crucial for proper setup.

#### Configuration Strategy

The platform follows a **layered configuration approach**:
1. **Root `.env`**: Shared credentials (database, AI providers, secrets)
2. **Backend `.env`**: Backend-specific overrides (rare)
3. **Frontend `.env`**: Public frontend configuration (no secrets!)
4. **Config JSON files**: Application behavior (not credentials)

Credentials are split across multiple `.env` files depending on the component:

| File Location                   | Purpose                               | Required Variables                                              |
| ------------------------------- | ------------------------------------- | --------------------------------------------------------------- |
| **Root `.env`**                 | Backend API, Celery, Database         | `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `OPENAI_API_KEY` |
| **`backend/.env`**              | Backend-specific overrides (optional) | Same as root, can override                                      |
| **`frontend/.env`**             | Next.js frontend                      | `NEXT_PUBLIC_API_URL` (defaults to http://localhost:8002)       |
| **`config/llm_config.json`**    | LLM provider settings                 | API keys referenced from `.env`, priorities and model configs   |
| **`config/feature_flags.json`** | Feature toggles                       | No credentials, controls feature availability                   |

#### 🔧 Creating Your Environment Files - Step by Step

Follow these steps in order to configure your local environment:

**Step 1: Copy the root environment template**
```bash
# From project root directory
cp .env.example .env
```

**Step 2: Configure required variables**

Open `.env` in your text editor and update these **REQUIRED** variables (see "Required Credentials" section above for details):

```bash
# 1. Database (if using Docker, keep defaults)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot

# 2. Redis (if using Docker, keep defaults)
REDIS_URL=redis://localhost:6379/0

# 3. Generate secure secrets (run these commands to generate)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 4. Add at least ONE AI provider (required for core features)
OPENAI_API_KEY=sk-proj-your-actual-key-here  # Get from platform.openai.com
# OR
GROQ_API_KEY=gsk_your-actual-key-here        # Get from console.groq.com (FREE tier)
```

**Step 3: Configure frontend (optional - has sensible defaults)**

The frontend requires minimal configuration. Only needed if your backend isn't on `localhost:8002`:

```bash
cd frontend
cp .env.example .env

# Edit frontend/.env (only if needed)
NEXT_PUBLIC_API_URL=http://localhost:8002  # Default - change if backend port differs
```

**Step 4: Verify configuration**

Test that your configuration is valid before starting services:

```bash
# Test 1: Backend can load configuration
cd backend
python -c "from app.core.config import get_settings; settings = get_settings(); print('✅ Config loaded successfully')"

# Test 2: Start services
docker-compose up -d

# Test 3: Check backend health
curl http://localhost:8002/health
# Expected output: {"status":"healthy","version":"3.3.0","database":"connected","redis":"connected"}

# Test 4: Check frontend is serving
curl http://localhost:3000
# Should return HTML (no errors)
```

**Common Setup Issues:**
- ❌ "Could not load config": Check `.env` file exists in project root
- ❌ "Database connection failed": Ensure PostgreSQL is running (`docker-compose ps postgres`)
- ❌ "Invalid API key": Verify your AI provider key is correct and has billing enabled
- ❌ "Port already in use": Another service is using 3000, 8000, 8002, 5432, or 6379 - change ports in `docker-compose.yml`

---

---

### LLM Provider Configuration

The platform supports multiple AI providers with intelligent routing. Configure provider priorities and model selection in [[config/llm_config.json]]:

```json
{
  "providers": {
    "openai": {
      "enabled": true,
      "priority": 1,
      "models": {
        "gpt-4": {"max_tokens": 8192, "cost_per_1k_tokens": 0.03},
        "gpt-3.5-turbo": {"max_tokens": 4096, "cost_per_1k_tokens": 0.002}
      }
    },
    "groq": {
      "enabled": true,
      "priority": 2,
      "models": {
        "llama-3.1-8b-instant": {"max_tokens": 8192, "cost_per_1k_tokens": 0.0}
      }
    }
  }
}
```

**Configuration Details**:
- `priority`: Lower number = higher priority (1 is highest)
- Platform automatically falls back to next provider if primary fails
- Cost tracking helps optimize provider selection
- See [[backend/app/services/llm_service.py]] for routing logic

---

### Frontend Environment Variables

Frontend configuration in `frontend/.env`:

```bash
# Backend API URL (REQUIRED)
NEXT_PUBLIC_API_URL=http://localhost:8002

# Sentry DSN for frontend error tracking (OPTIONAL)
NEXT_PUBLIC_SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/123456

# Feature flags (OPTIONAL - defaults to all enabled)
NEXT_PUBLIC_ENABLE_CALENDAR_SYNC=true
NEXT_PUBLIC_ENABLE_EMAIL_NOTIFICATIONS=true
NEXT_PUBLIC_ENABLE_AI_RECOMMENDATIONS=true
```

**Note**: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser, so never put secrets there!

---

### Troubleshooting Configuration Issues

#### "Invalid API Key" Errors

**Problem**: `401 Unauthorized` or `Invalid API key` errors

**Solutions**:
1. Verify API key is correct (no extra spaces, complete key)
2. Check API key hasn't expired (regenerate if needed)
3. Verify API key has correct permissions
4. For OpenAI: Ensure billing is set up: https://platform.openai.com/account/billing

```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test Groq key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_GROQ_KEY"
```

#### Database Connection Errors

**Problem**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions**:
1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Verify DATABASE_URL format: `postgresql://user:password@host:port/database`
3. Test connection:
   ```bash
   psql "postgresql://postgres:postgres@localhost:5432/career_copilot"
   ```
4. Check Docker network: `docker network ls` (should see `career-copilot_default`)

#### Redis Connection Errors

**Problem**: `redis.exceptions.ConnectionError`

**Solutions**:
1. Check Redis is running: `docker-compose ps redis`
2. Test connection: `redis-cli -h localhost -p 6379 ping`
3. Verify REDIS_URL in `.env`: `redis://localhost:6379/0`

#### OAuth Callback Errors

**Problem**: OAuth redirects fail with `redirect_uri_mismatch`

**Solutions**:
1. Verify redirect URI in OAuth provider settings matches exactly:
   - Google: Should be `http://localhost:8002/api/v1/calendar/google/callback`
   - GitHub: Should be `http://localhost:8002/api/v1/auth/github/callback`
2. No trailing slashes in URLs
3. Protocol must match (http vs https)
4. Port must match (8002 for development)

#### Email Sending Fails

**Problem**: SMTP authentication errors

**Solutions**:
1. Gmail users: Use App Password, not account password
2. Verify SMTP_PORT is 587 (TLS) not 465 (SSL)
3. Enable "Less secure app access" if using basic auth (not recommended)
4. Check SMTP credentials: `SMTP_USERNAME` should be full email address

```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('✅ SMTP connection successful')
server.quit()
"
```

---

### Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Rotate secrets regularly** - Especially for production
3. **Use different secrets per environment** - Don't reuse dev keys in production
4. **Limit API key permissions** - Only grant necessary scopes
5. **Monitor API usage** - Set up billing alerts to avoid surprise charges
6. **Use environment-specific keys** - Separate development and production credentials

For more details on security configuration, see [[docs/security/security-guidelines.md]].

---

### 1. Backend Environment

Copy and configure the main `.env` file (see detailed credential guide above):

```bash
cp .env.example .env
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

## 🐳 Docker Compose Services

The [[docker-compose.yml]] file orchestrates **6 interconnected services** that form the complete Career Copilot development environment. Understanding each service helps with debugging and customization.

### Service Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Career Copilot Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  HTTP/WS  ┌──────────┐  SQL   ┌──────────┐   │
│  │ Frontend │◄──────────►│ Backend  │◄──────►│PostgreSQL│   │
│  │(Next.js) │            │(FastAPI) │        │  (5432)  │   │
│  │  :3000   │            │  :8000   │        └──────────┘   │
│  └──────────┘            └────┬─────┘                        │
│                               │                              │
│                         ┌─────┴─────┐                        │
│                         │           │                        │
│                    ┌────▼───┐  ┌───▼────┐                   │
│                    │ Redis  │  │ Celery │                   │
│                    │ (6379) │  │Workers │                   │
│                    └────────┘  │& Beat  │                   │
│                                └────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Service Details

The [[docker-compose.yml]] file defines these 6 services:

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

## 🔄 Development Workflow

This section covers the **day-to-day development tasks** you'll perform while working on Career Copilot. We emphasize code quality, automated testing, and consistent formatting.

### Git Hooks & Linting Guardrails

**Why we use pre-commit hooks:** They catch code quality issues *before* they reach CI/CD, saving time and reducing feedback cycles. All code is automatically formatted and linted on commit.

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

**Testing Philosophy:** Career Copilot follows a **test pyramid approach**:
- **Unit tests** (70%): Fast, isolated tests of individual functions/classes
- **Integration tests** (20%): Test service interactions and database operations
- **E2E tests** (10%): Full user workflow tests

Tests are in [[backend/tests/]]. See [[backend/tests/TESTING_NOTES.md]] for comprehensive testing patterns and async testing strategies.

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

## 🏗️ Service Architecture & Communication

Understanding how services communicate helps with debugging and adding new features. Career Copilot uses a **microservices-inspired architecture** within a monorepo.

### Communication Patterns

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

## 📝 Common Development Tasks

This section provides **copy-paste ready commands** for frequent development tasks. Bookmark this section for quick reference!

### Creating a Test User

**When you need this:** Testing authentication, user-specific features, or application workflows without going through the signup flow.

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

## 🔍 Troubleshooting Guide

**Before diving into specific issues:** Always check the basics first:
1. Are all services running? `docker-compose ps`
2. Check logs for errors: `docker-compose logs --tail=50`
3. Verify `.env` file exists and has required variables
4. Ensure no port conflicts (3000, 8000, 8002, 5432, 6379)

### Service Won't Start

**Symptoms:** `docker-compose up` fails or service shows as "Exit 1" in `docker-compose ps`

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

## 🧹 Stopping & Cleanup

### Graceful Shutdown

**Best practice:** Stop services gracefully to avoid data corruption:

```bash
# Stop all services (preserves data volumes)
docker-compose down

# View what will be removed before doing it
docker-compose down --dry-run
```

### Data Cleanup (⚠️ Destructive Operations)

**Warning:** The following commands will **permanently delete data**. Use with caution!

```bash
# Stop and remove volumes (⚠️ deletes database, Redis data, logs)
docker-compose down -v

# Remove all Career Copilot containers, volumes, and networks
docker-compose down -v --remove-orphans

# Clean Docker system (removes unused images, containers, networks)
docker system prune -a

# Clean build cache (frees disk space)
docker builder prune
```

### Partial Cleanup (Recommended)

```bash
# Remove only stopped containers
docker-compose rm

# Remove unused images (keeps running ones)
docker image prune

# Clean logs but keep data
rm -rf data/logs/*
```

### Fresh Start Checklist

When you need a **completely fresh environment**:

```bash
# 1. Stop everything
docker-compose down -v

# 2. Remove .env (you'll need to reconfigure)
rm .env

# 3. Clean Docker artifacts
docker system prune -a

# 4. Remove local data directories
rm -rf data/postgres data/redis data/chroma data/logs

# 5. Start fresh
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

---

## 💡 Development Tips & Best Practices

These tips come from real development experience with Career Copilot. Following them will make your development smoother!

### 1. 🔥 Hot Reload Configuration

**Both frontend and backend support hot reload** - your changes appear instantly without manual restarts:

- **Backend**: Uvicorn auto-reloads on file changes (enabled via `--reload` flag in [[docker-compose.yml]])
  - Applies to: Python files in `backend/app/`
  - Restart time: 1-2 seconds
  - **Tip**: Large changes may require manual restart: `docker-compose restart backend`

- **Frontend**: Next.js dev server has Fast Refresh (sub-second updates)
  - Applies to: React components, CSS, pages
  - Preserves component state during updates
  - **Tip**: If hot reload breaks, refresh browser or restart: `docker-compose restart frontend`

### 2. 🔌 API Client Usage

**Frontend uses a unified API client** in [[frontend/src/lib/api/client.ts]] - **always use this, never raw `fetch()`**:

```typescript
// ✅ CORRECT - Type-safe, handles auth, consistent error handling
import { fetchApi } from '@/lib/api/client';

const jobs = await fetchApi<Job[]>('/jobs', {
  params: { limit: 10 },
  requiresAuth: false
});

// ❌ WRONG - No types, manual auth handling, inconsistent errors
const response = await fetch('http://localhost:8000/api/v1/jobs');
const jobs = await response.json();
```

**Benefits:**
- Automatic authentication token handling
- TypeScript types for all endpoints
- Consistent error handling across the app
- Request/response interceptors for logging

### 3. 🏗️ Service Layer Pattern

**Business logic belongs in [[backend/app/services/]], NOT in API routes**. This keeps routes thin and logic reusable:

```python
# ✅ CORRECT - Thin route, logic in service
@router.post("/jobs/search")
def search_jobs(filters: JobFilters, db: Session = Depends(get_db)):
    service = JobService(db)
    return service.search_jobs(filters)

# ❌ WRONG - Business logic in route
@router.post("/jobs/search")
def search_jobs(filters: JobFilters, db: Session = Depends(get_db)):
    # 50 lines of filtering logic here...
    jobs = db.query(Job).filter(...).all()
```

**See [[.github/copilot-instructions.md]] for detailed architectural patterns**

### 4. ⚙️ Configuration Management

Career Copilot uses **layered configuration** for flexibility:

| File                          | Purpose                 | When to Edit                  |
| ----------------------------- | ----------------------- | ----------------------------- |
| [[config/feature_flags.json]] | Enable/disable features | A/B testing, gradual rollouts |
| [[config/llm_config.json]]    | AI provider priorities  | Change provider, adjust costs |
| [[config/application.yaml]]   | App-wide settings       | CORS, rate limits, timeouts   |
| `.env`                        | Secrets & credentials   | Never commit, local only      |

**Example: Enable a new feature for 10% of users**
```json
// config/feature_flags.json
{
  "new_ai_recommendations": {
    "enabled": true,
    "rollout_percentage": 10
  }
}
```

### 5. 🧪 Testing Best Practices

**Test structure mirrors application structure:**

```
backend/app/services/job_service.py
→ backend/tests/unit/test_job_service.py
→ backend/tests/integration/test_job_service_integration.py
```

**Key resources:**
- Write tests in [[backend/tests/]]
- Use shared fixtures from [[backend/tests/conftest.py]] (includes test DB, test users)
- See [[backend/tests/TESTING_NOTES.md]] for async testing patterns and mocking strategies

**Quick test commands:**
```bash
# Run specific test file
pytest backend/tests/unit/test_job_service.py -v

# Run tests matching pattern
pytest -k "test_job_deduplication" -v

# Run with coverage report
pytest --cov=backend/app/services --cov-report=html
```

### 6. 🐛 Debugging Tips

**Backend debugging:**
```bash
# Add breakpoint in Python code
import pdb; pdb.set_trace()

# View SQL queries
# Add to .env: SQLALCHEMY_ECHO=true

# Check service health
curl http://localhost:8000/health | jq
```

**Frontend debugging:**
```typescript
// React DevTools is your friend
// Add logging in components
console.log('[JobCard] Rendering with:', job);

// Check API calls in Network tab
// All API calls go through /api/v1/* prefix
```

### 7. 📊 Monitoring & Logs

**Real-time log monitoring:**
```bash
# Watch all service logs
docker-compose logs -f

# Watch specific service
docker-compose logs -f backend

# Search logs for errors
docker-compose logs | grep ERROR

# Last 100 lines
docker-compose logs --tail=100
```

**Log locations:**
- Backend: `data/logs/backend/app.log`
- Celery: `data/logs/celery/celery.log`
- PostgreSQL: `docker-compose logs postgres`

### 8. 🚀 Performance Tips

**Backend:**
- Use async routes for I/O-bound operations
- Leverage Redis caching for expensive queries
- Monitor database query performance with `SQLALCHEMY_ECHO=true`

**Frontend:**
- Use Next.js Server Components for data fetching
- Lazy load heavy components with `next/dynamic`
- Check Lighthouse scores: `npm run lighthouse` (in frontend/)

---

## 🎯 Next Steps

Congratulations! You now have Career Copilot running locally. Here's your learning path:

### Immediate Next Steps (First Hour)
1. **Explore the UI** - Navigate to http://localhost:3000
   - Create a test user account
   - Browse the dashboard and job listings
   - Try creating a test application

2. **Review the API** - Check http://localhost:8000/docs
   - Interactive API documentation (Swagger UI)
   - Try the `/health` endpoint
   - Explore available endpoints

3. **Check the Architecture** - Read [[./README.md|Main README]]
   - Understand the core features
   - See the tech stack overview
   - Review the project roadmap

### Deepening Your Understanding (First Day)

4. **Learn the Coding Patterns** - Study [[.github/copilot-instructions.md]]
   - Service layer architecture
   - Database conventions
   - Testing strategies
   - Code quality standards

5. **Backend Deep Dive** - Read [[backend/README.md|Backend Documentation]]
   - Core architecture and patterns
   - Database models and relationships
   - Service layer organization
   - Background job system (Celery)

6. **Frontend Deep Dive** - Read [[frontend/README.md|Frontend Documentation]]
   - Next.js 15 App Router patterns
   - Component organization
   - State management approach
   - API client usage

### Advanced Topics (First Week)

7. **Explore Services** - Review [[backend/app/services/README.md]]
   - 100+ service catalog with descriptions
   - Service categories and responsibilities
   - Integration patterns

8. **Browse API Endpoints** - Navigate [[backend/app/api/v1/]]
   - Jobs API (`/jobs/*`)
   - Applications API (`/applications/*`)
   - Users & Auth API (`/users/*`, `/auth/*`)
   - Notifications API (`/notifications/*`)

9. **Study Testing** - Read [[backend/tests/TESTING_NOTES.md]]
   - Async testing patterns
   - Fixture usage and best practices
   - Integration test strategies
   - Mocking external services

### Contributing to the Project

10. **Check Active Work** - Review [[TODO.md]]
    - Current sprint tasks
    - Open issues and feature requests
    - Areas needing help

11. **Read Contributing Guidelines** - Study [[./CONTRIBUTING.md|Contributing Guidelines]]
    - Git workflow and branch naming
    - Pull request process
    - Code review expectations
    - Documentation standards

### Getting Help

12. **Troubleshooting** - See [[docs/troubleshooting/COMMON_ISSUES.md]]
    - Common setup problems and solutions
    - Performance optimization tips
    - Debugging strategies

---

## 📞 Support & Community

### Getting Help

**Found a bug?** **Need help?** **Have a feature idea?**

- **GitHub Issues**: https://github.com/moatasim-KT/career-copilot/issues
  - Bug reports: Use "bug" label
  - Feature requests: Use "enhancement" label
  - Questions: Use "question" label

- **Project Board**: Check [[TODO.md]] for active work and priorities

- **Documentation**: Browse [[docs/index.md]] for comprehensive guides

### Before Asking for Help

1. Check this setup guide for solutions
2. Search existing GitHub issues
3. Review [[docs/troubleshooting/COMMON_ISSUES.md]]
4. Check service logs: `docker-compose logs`

### Reporting Bugs

When reporting bugs, please include:
- Operating system and version
- Docker version: `docker --version`
- Error messages from logs: `docker-compose logs backend`
- Steps to reproduce
- Expected vs actual behavior

---

## 🎉 You're All Set!

You now have a complete Career Copilot development environment! Here's a quick recap:

✅ Services running (PostgreSQL, Redis, Backend, Frontend, Celery)  
✅ Configuration files set up (.env)  
✅ Database initialized (Alembic migrations)  
✅ Frontend accessible at http://localhost:3000  
✅ API docs available at http://localhost:8000/docs  

**Happy coding!** 🚀
