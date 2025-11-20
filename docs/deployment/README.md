# Deployment Documentation

> **Consolidated Guide**: All deployment-related documentation in one place.
> - Formerly: `deployment/DEPLOYMENT.md`, `deployment/PRODUCTION_CHECKLIST.md`

**Quick Links**: [[/index|Documentation Hub]] | [[/GETTING_STARTED|Getting Started]] | [[/architecture/README|Architecture]]

---

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Production Checklist](#production-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Database Migrations](#database-migrations)
5. [Monitoring & Logging](#monitoring--logging)
6. [Scaling Strategies](#scaling-strategies)
7. [Troubleshooting](#troubleshooting)

---

## Docker Deployment

### Production Docker Compose

```bash
# Start all services in production mode
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Environment Variables

See [[/ENVIRONMENT_CONFIGURATION|Environment Configuration Guide]] for complete reference.

**Critical production variables**:
```bash
# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-python-secrets>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://user:password@db:5432/career_copilot

# Redis
REDIS_URL=redis://redis:6379/0

# AI Provider
GROQ_API_KEY=gsk_your-production-key

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn
```

---

## Production Checklist

### Pre-Deployment

- [ ] All tests passing (`make test`)
- [ ] Code linted and formatted (`make quality-check`)
- [ ] Security audit clean (`npm audit`, `bandit`)
- [ ] Environment variables configured
- [ ] Database backup created
- [ ] SSL certificates obtained
- [ ] DNS configured

### Deployment

- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Static files built (`npm run build`)
- [ ] Docker images built
- [ ] Services started
- [ ] Health checks passing
- [ ] SSL/TLS configured
- [ ] Firewall rules applied

### Post-Deployment

- [ ] Smoke tests passed
- [ ] Monitoring dashboards configured
- [ ] Error tracking active (Sentry)
- [ ] Backup cron jobs scheduled
- [ ] Log rotation configured
- [ ] Performance baselines recorded

---

## Database Migrations

### Running Migrations

```bash
# View current version
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Rollback one version
docker-compose exec backend alembic downgrade -1

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Migration Best Practices

1. **Always test migrations** on staging first
2. **Create backups** before running migrations
3. **Use transactions** for data migrations
4. **Avoid breaking changes** in production
5. **Document migrations** in commit messages

---

## Monitoring & Logging

### Health Checks

```bash
# Backend health
curl https://your-domain.com/health

# Frontend health
curl https://your-domain.com/api/health

# Database connection
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"
```

### Log Locations

- **Backend**: `docker-compose logs backend`
- **Frontend**: `docker-compose logs frontend`
- **Nginx**: `docker-compose logs nginx`
- **PostgreSQL**: `docker-compose logs postgres`
- **Celery**: `docker-compose logs celery`

### Monitoring Tools

- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **New Relic**: APM (optional)

---

## Scaling Strategies

### Horizontal Scaling

1. **Backend**: Run multiple FastAPI instances behind load balancer
2. **Frontend**: Deploy to CDN (Vercel, Netlify)
3. **Database**: Read replicas for queries
4. **Redis**: Redis Cluster for high availability
5. **Celery**: Multiple workers across machines

### Vertical Scaling

1. **Increase resources**: More RAM, CPU for containers
2. **Optimize queries**: Add database indexes
3. **Cache aggressively**: Redis for frequently accessed data
4. **Connection pooling**: Reuse database connections

---

## Troubleshooting

### Common Issues

**Services won't start**:
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

**Database connection errors**:
```bash
# Verify database is running
docker-compose ps postgres

# Check connection string
docker-compose exec backend env | grep DATABASE_URL
```

**Frontend build errors**:
```bash
# Clear Next.js cache
docker-compose exec frontend rm -rf .next

# Rebuild
docker-compose build frontend
docker-compose up -d frontend
```

For more troubleshooting, see [[/troubleshooting/RUNBOOK|Operations Runbook]].

---

## Related Documentation

- **Getting Started**: [[/GETTING_STARTED|Setup Guide]]
- **Environment Config**: [[/ENVIRONMENT_CONFIGURATION|Environment Variables]]
- **Architecture**: [[/architecture/README|System Architecture]]
- **Troubleshooting**: [[/troubleshooting/README|Troubleshooting Hub]]

---

**Last Updated**: November 2025
