# Deployment Guide

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

## Overview

This guide covers deploying Career Copilot to production environments.

## Deployment Options

1. **Docker Compose** (Recommended for small deployments)
2. **Kubernetes** (For scalable production)
3. **Traditional VPS** (Manual deployment)
4. **Cloud Platforms** (Render, AWS, GCP, Azure)

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificates obtained
- [ ] Domain name configured
- [ ] Backup strategy implemented
- [ ] Monitoring tools set up
- [ ] Security audit completed
- [ ] Performance testing done

## Docker Compose Deployment

### 1. Prepare Environment

```bash
# Clone repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# Create production environment file
cp .env.example .env.production
# Edit .env.production with production values
```

### 2. Configure Production Settings

```env
# .env.production
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=<generate-secure-key>

# Database (use external PostgreSQL)
DATABASE_URL=postgresql://user:password@db-host:5432/career_copilot

# Redis (use external Redis)
REDIS_URL=redis://redis-host:6379/0

# URLs
FRONTEND_URL=https://career-copilot.com
BACKEND_URL=https://api.career-copilot.com

# AI Providers
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<app-password>
```

### 3. Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create initial user
docker-compose exec backend python scripts/create_test_user.py

# Check logs
docker-compose logs -f
```

### 4. Set Up Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/career-copilot
server {
    listen 80;
    server_name career-copilot.com www.career-copilot.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name career-copilot.com www.career-copilot.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/career-copilot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/career-copilot.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site and reload nginx
sudo ln -s /etc/nginx/sites-available/career-copilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Kubernetes Deployment

### 1. Prepare Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: career-copilot
```

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: career-copilot-config
  namespace: career-copilot
data:
  ENVIRONMENT: "production"
  FRONTEND_URL: "https://career-copilot.com"
  BACKEND_URL: "https://api.career-copilot.com"
```

```yaml
# k8s/secrets.yaml (encrypt with kubeseal)
apiVersion: v1
kind: Secret
metadata:
  name: career-copilot-secrets
  namespace: career-copilot
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  OPENAI_API_KEY: "your-openai-key"
  DATABASE_URL: "postgresql://..."
  REDIS_URL: "redis://..."
```

### 2. Deploy Services

```bash
# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n career-copilot
kubectl get services -n career-copilot
```

## Cloud Platform Deployment

### Render.com

Using the included `render.yaml`:

1. **Connect Repository**: Link GitHub repo to Render
2. **Configure Environment**: Add secrets in Render dashboard
3. **Deploy**: Render auto-deploys from main branch

### AWS (EC2 + RDS)

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. Install dependencies
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx

# 3. Clone and deploy
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Configure RDS
# Use RDS PostgreSQL endpoint in DATABASE_URL

# 5. Set up SSL
sudo certbot --nginx -d career-copilot.com
```

### Google Cloud Platform

```bash
# 1. Build and push images
gcloud builds submit --config deployment/gcp/cloudbuild.yaml

# 2. Deploy to Cloud Run
gcloud run deploy career-copilot-backend \
  --image gcr.io/PROJECT_ID/backend \
  --platform managed \
  --region us-central1

gcloud run deploy career-copilot-frontend \
  --image gcr.io/PROJECT_ID/frontend \
  --platform managed \
  --region us-central1

# 3. Configure Cloud SQL
gcloud sql instances create career-copilot-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1
```

## Database Setup

### Run Migrations

```bash
# Docker
docker-compose exec backend alembic upgrade head

# Local
cd backend
source venv/bin/activate
alembic upgrade head
```

### Create Initial Data

```bash
# Create test user
docker-compose exec backend python scripts/create_test_user.py

# Initialize demo data (optional)
docker-compose exec backend python scripts/initialize_demo_data.py
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
# scripts/backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/daily"
DB_NAME="career_copilot"

# Create backup
docker-compose exec -T postgres pg_dump -U postgres $DB_NAME > \
  $BACKUP_DIR/backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/backup_$DATE.sql

# Delete backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

```bash
# Add to crontab
0 2 * * * /path/to/scripts/backup_database.sh
```

## Monitoring

### Health Checks

```bash
# Backend health
curl https://api.career-copilot.com/health

# Expected response
{"status":"healthy","database":"ok","redis":"ok"}
```

### Logging

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery

# Kubernetes
kubectl logs -f deployment/backend -n career-copilot
```

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'career-copilot-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

## Security

### SSL Certificates (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d career-copilot.com -d www.career-copilot.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### Security Headers

Add to Nginx config:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## Performance Optimization

### Enable Caching

```nginx
# Nginx caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout updating;
}
```

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);

-- Analyze tables
ANALYZE jobs;
ANALYZE applications;
```

### Enable Compression

```nginx
# Nginx gzip
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml;
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend workers
docker-compose up -d --scale backend=3

# Kubernetes
kubectl scale deployment backend --replicas=3 -n career-copilot
```

### Database Read Replicas

```yaml
# docker-compose.yml
services:
  postgres-replica:
    image: postgres:14-alpine
    environment:
      POSTGRES_REPLICA_MODE: slave
      POSTGRES_MASTER_SERVICE: postgres
```

## Rollback Strategy

### Docker Compose

```bash
# Tag current version
docker-compose build
docker tag career-copilot-backend:latest career-copilot-backend:v1.0.0

# Rollback
docker-compose down
docker-compose up -d career-copilot-backend:v1.0.0
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/backend -n career-copilot

# Check rollout status
kubectl rollout status deployment/backend -n career-copilot
```

## Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check logs
docker-compose logs

# Check resources
docker stats
df -h
```

**Database connection errors**
```bash
# Verify database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -d career_copilot -c "SELECT 1;"
```

**SSL certificate issues**
```bash
# Renew certificate
sudo certbot renew

# Check certificate
sudo certbot certificates
```

## Post-Deployment

### Verification

```bash
# Health check
curl https://api.career-copilot.com/health

# API documentation
curl https://api.career-copilot.com/docs

# Frontend
curl https://career-copilot.com
```

### Monitoring Setup

1. Configure uptime monitoring (UptimeRobot, Pingdom)
2. Set up error tracking (Sentry)
3. Enable performance monitoring (New Relic, DataDog)
4. Configure log aggregation (ELK, Splunk)

## Maintenance

### Update Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Database Maintenance

```bash
# Vacuum database (weekly)
docker-compose exec postgres psql -U postgres -d career_copilot -c "VACUUM ANALYZE;"

# Reindex database (monthly)
docker-compose exec postgres psql -U postgres -d career_copilot -c "REINDEX DATABASE career_copilot;"
```

## Next Steps

- [Monitoring Setup](MONITORING.md) - Set up monitoring
- [Troubleshooting](../troubleshooting/COMMON_ISSUES.md) - Common issues
- [Security Guide](SECURITY.md) - Security best practices
- [Architecture](../architecture/ARCHITECTURE.md) - System design
