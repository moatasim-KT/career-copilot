# Configuration Guide

## Environment Variables

### Backend (.env)

Create `backend/.env` from template:

```bash
cp backend/.env.example backend/.env
```

#### Required Variables

```env
# Application
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=career_copilot
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# AI Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Default User (Single-User Mode)
DEFAULT_USER_ID=1
```

#### Optional Variables

```env
# Email Configuration (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Job Scraping Configuration
SCRAPING_INTERVAL_HOURS=24
MAX_JOBS_PER_SOURCE=100

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=data/logs/backend/app.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Session Configuration
SESSION_TIMEOUT_MINUTES=30
```

### Frontend (.env.local)

Create `frontend/.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true

# Environment
NODE_ENV=development
```

## Database Configuration

### PostgreSQL Setup

#### Local Development

```sql
-- Create database
CREATE DATABASE career_copilot;

-- Create user (optional)
CREATE USER career_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE career_copilot TO career_user;
```

#### Connection String Format

```
postgresql://[user]:[password]@[host]:[port]/[database]
```

Examples:
- Local: `postgresql://postgres:postgres@localhost:5432/career_copilot`
- Docker: `postgresql://postgres:postgres@postgres:5432/career_copilot`
- Production: `postgresql://user:pass@db.example.com:5432/career_copilot`

### Redis Configuration

#### Local Development

```bash
# Start Redis with persistence
redis-server --appendonly yes

# Start Redis with custom port
redis-server --port 6380
```

#### Connection String Format

```
redis://[host]:[port]/[db_number]
```

Examples:
- Local: `redis://localhost:6379/0`
- Docker: `redis://redis:6379/0`
- Production: `redis://redis.example.com:6379/0`

## AI Provider Configuration

### OpenAI

Required for resume generation and job analysis.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # or gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

Get your API key: https://platform.openai.com/api-keys

### Anthropic Claude

Optional, for enhanced content analysis.

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=2000
```

Get your API key: https://console.anthropic.com/

### Configuration Priority

The system uses this priority order:
1. OpenAI (if API key provided)
2. Anthropic (if OpenAI unavailable)
3. Error if no provider configured

## Service Configuration Files

### LLM Configuration (config/llm_config.json)

```json
{
  "providers": {
    "openai": {
      "model": "gpt-4o-mini",
      "temperature": 0.7,
      "max_tokens": 2000,
      "enabled": true
    },
    "anthropic": {
      "model": "claude-3-5-sonnet-20241022",
      "temperature": 0.7,
      "max_tokens": 2000,
      "enabled": true
    }
  },
  "fallback_order": ["openai", "anthropic"],
  "retry_attempts": 3,
  "timeout_seconds": 30
}
```

### Feature Flags (config/feature_flags.json)

```json
{
  "job_scraping": true,
  "ai_resume_generation": true,
  "email_notifications": false,
  "analytics_tracking": true,
  "job_recommendations": true,
  "application_tracking": true,
  "career_resources": true
}
```

### Application Config (config/application.yaml)

```yaml
application:
  name: "Career Copilot"
  version: "1.0.0"
  environment: "development"
  
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  
redis:
  max_connections: 50
  socket_timeout: 5
  
celery:
  worker_concurrency: 4
  task_soft_time_limit: 300
  task_hard_time_limit: 600
  
scraping:
  interval_hours: 24
  max_jobs_per_source: 100
  timeout_seconds: 30
```

## Docker Configuration

### docker-compose.yml

Main configuration for all services:

```yaml
services:
  postgres:
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-career_copilot}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    
  redis:
    command: redis-server --appendonly yes
    
  backend:
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/career_copilot
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
```

### Environment-Specific Overrides

**Development** (`docker-compose.override.yml`):
```yaml
services:
  backend:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
```

**Production** (`docker-compose.prod.yml`):
```yaml
services:
  backend:
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
    restart: always
```

## Security Configuration

### Secret Key Generation

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### CORS Configuration

```env
# Development (permissive)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Production (strict)
ALLOWED_ORIGINS=https://career-copilot.com,https://api.career-copilot.com
```

### SSL/TLS (Production)

```env
# Enable HTTPS
FORCE_HTTPS=true
SSL_CERT_FILE=/path/to/cert.pem
SSL_KEY_FILE=/path/to/key.pem
```

## Logging Configuration

### Log Levels

```env
# Development
LOG_LEVEL=DEBUG

# Production
LOG_LEVEL=INFO
```

### Log Files

```env
# Backend logs
LOG_FILE=data/logs/backend/app.log
ERROR_LOG_FILE=data/logs/backend/error.log

# Celery logs
CELERY_LOG_FILE=data/logs/celery/worker.log

# Frontend logs
NEXT_LOG_FILE=data/logs/frontend/next.log
```

## Performance Tuning

### Database Connection Pool

```env
# For high traffic
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# For low traffic
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Redis Connection Pool

```env
# For high traffic
REDIS_MAX_CONNECTIONS=100

# For low traffic
REDIS_MAX_CONNECTIONS=20
```

### Celery Workers

```env
# Number of worker processes
CELERY_WORKER_CONCURRENCY=4

# Task time limits (seconds)
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_HARD_TIME_LIMIT=600
```

## Validation

### Check Configuration

```bash
# Backend
cd backend
python -c "from app.core.config import settings; print(settings.dict())"

# Frontend
cd frontend
npm run check-env
```

### Test Connections

```bash
# Test database connection
psql -h localhost -U postgres -d career_copilot -c "SELECT 1;"

# Test Redis connection
redis-cli ping

# Test API endpoints
curl http://localhost:8000/health
```

## Next Steps

- [Installation Guide](INSTALLATION.md) - Complete setup
- [Development Guide](../development/DEVELOPMENT.md) - Start developing
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Deploy to production
- [Security Guide](SECURITY.md) - Secure your installation

## Support

For configuration issues:
- Check [Troubleshooting Guide](../troubleshooting/COMMON_ISSUES.md)
- Review [Environment Examples](.env.example)
- Open an issue on [GitHub](https://github.com/moatasim-KT/career-copilot/issues)
