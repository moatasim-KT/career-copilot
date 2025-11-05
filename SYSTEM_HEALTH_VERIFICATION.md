# System Health Verification Guide

## Overview

This document provides a comprehensive guide to verifying that all critical components of the Career Copilot system are operational:

1. **Scheduler** - Celery Beat for automated task execution
2. **Notification System** - Email delivery for briefings and alerts
3. **Resume Parsing** - PDF/DOCX parsing with skill extraction
4. **Dashboard Progress** - Daily goal tracking and progress bars

---

## 1. Scheduler System

### Components

The application uses **Celery Beat** for task scheduling with **Redis** as the message broker.

### Scheduled Tasks

| Task Name | Schedule | Description |
|-----------|----------|-------------|
| `ingest-jobs-daily` | 4:00 AM daily | Scrape new jobs from all sources |
| `send_morning_briefing` | 8:00 AM daily | Send personalized morning briefings |
| `send_evening_summary` | 8:00 PM daily | Send daily progress summaries |
| `process-jobs-periodic` | Every 3 hours | Process job queue and enrichment |
| `analyze-skills-weekly` | Weekly | Analyze skill trends |

### Verification Steps

#### Check Scheduler Status

```bash
# Run the system health check
python backend/scripts/verify_system_health.py
```

#### Manual Checks

```bash
# Check if Celery Beat is running
pgrep -f "celery.*beat"

# Check if Celery Worker is running
pgrep -f "celery.*worker"

# Check Redis connection
redis-cli ping
```

#### Start Scheduler (if not running)

```bash
# Terminal 1: Start Celery Worker
celery -A app.celery worker --loglevel=info

# Terminal 2: Start Celery Beat
celery -A app.celery beat --loglevel=info
```

### Configuration Files

- **Main Config**: `backend/app/celery.py`
- **Beat Schedule**: `backend/app/core/celeryconfig.py`
- **Tasks Location**:
  - `backend/app/tasks/email_tasks.py`
  - `backend/app/tasks/notification_tasks.py`
  - `backend/app/tasks/job_ingestion_tasks.py`

### Troubleshooting

**Problem**: Celery Beat not running
```bash
# Solution: Start Celery Beat
celery -A app.celery beat --loglevel=info --pidfile=/tmp/celerybeat.pid
```

**Problem**: Tasks not executing
```bash
# Check Celery worker logs
celery -A app.celery worker --loglevel=debug

# Check Redis connection
redis-cli ping

# Verify beat schedule is loaded
python -c "from app.celery import celery_app; print(celery_app.conf.beat_schedule)"
```

---

## 2. Notification System

### Components

- **NotificationService** - Core email sending service
- **EmailTemplateManager** - Template rendering and queuing
- **Celery Tasks** - Async email delivery

### Email Types

1. **Morning Briefings** (8 AM)
   - Daily job recommendations
   - Progress updates
   - Market insights

2. **Evening Summaries** (8 PM)
   - Applications sent today
   - Goals achievement
   - Tomorrow's plan

3. **Job Alerts**
   - New matching jobs
   - Application confirmations
   - Interview reminders

4. **Milestones**
   - Achievement celebrations
   - Streak notifications

### Verification Steps

#### Run System Health Check

```bash
python backend/scripts/verify_system_health.py
```

#### Send Test Email

```bash
# Simple test email
python backend/scripts/test_email_notification.py --email your@email.com --type simple

# Job alert test email
python backend/scripts/test_email_notification.py --email your@email.com --type job_alert
```

### Configuration

Required environment variables in `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@careercopilot.com
```

**For Gmail**: Generate an App Password at https://myaccount.google.com/apppasswords

### Email Templates Location

All templates are in: `backend/app/templates/email/`

- `morning_briefing.html`
- `evening_summary.html`
- `application_confirmation.html`
- `application_milestone.html`
- `job_alert.html`

### Troubleshooting

**Problem**: Emails not sending
```bash
# Check SMTP configuration
python -c "import os; print('SMTP_USER:', os.getenv('SMTP_USER')); print('SMTP_HOST:', os.getenv('SMTP_HOST'))"

# Test SMTP connection
python -c "import smtplib; s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); print('SMTP OK')"
```

**Problem**: Templates not rendering
```bash
# Check template directory exists
ls -la backend/app/templates/email/

# Test template loading
python -c "from pathlib import Path; from jinja2 import Template; t = Path('backend/app/templates/email/morning_briefing.html').read_text(); print('Template OK')"
```

---

## 3. Resume Parsing

### Components

- **ResumeParserService** - Docling-based parsing
- **Resume API Endpoints** - Upload and status checking
- **Async Tasks** - Background parsing with Celery

### Supported Formats

- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Markdown (.md)
- Plain text (.txt)

### Extracted Data

1. **Contact Information**
   - Name, email, phone
   - LinkedIn, GitHub profiles

2. **Skills**
   - Technical skills
   - Soft skills
   - Technologies

3. **Experience**
   - Job titles, companies
   - Dates, locations
   - Responsibilities

4. **Education**
   - Degrees, institutions
   - Graduation dates, GPAs

5. **Certifications**

### Verification Steps

#### Run System Health Check

```bash
python backend/scripts/verify_system_health.py
```

#### Check Docling Installation

```bash
# Verify Docling is installed
python -c "import docling; print('Docling version:', docling.__version__)"

# If not installed:
pip install docling
```

#### Test Resume Parsing (via API)

```bash
# Upload a resume
curl -X POST "http://localhost:8000/api/v1/resume/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/resume.pdf"

# Get parsing status
curl -X GET "http://localhost:8000/api/v1/resume/{upload_id}/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get profile suggestions
curl -X GET "http://localhost:8000/api/v1/resume/{upload_id}/suggestions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### API Endpoints

- `POST /api/v1/resume/upload` - Upload resume file
- `GET /api/v1/resume/{upload_id}/status` - Check parsing status
- `GET /api/v1/resume/{upload_id}/suggestions` - Get profile update suggestions
- `POST /api/v1/resume/parse-job-description` - Parse job description

### Database Schema

Table: `resume_uploads`

```sql
- id (primary key)
- user_id (foreign key)
- filename, file_path, file_size, file_type
- parsing_status (pending, processing, completed, failed)
- parsed_data (JSON)
- extracted_skills (JSON array)
- extracted_experience (string)
- extracted_contact_info (JSON)
- parsing_error (text)
- created_at, updated_at
```

### Troubleshooting

**Problem**: Docling not installed
```bash
pip install docling
```

**Problem**: Parsing fails
```bash
# Check file size (max 10MB)
ls -lh uploads/resume.pdf

# Check file is readable
file uploads/resume.pdf

# Check logs
tail -f logs/backend/app.log | grep -i resume
```

**Problem**: Uploads directory missing
```bash
mkdir -p backend/uploads
chmod 755 backend/uploads
```

---

## 4. Dashboard Progress Tracking

### Components

- **AnalyticsService** - Calculate metrics and progress
- **DashboardService** - Real-time updates
- **GoalService** - Goal tracking and milestones
- **Frontend Dashboard** - Progress visualization

### Tracked Metrics

#### Daily Metrics
- Applications sent today
- Daily goal (default: 10 applications)
- Progress percentage
- Goal achievement status

#### Weekly Metrics
- Total applications this week
- Response rate
- Interviews scheduled
- Streak days

#### Monthly Metrics
- Total applications
- Acceptance rate
- Top skills in applied jobs
- Top companies

### Verification Steps

#### Run System Health Check

```bash
python backend/scripts/verify_system_health.py
```

#### Check Analytics API

```bash
# Get analytics summary
curl -X GET "http://localhost:8000/api/v1/analytics/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Expected Response

```json
{
  "total_jobs": 150,
  "total_applications": 45,
  "pending_applications": 30,
  "interviews_scheduled": 3,
  "offers_received": 1,
  "rejections_received": 5,
  "acceptance_rate": 2.2,
  "daily_applications_today": 3,
  "weekly_applications": 12,
  "monthly_applications": 45,
  "daily_application_goal": 10,
  "daily_goal_progress": 30.0,
  "top_skills_in_jobs": [...],
  "top_companies_applied": [...],
  "application_status_breakdown": {...}
}
```

### Dashboard Components

#### Frontend Location
`frontend/src/components/pages/Dashboard.tsx`

#### Key Features

1. **Progress Bar**
   - Visual representation of daily goal
   - Color-coded (red < 50%, yellow 50-80%, green > 80%)
   - Real-time updates

2. **Statistics Cards**
   - Total jobs, applications
   - Interviews, offers
   - Acceptance rate

3. **Recent Activity**
   - Last 5 applications
   - Status indicators
   - Quick navigation

4. **Status Breakdown**
   - Applications by status
   - Visual icons for each status

### Setting Daily Goals

#### Via API

```bash
curl -X PATCH "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"daily_application_goal": 15}'
```

#### Via Database

```sql
UPDATE users 
SET daily_application_goal = 15 
WHERE id = 1;
```

### Goal Service

Advanced goal tracking available via `GoalService`:

```python
from app.services.goal_service import GoalService

goal_service = GoalService(db)

# Create a goal
goal = goal_service.create_goal(
    user_id=1,
    goal_data={
        "goal_type": "daily_applications",
        "target_value": 10,
        "target_date": "2024-12-31"
    }
)

# Get dashboard
dashboard = goal_service.get_goal_dashboard(user_id=1)
```

### Troubleshooting

**Problem**: Progress not updating
```bash
# Check analytics service
python -c "from app.services.analytics_service import AnalyticsService; from app.core.database import SessionLocal; db = SessionLocal(); service = AnalyticsService(db); print('Service OK')"

# Clear cache (if implemented)
redis-cli FLUSHDB
```

**Problem**: Daily goal not showing
```bash
# Check user's daily goal setting
python -c "from app.models.user import User; from app.core.database import SessionLocal; db = SessionLocal(); user = db.query(User).first(); print('Goal:', user.daily_application_goal)"

# Set default goal
python -c "from app.models.user import User; from app.core.database import SessionLocal; db = SessionLocal(); user = db.query(User).first(); user.daily_application_goal = 10; db.commit(); print('Goal set to 10')"
```

---

## Quick Verification Checklist

### Before Production Deployment

- [ ] **Scheduler Running**
  - Celery Beat process active
  - Celery Worker process active
  - Redis connection successful
  - Beat schedule configured

- [ ] **Notifications Working**
  - SMTP credentials configured
  - Test email sent successfully
  - Templates rendering correctly
  - Email tasks registered

- [ ] **Resume Parsing Operational**
  - Docling installed
  - ResumeParserService initialized
  - Upload endpoint working
  - Parsing status endpoint working

- [ ] **Dashboard Progress Tracking**
  - Analytics service functional
  - Daily goal calculation working
  - Progress bar displaying
  - Real-time updates working

### Automated Verification

Run the comprehensive health check:

```bash
python backend/scripts/verify_system_health.py
```

Expected output:
```
✅ SCHEDULER: OPERATIONAL
✅ NOTIFICATIONS: OPERATIONAL
✅ RESUME PARSING: OPERATIONAL
✅ DASHBOARD: OPERATIONAL

🎉 All 4 system components are operational!
```

---

## Monitoring Commands

### Check All Services Status

```bash
# Celery processes
ps aux | grep celery

# Redis
redis-cli ping

# Backend API
curl http://localhost:8000/health

# Database
psql -U postgres -d career_copilot -c "SELECT COUNT(*) FROM users;"
```

### View Logs

```bash
# Backend logs
tail -f logs/backend/app.log

# Celery worker logs
tail -f logs/celery/worker.log

# Celery beat logs
tail -f logs/celery/beat.log

# Email logs
tail -f logs/backend/app.log | grep -i email
```

### Real-time Monitoring

```bash
# Celery task monitoring
celery -A app.celery inspect active

# Scheduled tasks
celery -A app.celery inspect scheduled

# Redis monitoring
redis-cli monitor
```

---

## Production Deployment

### Environment Variables

Ensure all required variables are set:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/career_copilot

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your_secret_key
```

### Start All Services

```bash
# 1. Start Redis
redis-server

# 2. Start PostgreSQL
pg_ctl start

# 3. Start Backend API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Start Celery Worker
celery -A app.celery worker --loglevel=info

# 5. Start Celery Beat
celery -A app.celery beat --loglevel=info

# 6. Start Frontend (development)
cd frontend && npm run dev
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## Support & Debugging

### Common Issues

1. **Emails not sending**
   - Check SMTP credentials
   - Verify firewall/network settings
   - Test with `test_email_notification.py`

2. **Scheduler not running**
   - Ensure Redis is running
   - Check Celery Beat logs
   - Verify beat schedule configuration

3. **Resume parsing fails**
   - Install Docling: `pip install docling`
   - Check file size limits
   - Verify file format support

4. **Dashboard not updating**
   - Clear browser cache
   - Check API connectivity
   - Verify analytics calculation

### Getting Help

- Check logs in `logs/` directory
- Run `verify_system_health.py` for diagnostics
- Review error messages in Celery logs
- Test individual components with provided scripts

---

## Conclusion

All four critical systems are now fully documented and verifiable:

1. ✅ **Scheduler** - Automated task execution with Celery Beat
2. ✅ **Notifications** - Email delivery for engagement
3. ✅ **Resume Parsing** - Intelligent skill extraction
4. ✅ **Dashboard Progress** - Real-time goal tracking

Run `python backend/scripts/verify_system_health.py` to confirm all systems are operational.
