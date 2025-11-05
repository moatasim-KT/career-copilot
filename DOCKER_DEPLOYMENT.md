# 🐳 Career Copilot - Complete Docker Deployment Setup

## ✅ What Was Created

### Docker Compose Files
1. **`docker-compose.yml`** - Production deployment
   - Full stack: Backend, Frontend, PostgreSQL, Redis, Celery, Nginx
   - Monitoring: Prometheus, Grafana, Alertmanager
   - Multi-container orchestration with health checks
   - Volume persistence for data

2. **`docker-compose.dev.yml`** - Development environment
   - Lightweight setup for local development
   - Hot-reload enabled for backend
   - Minimal monitoring (Prometheus + Grafana)
   - Faster startup times

### Dockerfiles
1. **`deployment/docker/Dockerfile.backend`**
   - Multi-stage build (base → development → production)
   - Python 3.11 with FastAPI
   - Gunicorn for production (4 workers)
   - Uvicorn for development (hot-reload)

2. **`deployment/docker/Dockerfile.frontend`**
   - Multi-stage build (deps → builder → runner)
   - Node.js 18 with Next.js 14
   - Optimized production build
   - Non-root user for security

### Configuration Files
1. **`deployment/nginx/nginx.conf`**
   - Reverse proxy for all services
   - SSL/TLS configuration
   - Rate limiting (API: 10 req/s, General: 100 req/s)
   - WebSocket support
   - Protected monitoring endpoints (basic auth)
   - Security headers

2. **`.env.example`**
   - Complete environment variable template
   - Database, Redis, JWT configuration
   - AI API keys (OpenAI, Anthropic, Groq, Google)
   - Email/SMS settings
   - Monitoring credentials

3. **`monitoring/prometheus/prometheus.yml`** & **`prometheus-dev.yml`**
   - Updated to use correct ports (backend:8002, frontend:3000)
   - Scrape configs for all services
   - Alert rules integration

### Helper Scripts
1. **`deploy.sh`**
   - Interactive deployment wizard
   - Environment selection (dev/prod)
   - SSL certificate generation
   - Service health check

2. **`deployment/docker/README.md`**
   - Complete deployment guide
   - Troubleshooting section
   - Common operations
   - Security checklist

### Cleanup
✅ **Removed unused monitoring tools:**
- ❌ Elasticsearch (replaced by Prometheus)
- ❌ Kibana (replaced by Grafana)
- ❌ Logstash (not needed)
- ❌ Loki (log aggregation - overkill for now)
- ❌ Promtail (log shipping - not needed)

✅ **Kept essential monitoring:**
- ✅ Prometheus (metrics collection & storage)
- ✅ Grafana (visualization with pre-built dashboards)
- ✅ Alertmanager (alert routing & notifications)

---

## 🚀 Quick Start

### 1. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your values
nano .env  # or vim, code, etc.
```

**Required variables to set:**
- `POSTGRES_PASSWORD` - Secure database password
- `REDIS_PASSWORD` - Secure Redis password
- `SECRET_KEY` - Application secret (32+ chars)
- `JWT_SECRET_KEY` - JWT signing key
- `OPENAI_API_KEY` - For AI features
- `GRAFANA_PASSWORD` - Grafana admin password

### 2. Run Deployment Script
```bash
# Use the interactive script
./deploy.sh

# Or manually:
# For development
docker-compose -f docker-compose.dev.yml up -d

# For production
docker-compose up -d --build
```

### 3. Access Services

**Development:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8002
- API Docs: http://localhost:8002/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

**Production (via Nginx):**
- Application: https://your-domain.com
- API: https://your-domain.com/api/
- Prometheus: https://your-domain.com/prometheus/ (basic auth required)
- Grafana: https://your-domain.com/grafana/ (basic auth required)

---

## 📊 Monitoring Stack Details

### What You Get

1. **Prometheus** (Port 9090)
   - Collects metrics from `/metrics` endpoint every 10-15s
   - Stores 30 days of data (dev: 7 days)
   - Tracks: HTTP requests, response times, errors, AI costs, job scraping
   - Alert rules for high error rates, slow responses

2. **Grafana** (Port 3001)
   - Pre-configured dashboards:
     - Business Analytics
     - Infrastructure Monitoring
     - Production System Overview
   - Auto-connected to Prometheus
   - Visualizes all backend metrics

3. **Alertmanager** (Port 9093)
   - Routes alerts from Prometheus
   - Configurable notifications (email, Slack, SMS)
   - Alert grouping and silencing

### Metrics Available

Your backend already exports 50+ metrics:

**HTTP Metrics:**
- `http_requests_total` - Total requests by method/endpoint/status
- `http_request_duration_seconds` - Response time histogram
- `http_requests_in_progress` - Active requests

**AI Metrics:**
- `ai_generation_total` - AI content generations
- `ai_tokens_used_total` - Token usage by provider/model
- `ai_cost_total` - Costs in USD
- `ai_generation_duration_seconds` - AI response times

**Job Scraping:**
- `job_scraper_success_total` - Successful scrapes
- `job_scraper_errors_total` - Scraper errors
- `jobs_scraped_total` - Total jobs found

**Database:**
- `db_query_duration_seconds` - Query performance
- `db_connection_pool_size` - Connection pool metrics

**Cache:**
- `cache_hits_total` / `cache_misses_total` - Redis performance

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx (80/443)                      │
│              Reverse Proxy + Load Balancer             │
└─────────────┬───────────────────────────────────────────┘
              │
         ┌────┴────┐
         │         │
    ┌────▼─────┐ ┌▼─────────┐
    │ Frontend │ │ Backend  │
    │ Next.js  │ │ FastAPI  │
    │  :3000   │ │  :8002   │
    └──────────┘ └─┬────┬───┘
                   │    │
         ┌─────────┘    └──────────┐
         │                         │
    ┌────▼─────┐            ┌──────▼─────┐
    │ Postgres │            │   Redis    │
    │  :5432   │            │   :6379    │
    └──────────┘            └─────┬──────┘
                                  │
                         ┌────────▼────────┐
                         │  Celery Worker  │
                         │  Celery Beat    │
                         └─────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Monitoring Stack                      │
├─────────────┬───────────────┬───────────────────────────┤
│ Prometheus  │   Grafana     │     Alertmanager         │
│   :9090     │    :3001      │        :9093             │
└─────────────┴───────────────┴───────────────────────────┘
```

---

## 🔧 Common Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f prometheus

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services
```bash
# All
docker-compose restart

# Specific
docker-compose restart backend
docker-compose restart grafana
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U moatasimfarooque -d career_copilot

# Run migrations
docker-compose exec backend alembic upgrade head

# Backup
docker-compose exec postgres pg_dump -U moatasimfarooque career_copilot > backup.sql

# Restore
docker-compose exec -T postgres psql -U moatasimfarooque career_copilot < backup.sql
```

### Monitor Service Health
```bash
# Check status
docker-compose ps

# Check health
docker inspect career-copilot-backend | grep -A 10 Health

# Test endpoints
curl http://localhost:8002/health
curl http://localhost:8002/metrics
```

---

## 🔒 Security Setup

### 1. SSL Certificates

**For Development (Self-signed):**
```bash
mkdir -p deployment/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/nginx/ssl/key.pem \
  -out deployment/nginx/ssl/cert.pem
```

**For Production (Let's Encrypt):**
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone \
  -d career-copilot.com -d www.career-copilot.com

# Copy to nginx directory
sudo cp /etc/letsencrypt/live/career-copilot.com/fullchain.pem \
  deployment/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/career-copilot.com/privkey.pem \
  deployment/nginx/ssl/key.pem
```

### 2. Basic Auth for Monitoring

```bash
# Create password file
htpasswd -c deployment/nginx/.htpasswd admin
# Enter password when prompted

# Add to nginx volume in docker-compose.yml (already configured)
```

### 3. Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong `SECRET_KEY` (32+ chars random)
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Configure CORS origins properly
- [ ] Set up basic auth for monitoring endpoints
- [ ] Review nginx security headers
- [ ] Enable log rotation
- [ ] Set up automated backups

---

## 📈 Monitoring Dashboard Setup

### 1. Access Grafana
```
URL: http://localhost:3001
Username: admin
Password: (from .env or default: admin)
```

### 2. Dashboards Auto-Loaded

Already provisioned from `monitoring/grafana/dashboards/`:
- ✅ Business Analytics
- ✅ Infrastructure Monitoring  
- ✅ Production System Overview

### 3. Create Custom Dashboard

1. Click **"+"** → **Dashboard** → **Add Panel**
2. Select **Prometheus** as data source
3. Enter query:
   ```promql
   # Request rate
   rate(http_requests_total[5m])
   
   # Error rate
   rate(http_requests_total{status_code=~"5.."}[5m])
   
   # Response time (95th percentile)
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   
   # AI costs per hour
   rate(ai_cost_total[1h])
   ```

### 4. Set Up Alerts

1. Go to **Alerting** → **Alert Rules**
2. Create rule:
   ```yaml
   Name: High Error Rate
   Query: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
   For: 5m
   Severity: warning
   ```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Verify postgres is running
docker-compose ps postgres

# Test connection
docker-compose exec backend python -c \
  "from app.core.database import engine; print('OK')"

# Check database logs
docker-compose logs postgres
```

### Prometheus Not Scraping

1. Check targets: http://localhost:9090/targets
2. Verify backend /metrics: http://localhost:8002/metrics
3. Check prometheus logs:
   ```bash
   docker-compose logs prometheus
   ```

### Grafana Shows No Data

1. Verify data source: **Configuration** → **Data Sources**
2. Test connection to Prometheus
3. Check if Prometheus is collecting metrics:
   ```bash
   curl http://localhost:9090/api/v1/query?query=up
   ```

---

## 📦 Volumes & Data Persistence

All important data is persisted in Docker volumes:

- `career-copilot-postgres-data` - Database
- `career-copilot-redis-data` - Cache
- `career-copilot-prometheus-data` - Metrics (30 days)
- `career-copilot-grafana-data` - Dashboards & config
- `career-copilot-backend-uploads` - User uploads
- `career-copilot-backend-logs` - Application logs

**Backup volumes:**
```bash
docker run --rm -v career-copilot-postgres-data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data
```

**Restore volumes:**
```bash
docker run --rm -v career-copilot-postgres-data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

---

## 🎯 What's Next?

1. **Configure Environment** - Edit `.env` with your values
2. **Run Deployment** - Use `./deploy.sh` or docker-compose
3. **Access Grafana** - View your metrics dashboards
4. **Set Up Alerts** - Configure email/Slack notifications
5. **Monitor Performance** - Use dashboards to optimize
6. **Scale Up** - Add more workers as needed

---

## 📚 Additional Resources

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Guide](https://grafana.com/docs/grafana/latest/dashboards/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Next.js Docker Guide](https://nextjs.org/docs/deployment#docker-image)

---

## ✅ Summary

You now have:
- ✅ Production-ready Docker setup
- ✅ Development environment with hot-reload
- ✅ Complete monitoring stack (Prometheus + Grafana + Alertmanager)
- ✅ Nginx reverse proxy with SSL
- ✅ Automated deployment script
- ✅ Comprehensive documentation
- ✅ Security best practices
- ✅ Data persistence with volumes
- ✅ Health checks for all services
- ✅ Pre-built Grafana dashboards

**Total setup time: ~15 minutes** 🚀
