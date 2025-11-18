# 🆓 Free Job Board APIs Setup Guide

**Quick setup guide for enabling 5 FREE job board APIs** - No credit card required, 4 minutes total setup time!

---

## Why Use These APIs?

While Career Copilot's web scraping works great, these FREE APIs provide:
- ✅ Better data quality and consistency
- ✅ Faster job discovery
- ✅ More reliable access (no rate limiting issues)
- ✅ Structured data (easier to parse)
- ✅ 50,000+ jobs/month instead of 30,000

**Cost: $0.00/month** | **Setup time: ~4 minutes**

---

## 📋 Setup Checklist

- [ ] Adzuna API (2 min) - 1,000 calls/month, 22 countries
- [ ] RapidAPI JSearch (2 min) - 1,000 requests/month, aggregates multiple sources
- [ ] The Muse (0 min) - 500/hour, no signup needed
- [ ] Remotive (0 min) - Unlimited remote jobs, no signup needed
- [ ] RemoteOK (0 min) - Unlimited, no signup needed

---

## 1. Adzuna API (2 minutes)

**Coverage**: 22 countries including UK, US, DE, FR, NL, BE, AT, CH  
**Limit**: 1,000 calls/month (free tier)  
**Credit Card**: NO

### Setup Steps:

1. **Sign up**: https://developer.adzuna.com/signup
   - Enter email and password
   - Confirm email (check inbox)

2. **Get API credentials**:
   - Log in to developer dashboard
   - You'll see your **App ID** and **API Key** immediately
   - Copy both values

3. **Add to `.env`**:
   ```bash
   ADZUNA_APP_ID=your-app-id-here
   ADZUNA_APP_KEY=your-api-key-here
   ```

4. **Restart services**:
   ```bash
   docker-compose restart backend celery
   ```

### Example API Response:
```json
{
  "title": "Senior Python Developer",
  "company": "Tech Company GmbH",
  "location": "Berlin, Germany",
  "salary_min": 70000,
  "salary_max": 90000,
  "description": "...",
  "url": "https://..."
}
```

### Documentation:
- API Docs: https://developer.adzuna.com/docs/search
- Coverage: https://developer.adzuna.com/coverage

---

## 2. RapidAPI JSearch (2 minutes)

**Coverage**: Aggregates Google Jobs, LinkedIn, Indeed, Glassdoor  
**Limit**: 1,000 requests/month (free tier)  
**Credit Card**: NO (for free tier)

### Setup Steps:

1. **Sign up for RapidAPI**: https://rapidapi.com/auth/sign-up
   - Create account with email or Google
   - No credit card required for free tier

2. **Subscribe to JSearch**:
   - Go to: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
   - Click **"Subscribe to Test"**
   - Select **"Basic" plan (FREE)**
   - Click **"Subscribe"**

3. **Get API Key**:
   - Click **"Code Snippets"** or **"Test Endpoint"**
   - Copy your **X-RapidAPI-Key** from the headers
   - It starts with something like: `1234567890abcdef...`

4. **Add to `.env`**:
   ```bash
   RAPIDAPI_KEY=your-rapidapi-key-here
   ```

5. **Restart services**:
   ```bash
   docker-compose restart backend celery
   ```

### Example API Response:
```json
{
  "job_title": "Data Scientist",
  "employer_name": "Amazon",
  "job_city": "Munich",
  "job_country": "DE",
  "job_apply_link": "https://...",
  "job_description": "..."
}
```

### Documentation:
- API Docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
- Endpoints: `/search`, `/job-details`, `/estimated-salary`

---

## 3. The Muse API (0 minutes - No Signup!)

**Coverage**: Curated jobs from top companies, strong company culture focus  
**Limit**: 500 requests/hour (no monthly cap)  
**Credit Card**: NO  
**API Key**: NOT NEEDED!

### Setup Steps:

1. **Add to `.env`**:
   ```bash
   THE_MUSE_ENABLED=true
   ```

2. **Restart services**:
   ```bash
   docker-compose restart backend celery
   ```

That's it! The API is public and requires no authentication.

### Example API Response:
```json
{
  "name": "Software Engineer",
  "company": {
    "name": "Spotify"
  },
  "locations": [
    {"name": "Berlin, Germany"}
  ],
  "contents": "...",
  "publication_date": "2025-11-15T00:00:00Z"
}
```

### Documentation:
- API Docs: https://www.themuse.com/developers/api/v2
- Company Culture: https://www.themuse.com/advice/company-culture

---

## 4. Remotive API (0 minutes - No Signup!)

**Coverage**: Remote jobs only (perfect for EU remote work)  
**Limit**: Unlimited  
**Credit Card**: NO  
**API Key**: NOT NEEDED!

### Setup Steps:

1. **Add to `.env`**:
   ```bash
   REMOTIVE_ENABLED=true
   ```

2. **Restart services**:
   ```bash
   docker-compose restart backend celery
   ```

That's it! Public API with no rate limits.

### Example API Response:
```json
{
  "title": "Senior Backend Engineer",
  "company_name": "GitLab",
  "job_type": "full-time",
  "candidate_required_location": "Europe",
  "salary": "€80,000 - €120,000",
  "url": "https://..."
}
```

### Documentation:
- API Docs: https://remotive.com/api
- Job Categories: Tech, Marketing, Customer Support, Sales, etc.

---

## 5. RemoteOK API (0 minutes - No Signup!)

**Coverage**: 100,000+ remote jobs worldwide  
**Limit**: 1 request per second (rate limit)  
**Credit Card**: NO  
**API Key**: NOT NEEDED!

### Setup Steps:

1. **Add to `.env`**:
   ```bash
   REMOTEOK_ENABLED=true
   ```

2. **Restart services**:
   ```bash
   docker-compose restart backend celery
   ```

That's it! Public API with minimal rate limiting.

### Example API Response:
```json
{
  "position": "Full Stack Developer",
  "company": "Buffer",
  "location": "Worldwide",
  "tags": ["javascript", "react", "node"],
  "date": "Nov 15, 2025",
  "url": "https://..."
}
```

### Documentation:
- API Docs: https://remoteok.com/api
- Rate Limit: 1 request/second (just sleep 1 second between calls)

---

## ✅ Verification

After setup, verify all APIs are working:

```bash
# Test API configuration
docker-compose exec backend python -c "
from app.core.config import get_settings
settings = get_settings()

print('=== FREE API CONFIGURATION ===')
print(f'✅ Adzuna: {bool(getattr(settings, \"adzuna_app_id\", None))}')
print(f'✅ RapidAPI: {bool(getattr(settings, \"rapidapi_key\", None))}')
print(f'✅ The Muse: {bool(getattr(settings, \"the_muse_enabled\", False))}')
print(f'✅ Remotive: {bool(getattr(settings, \"remotive_enabled\", False))}')
print(f'✅ RemoteOK: {bool(getattr(settings, \"remoteok_enabled\", False))}')
"
```

Expected output:
```
=== FREE API CONFIGURATION ===
✅ Adzuna: True
✅ RapidAPI: True
✅ The Muse: True
✅ Remotive: True
✅ RemoteOK: True
```

### Test Job Discovery

Trigger a manual job scraping run to test all APIs:

```bash
# Trigger job scraping
docker-compose exec celery python -c "
from app.tasks.job_ingestion_tasks import ingest_jobs
result = ingest_jobs.delay([1])  # Replace 1 with your user ID
print(f'Task started: {result.id}')
"

# Check Celery logs
docker-compose logs -f celery | grep "Job"
```

You should see log messages indicating jobs are being fetched from all enabled sources.

---

## 📊 Usage Statistics

After enabling all free APIs, you'll have access to:

| Source           | Jobs/Day    | Jobs/Month   | Credit Card? | Signup Time |
| ---------------- | ----------- | ------------ | ------------ | ----------- |
| **Web Scraping** | ~1,000      | ~30,000      | NO           | 0 min       |
| **Adzuna**       | ~33         | ~1,000       | NO           | 2 min       |
| **RapidAPI**     | ~33         | ~1,000       | NO           | 2 min       |
| **The Muse**     | ~12,000     | ~360,000     | NO           | 0 min       |
| **Remotive**     | ~50         | ~1,500       | NO           | 0 min       |
| **RemoteOK**     | ~100        | ~3,000       | NO           | 0 min       |
| **TOTAL**        | **~13,216** | **~396,500** | **NO**       | **4 min**   |

After deduplication: **~50,000 unique jobs/month**

---

## 🔧 Troubleshooting

### "Invalid API credentials" (Adzuna)

1. Check `.env` for typos
2. Ensure no extra spaces around keys
3. Verify App ID and API Key are correct in dashboard
4. Restart services: `docker-compose restart backend celery`

### "Rate limit exceeded" (RapidAPI)

1. Check usage dashboard: https://rapidapi.com/developer/billing
2. Free tier: 1,000 requests/month
3. Upgrade to Pro if needed (paid)
4. Or reduce scraping frequency

### "Connection timeout" (The Muse, Remotive, RemoteOK)

1. These are public APIs, no authentication issues
2. Check internet connection
3. Try again later (might be temporary downtime)
4. Check API status pages

### "No jobs found from API X"

1. Check Celery logs: `docker-compose logs celery | grep "API_NAME"`
2. Verify API is enabled in `.env`
3. Check if service is configured in `backend/app/services/scraping/`
4. Some APIs may have country/region restrictions

---

## 🚀 Next Steps

1. **Monitor API usage**: Check dashboards for Adzuna and RapidAPI
2. **Adjust scraping frequency**: In `backend/app/core/celery_app.py`
3. **Add custom filters**: Configure in `backend/app/services/job_service.py`
4. **Set up notifications**: Get alerts when new jobs match your criteria

---

## 📚 Additional Resources

- [[../LOCAL_SETUP.md|Local Setup Guide]] - Complete setup documentation
- [[../../FREE_TIER_SETUP.md|Free Tier Setup]] - Zero-cost deployment guide
- [[../../backend/app/services/scraping/README.md|Scraping Service Docs]] - Scraper architecture
- [[../../config/feature_flags.json|Feature Flags]] - Enable/disable scrapers

---

**Questions or issues?** Check [[../troubleshooting/COMMON_ISSUES.md|Common Issues]] or open a GitHub issue.
