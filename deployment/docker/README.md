# Career Copilot - Docker Deployment Guide

## 🚀 Quick Start

### Development Environment
```bash
# Start all services (backend, postgres, redis, prometheus, grafana)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down
```

### Production Environment
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📦 Services

### Core Services
- **Backend API** (port 8002): FastAPI application
- **Frontend** (port 3000): Next.js application
- **PostgreSQL** (port 5432): Database
- **Redis** (port 6379): Cache and task queue
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task scheduler
- **Nginx** (ports 80, 443): Reverse proxy

### Monitoring Stack
- **Prometheus** (port 9090): Metrics collection
- **Grafana** (port 3001): Metrics visualization
- **Alertmanager** (port 9093): Alert routing

## 🔧 Configuration

### 1. Environment Variables

Copy the example file and configure:
```bash
cp .env.example .env
# Edit .env with your actual values
```

Required variables:
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `SECRET_KEY`: Application secret key (32+ characters)
- `JWT_SECRET_KEY`: JWT signing key
- `OPENAI_API_KEY`: OpenAI API key (if using AI features)
- `SMTP_*`: Email configuration
- `GRAFANA_PASSWORD`: Grafana admin password

### 2. SSL Certificates (Production)

Generate self-signed certificates for testing:
```bash
mkdir -p deployment/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/nginx/ssl/key.pem \
  -out deployment/nginx/ssl/cert.pem
```

For production, use Let's Encrypt:
```bash
# Use certbot to generate real certificates
docker run -it --rm -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d career-copilot.com -d www.career-copilot.com
```

### 3. Nginx Basic Auth (Monitoring)

Create password file for Prometheus/Grafana access:
```bash
# Install htpasswd (if not available)
apt-get install apache2-utils  # Ubuntu/Debian
brew install httpd              # macOS

# Create password file
htpasswd -c deployment/nginx/.htpasswd admin
```

## 🏗️ Build Details

### Multi-stage Builds

**Backend Dockerfile:**
- `base`: Common dependencies
- `development`: Dev dependencies + hot-reload
- `production`: Optimized with gunicorn

**Frontend Dockerfile:**
- `deps`: Install dependencies
- `builder`: Build Next.js
- `runner`: Production-ready image

### Build Commands

```bash
# Build specific service
docker-compose build backend
docker-compose build frontend

# Build with no cache
docker-compose build --no-cache

# Build for specific stage
docker build -f deployment/docker/Dockerfile.backend \
  --target production -t career-copilot-backend .
```

## 📊 Accessing Services

### Development
- Frontend: http://localhost:3000
- Backend API: http://localhost:8002
- API Docs: http://localhost:8002/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### Production (via Nginx)
- Frontend: https://career-copilot.com
- Backend API: https://career-copilot.com/api/
- Prometheus: https://career-copilot.com/prometheus/ (basic auth)
- Grafana: https://career-copilot.com/grafana/ (basic auth)

## 🔍 Monitoring Setup

### 1. Access Grafana
```
URL: http://localhost:3001
Username: admin
Password: (set in .env or default: admin)
```

### 2. Verify Prometheus Data Source
- Go to Configuration → Data Sources
- Prometheus should be auto-configured at http://prometheus:9090

### 3. Import Dashboards
Dashboards are auto-loaded from `monitoring/grafana/dashboards/`:
- Business Analytics
- Infrastructure Monitoring
- Production System Overview
- Contract Analyzer Dashboard

### 4. View Metrics
- Backend metrics: http://localhost:8002/metrics
- Prometheus UI: http://localhost:9090
- Query example: `rate(http_requests_total[5m])`

## 🔧 Common Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f prometheus
docker-compose logs -f grafana

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
docker-compose restart prometheus
```

### Execute Commands in Container
```bash
# Backend shell
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend alembic upgrade head

# Django-style management commands
docker-compose exec backend python -m app.cli migrate
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U moatasimfarooque -d career_copilot

# Backup database
docker-compose exec postgres pg_dump -U moatasimfarooque career_copilot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U moatasimfarooque career_copilot < backup.sql
```

### Redis Operations
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# With password
docker-compose exec redis redis-cli -a your_redis_password

# Flush all data (careful!)
docker-compose exec redis redis-cli FLUSHALL
```

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check status
docker-compose ps

# Check logs
docker-compose logs backend

# Restart specific service
docker-compose restart backend
```

### Database Connection Issues
```bash
# Verify postgres is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "from app.core.database import get_db; print('OK')"
```

### Prometheus Not Scraping
```bash
# Check Prometheus targets
# Visit: http://localhost:9090/targets

# Verify backend /metrics endpoint
curl http://localhost:8002/metrics

# Check Prometheus config
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
```

### Grafana No Data
```bash
# Check data source connection
# Visit: http://localhost:3001/datasources

# Verify Prometheus is accessible from Grafana
docker-compose exec grafana wget -O- http://prometheus:9090/api/v1/query?query=up
```

### Frontend Build Fails
```bash
# Check Next.js config
cat frontend/next.config.js

# Rebuild without cache
docker-compose build --no-cache frontend

# Check for syntax errors
docker-compose run frontend npm run lint
```

## 🔒 Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure SSL certificates for production
- [ ] Set up nginx basic auth for monitoring endpoints
- [ ] Configure firewall rules
- [ ] Enable HTTPS redirect
- [ ] Set up rate limiting
- [ ] Configure CORS origins properly
- [ ] Review security headers in nginx.conf
- [ ] Set up backup strategy for volumes

## 📈 Performance Tuning

### Database
```yaml
# Add to docker-compose.yml under postgres service
command: >
  postgres
  -c shared_buffers=256MB
  -c effective_cache_size=1GB
  -c maintenance_work_mem=64MB
  -c checkpoint_completion_target=0.9
```

### Redis
```yaml
# Add to docker-compose.yml under redis service
command: >
  redis-server
  --maxmemory 512mb
  --maxmemory-policy allkeys-lru
```

### Backend (Gunicorn)
```dockerfile
# Adjust workers based on CPU cores
CMD ["gunicorn", "app.main:app", "--workers", "4"]
# Formula: (2 x num_cores) + 1
```

## 🗑️ Cleanup

### Remove All Containers and Volumes
```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove all unused Docker resources
docker system prune -a --volumes
```

### Remove Specific Volumes
```bash
# List volumes
docker volume ls

# Remove specific volume
docker volume rm career-copilot-postgres-data
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Next.js Docker Guide](https://nextjs.org/docs/deployment)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
