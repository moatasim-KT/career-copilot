# Common Issues & Troubleshooting

## Installation Issues

### Python Version Mismatch

**Problem**: `Python 3.11+ required`

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.11 (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11

# macOS (using Homebrew)
brew install python@3.11

# Create virtual environment with specific version
python3.11 -m venv venv
```

### Dependency Installation Failures

**Problem**: `pip install` fails with errors

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails, install build dependencies
sudo apt install python3-dev build-essential  # Ubuntu/Debian
brew install gcc  # macOS
```

### Node.js/npm Issues

**Problem**: `npm install` fails or wrong Node version

**Solution**:
```bash
# Check Node version
node --version  # Should be 18.0+

# Install correct version (using nvm)
nvm install 18
nvm use 18

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## Database Issues

### PostgreSQL Connection Refused

**Problem**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@14  # macOS

# Verify connection
psql -h localhost -U postgres -c "SELECT 1;"
```

### Database Does Not Exist

**Problem**: `database "career_copilot" does not exist`

**Solution**:
```bash
# Create database
createdb career_copilot

# Or using psql
psql -U postgres -c "CREATE DATABASE career_copilot;"

# Run migrations
cd backend
alembic upgrade head
```

### Migration Conflicts

**Problem**: `Target database is not up to date`

**Solution**:
```bash
# Check migration status
alembic current

# See migration history
alembic history

# Downgrade if needed
alembic downgrade -1

# Upgrade to latest
alembic upgrade head

# If completely broken, reset (CAUTION: destroys data)
alembic downgrade base
alembic upgrade head
```

## Redis Issues

### Redis Connection Errors

**Problem**: `Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Start Redis
redis-server  # Foreground
redis-server --daemonize yes  # Background

# Check Redis logs
tail -f /var/log/redis/redis-server.log  # Linux
tail -f /usr/local/var/log/redis.log  # macOS

# Test connection with Python
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
```

### Redis Out of Memory

**Problem**: `OOM command not allowed`

**Solution**:
```bash
# Check memory usage
redis-cli INFO memory

# Clear all keys (CAUTION)
redis-cli FLUSHALL

# Increase max memory (redis.conf)
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
```

## API Issues

### 404 Not Found

**Problem**: API endpoints return 404

**Solution**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check API documentation
curl http://localhost:8000/docs

# Verify correct URL
# Correct: http://localhost:8000/api/v1/jobs
# Wrong: http://localhost:8000/jobs

# Check backend logs
docker-compose logs backend
```

### 401 Unauthorized

**Problem**: `{"detail":"Not authenticated"}`

**Solution**:
```bash
# Verify token is included
curl http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get new token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Check token expiration
# Tokens expire after 30 minutes by default
```

### 422 Validation Error

**Problem**: `{"detail":[{"loc":["body","email"],"msg":"field required"}]}`

**Solution**:
```json
// Ensure all required fields are provided
{
  "email": "user@example.com",  // Required
  "password": "password123"     // Required
}
```

### 500 Internal Server Error

**Problem**: Server returns 500 error

**Solution**:
```bash
# Check backend logs
docker-compose logs backend | tail -50

# Check database connection
psql -h localhost -U postgres -d career_copilot -c "SELECT 1;"

# Check environment variables
docker-compose exec backend env | grep DATABASE_URL

# Restart services
docker-compose restart backend
```

## Celery Issues

### Celery Workers Not Starting

**Problem**: Celery workers fail to start

**Solution**:
```bash
# Check Celery logs
docker-compose logs celery

# Verify Redis connection
redis-cli ping

# Check broker URL
echo $CELERY_BROKER_URL

# Restart Celery
docker-compose restart celery

# Start with verbose logging
celery -A app.core.celery_app worker --loglevel=debug
```

### Tasks Not Executing

**Problem**: Tasks queued but not running

**Solution**:
```bash
# Check active workers
celery -A app.core.celery_app inspect active

# Check queued tasks
celery -A app.core.celery_app inspect reserved

# Purge all tasks (CAUTION)
celery -A app.core.celery_app purge

# Check task routing
celery -A app.core.celery_app inspect registered
```

## Frontend Issues

### npm run dev Fails

**Problem**: Development server won't start

**Solution**:
```bash
# Check Node version
node --version  # Must be 18+

# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts
lsof -ti:3000 | xargs kill -9

# Start with verbose output
npm run dev -- --verbose
```

### API Connection Errors

**Problem**: Frontend can't connect to backend

**Solution**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS configuration (backend/.env)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Check frontend API URL (frontend/.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Check network in browser DevTools
# Look for CORS errors in console
```

### Build Errors

**Problem**: `npm run build` fails

**Solution**:
```bash
# Check TypeScript errors
npm run type-check

# Fix linting issues
npm run lint

# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

## Docker Issues

### Container Won't Start

**Problem**: Docker container exits immediately

**Solution**:
```bash
# Check logs
docker-compose logs [service-name]

# Check container status
docker-compose ps

# Inspect container
docker inspect [container-id]

# Try running interactively
docker-compose run --rm backend bash

# Check resources
docker stats
```

### Port Already in Use

**Problem**: `port is already allocated`

**Solution**:
```bash
# Find process using port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:5432 | xargs kill -9  # PostgreSQL
lsof -ti:6379 | xargs kill -9  # Redis

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Out of Disk Space

**Problem**: Docker runs out of space

**Solution**:
```bash
# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove specific images
docker rmi $(docker images -q)
```

## Performance Issues

### Slow API Responses

**Problem**: API requests take too long

**Solution**:
```bash
# Check database query performance
# Add EXPLAIN ANALYZE to slow queries

# Add database indexes
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

# Enable Redis caching
# Check redis hit rate
redis-cli INFO stats | grep hit_rate

# Monitor backend performance
docker stats backend
```

### High Memory Usage

**Problem**: Services consuming too much memory

**Solution**:
```bash
# Check memory usage
docker stats

# Limit container memory (docker-compose.yml)
services:
  backend:
    mem_limit: 512m
    
# Check for memory leaks
# Monitor memory over time

# Restart services
docker-compose restart
```

## AI Service Issues

### OpenAI API Errors

**Problem**: `OpenAI API key not valid`

**Solution**:
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits
# OpenAI returns 429 when rate limited

# Use fallback provider (Anthropic)
ANTHROPIC_API_KEY=sk-ant-...
```

### Resume Generation Fails

**Problem**: AI resume generation returns errors

**Solution**:
```bash
# Check logs
docker-compose logs backend | grep "resume"

# Verify user profile data
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Check AI provider configuration
cat config/llm_config.json

# Test with simple request
curl -X POST http://localhost:8000/api/v1/ai/resume/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"job_id": 1}'
```

## Job Scraping Issues

### Scrapers Not Running

**Problem**: Job scrapers don't execute

**Solution**:
```bash
# Check Celery beat is running
docker-compose ps celery-beat

# Check scheduled tasks
celery -A app.core.celery_app inspect scheduled

# Manually trigger scraping
curl -X POST http://localhost:8000/api/v1/scraping/trigger \
  -H "Authorization: Bearer $TOKEN"

# Check scraper logs
docker-compose logs celery | grep "scraping"
```

### Scraping Returns No Results

**Problem**: Scrapers run but find no jobs

**Solution**:
```bash
# Check scraper configuration
cat config/application.yaml

# Verify internet connectivity
ping linkedin.com

# Check for IP blocking
# Use proxies if needed

# Increase timeout
# Edit config/application.yaml
scraping:
  timeout_seconds: 60

# Test specific scraper
python -c "from app.services.scrapers.linkedin_scraper import LinkedInScraper; scraper = LinkedInScraper(); print(scraper.scrape())"
```

## Security Issues

### CORS Errors

**Problem**: `Access-Control-Allow-Origin` errors

**Solution**:
```bash
# Add frontend URL to ALLOWED_ORIGINS (backend/.env)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Check CORS middleware configuration
# backend/app/main.py

# Restart backend
docker-compose restart backend
```

### SSL Certificate Errors

**Problem**: HTTPS not working

**Solution**:
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect career-copilot.com:443

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

## Getting Help

If none of these solutions work:

1. **Check logs**: Always start with logs
   ```bash
   docker-compose logs -f
   ```

2. **Enable debug mode**:
   ```env
   DEBUG=True
   LOG_LEVEL=DEBUG
   ```

3. **Search GitHub issues**: [GitHub Issues](https://github.com/moatasim-KT/career-copilot/issues)

4. **Ask for help**:
   - Email: <moatasimfarooque@gmail.com>
   - Open a new issue with:
     - Error message
     - Steps to reproduce
     - Environment details
     - Relevant logs

## Diagnostic Commands

```bash
# Full system check
./scripts/verify_deployment.py

# Check all services
docker-compose ps

# Check logs
docker-compose logs --tail=100

# Check resource usage
docker stats

# Check network
docker network ls
docker network inspect career-copilot_default

# Check volumes
docker volume ls
docker volume inspect career-copilot_postgres-data

# Test database
docker-compose exec postgres psql -U postgres -d career_copilot -c "\dt"

# Test Redis
docker-compose exec redis redis-cli ping

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

## Next Steps

- [Installation Guide](../setup/INSTALLATION.md) - Fresh installation
- [Configuration Guide](../setup/CONFIGURATION.md) - Configuration help
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Production deployment
- [API Documentation](../api/API.md) - API reference
