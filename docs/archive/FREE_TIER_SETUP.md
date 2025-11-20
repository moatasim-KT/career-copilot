# 🆓 Career Copilot - Free Tier Setup Guide

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

**Total Monthly Cost: $0.00** 💰

This guide shows you how to run Career Copilot using **ONLY FREE services** - no credit card required!

---

## ⚡ 5-Minute Setup

### Step 1: Prerequisites
- Install Docker Desktop (free): https://www.docker.com/products/docker-desktop/
- That's it! 

### Step 2: Clone & Configure

```bash
# Clone repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# Copy free tier configuration
cp .env.free-tier-example .env
```

### Step 3: Get FREE Groq API Key (2 minutes)

1. Visit: https://console.groq.com/keys
2. Sign up (NO credit card required)
3. Click "Create API Key"
4. Copy the key (starts with `gsk_...`)

### Step 4: Generate Security Keys (1 minute)

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY  
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Edit .env File (1 minute)

Open `.env` and replace these 3 values:

```bash
# Paste your generated keys
SECRET_KEY=paste-generated-secret-key-here
JWT_SECRET_KEY=paste-generated-jwt-secret-key-here

# Paste your FREE Groq API key
GROQ_API_KEY=gsk_paste-your-groq-key-here
```

### Step 6: Start Services (1 minute)

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head

# Verify everything is running
docker-compose ps
```

### Step 7: Access Application ✅

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health

---

## 🎯 What You Get For Free

### ✅ Core Features (100% Free)

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
     - ✅ **RapidAPI JSearch** - 1,000 requests/month (aggregates Google Jobs, LinkedIn, Indeed)
     - ✅ **The Muse** - 500 requests/hour (curated jobs, company culture focus)
     - ✅ **Remotive** - Unlimited (remote jobs only)
     - ✅ **RemoteOK** - Unlimited (100k+ remote jobs)

4. **Automatic Deduplication**
   - Smart duplicate detection across job boards
   - MinHash + Jaccard similarity algorithm
   - Saves time reviewing duplicate postings

5. **Dashboard & Analytics**
   - Application pipeline visualization
   - Response rate tracking
   - Time-to-hire statistics
   - Success metrics

### 📊 Usage Limits (Free Tier)

| Feature                | Limit       | Typical Usage | More Than Enough?       |
| ---------------------- | ----------- | ------------- | ----------------------- |
| **AI Requests**        | 14,400/day  | 10-50/day     | ✅ Yes (280x your needs) |
| **Job Scraping (Web)** | Unlimited   | N/A           | ✅ Yes                   |
| **Adzuna API**         | 1,000/month | 30/day        | ✅ Yes (covers 33 days)  |
| **RapidAPI JSearch**   | 1,000/month | 30/day        | ✅ Yes (covers 33 days)  |
| **The Muse API**       | 500/hour    | 10/hour       | ✅ Yes (50x your needs)  |
| **Remotive API**       | Unlimited   | N/A           | ✅ Yes                   |
| **RemoteOK API**       | 1 req/sec   | N/A           | ✅ Yes                   |
| **Applications**       | Unlimited   | N/A           | ✅ Yes                   |
| **Storage**            | Unlimited*  | ~100MB        | ✅ Yes                   |

*Limited only by your disk space

**Combined Job Discovery Power (Free Tier)**:
- ~1,000 web scraped jobs per day
- +1,000 API jobs per month (Adzuna)
- +1,000 API jobs per month (RapidAPI)
- +12,000 API jobs per day (The Muse: 500/hour × 24)
- +Unlimited remote jobs (Remotive + RemoteOK)

**Total**: Easily 50,000+ unique job postings per month for FREE!

---

## 🚫 What's NOT Included (And Why You Don't Need It)

### Services You're Avoiding Costs For:

1. **OpenAI GPT ($)** - Groq is free and just as good for job search tasks
2. **Anthropic Claude ($)** - Groq handles all AI needs
3. **SendGrid Email ($)** - Use console logging or free Gmail SMTP
4. **Sentry Monitoring ($)** - Use Docker logs instead
5. **Indeed Publisher API (⏳)** - Requires 1-2 week approval, web scraping works
6. **LinkedIn API (🚫)** - Enterprise only, web scraping works
7. **Glassdoor API (🚫)** - Restricted partners only, web scraping works

### Optional Free Enhancements (Highly Recommended):

These are **completely optional** but 100% free and improve data quality:

#### **Job Board APIs (All Free)**
- **Adzuna** (1,000/month) - 22 countries, instant signup: https://developer.adzuna.com/signup
- **RapidAPI JSearch** (1,000/month) - Aggregates multiple sources: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
- **The Muse** (500/hour) - No API key needed: https://www.themuse.com/developers/api/v2
- **Remotive** (Unlimited) - Remote jobs, no key needed: https://remotive.com/api
- **RemoteOK** (Unlimited) - 100k+ remote jobs, no key needed: https://remoteok.com/api

#### **Other Free Services**
- **Gmail Notifications** - Use your Gmail account (free, 500 emails/day limit)
- **Slack Notifications** - Create free Slack workspace
- **Google Calendar Sync** - Free OAuth integration
- **GitHub OAuth** - Free authentication

---

## 🔧 Configuration Quick Reference

### Required in .env (3 values total):

```bash
# 1. Generate with: openssl rand -hex 32
SECRET_KEY=your-generated-key

# 2. Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-generated-key

# 3. Get FREE key from: https://console.groq.com/keys
GROQ_API_KEY=gsk_your-groq-key
```

### Optional Free APIs (Highly Recommended for Better Data):

```bash
# Get FREE Adzuna API (2 min signup, no credit card)
# Visit: https://developer.adzuna.com/signup
ADZUNA_APP_ID=your-app-id
ADZUNA_APP_KEY=your-api-key

# Get FREE RapidAPI key (2 min signup, no credit card)  
# Visit: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
RAPIDAPI_KEY=your-rapidapi-key

# Enable free public APIs (no signup needed!)
THE_MUSE_ENABLED=true
REMOTIVE_ENABLED=true
REMOTEOK_ENABLED=true
```

### Everything Else (Leave as-is):

```bash
# Database (Docker handles this)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot

# Redis (Docker handles this)
REDIS_URL=redis://localhost:6379/0

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

---

## ✅ Verification Checklist

After setup, verify your free tier configuration:

```bash
# 1. Check all services are running
docker-compose ps
# Should show: postgres, redis, backend, frontend, celery, celery-beat (all "Up")

# 2. Test backend health
curl http://localhost:8002/health
# Should return: {"status":"healthy","database":"connected","redis":"connected"}

# 3. Verify FREE Groq is enabled
docker-compose exec backend python -c "
from app.core.config import get_settings
s = get_settings()
print('✅ FREE TIER VERIFIED' if s.groq_api_key and not getattr(s, 'openai_api_key', None) else '⚠️ CHECK CONFIG')
"
# Should print: ✅ FREE TIER VERIFIED

# 4. Access frontend
open http://localhost:3000
# Should open in browser (may take 30 seconds first time)
```

All checks passed? **You're running 100% free!** 🎉

---

## 📚 Next Steps

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

## 🆘 Troubleshooting Free Tier Setup

### "Services won't start"

```bash
# Check Docker is running
docker --version

# View logs for errors
docker-compose logs backend
docker-compose logs frontend
```

### "Database connection failed"

```bash
# Wait for PostgreSQL to be ready (can take 10-30 seconds)
docker-compose logs postgres | grep "ready to accept connections"

# Restart backend after database is ready
docker-compose restart backend
```

### "Invalid API key" (Groq)

1. Verify key starts with `gsk_`
2. Check no extra spaces in `.env`
3. Regenerate key at: https://console.groq.com/keys
4. Restart services: `docker-compose restart`

### "Frontend shows blank page"

```bash
# Wait for build to complete (first time: 1-2 minutes)
docker-compose logs frontend | tail -20

# Look for: "ready - started server on 0.0.0.0:3000"
```

### "AI features not working"

```bash
# Verify Groq configuration
docker-compose exec backend python -c "
from app.services.llm_service import LLMService
service = LLMService()
print('✅ Groq working' if service.groq_client else '❌ Check GROQ_API_KEY')
"
```

---

## 💡 Pro Tips for Free Tier Users

1. **Groq's 14,400 requests/day resets at midnight UTC**
   - That's 600 requests per hour
   - You'd need to generate 600 cover letters per hour to hit the limit!

2. **Use console logging for notifications**
   - View in real-time: `docker-compose logs -f backend | grep Notification`
   - No email setup needed

3. **Job scraping runs automatically**
   - Daily at 4 AM UTC (configurable in `backend/app/core/celery_app.py`)
   - Or trigger manually in the UI

4. **Backup your data**
   - Database is in `./data/postgres/`
   - Create backups: `docker-compose exec postgres pg_dump -U postgres career_copilot > backup.sql`

5. **Monitor usage**
   - Check Groq dashboard: https://console.groq.com/usage
   - See your daily request count

---

## 🎉 You're All Set!

Your Career Copilot installation is:
- ✅ 100% free
- ✅ Fully functional
- ✅ No credit card required
- ✅ No hidden costs
- ✅ Unlimited job tracking
- ✅ 14,400 AI requests per day

**Monthly cost: $0.00** 🎊

Enjoy your job search! 🚀

---

## 📞 Need Help?

- **Documentation**: [[./LOCAL_SETUP.md|Full Setup Guide]]
- **Issues**: https://github.com/moatasim-KT/career-copilot/issues
- **Common Problems**: [[./docs/troubleshooting/COMMON_ISSUES.md]]

---

**Last Updated**: November 2025  
**Free Tier Configuration**: `.env.free-tier-example`
