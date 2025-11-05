# 🔧 Quick Fix for Docker Deployment Issue

## Issue Encountered
```
error getting credentials - err: exec: "docker-credential-osxkeychain": executable file not found in $PATH
```

## ✅ Solution Applied

The Docker credential helper was misconfigured. I've fixed it by removing the `credsStore` entry from `~/.docker/config.json`.

---

## 🚀 Simplified Deployment Steps

### Option 1: Start with Core Services Only (Recommended First)

```bash
# Use the minimal compose file (Backend + PostgreSQL + Redis only)
docker-compose -f docker-compose.minimal.yml up -d --build

# Check status
docker-compose -f docker-compose.minimal.yml ps

# View logs
docker-compose -f docker-compose.minimal.yml logs -f backend

# Access
# Backend: http://localhost:8002
# API Docs: http://localhost:8002/docs
```

### Option 2: Full Development Stack (with Monitoring)

```bash
# Build images first
docker-compose -f docker-compose.dev.yml build

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps

# View all logs
docker-compose -f docker-compose.dev.yml logs -f

# Access
# Backend: http://localhost:8002
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001
```

### Option 3: Full Production Stack

```bash
# Make sure .env is configured
cp .env.example .env
# Edit .env with your values

# Build images
docker-compose build

# Start services
docker-compose up -d

# Monitor startup
docker-compose logs -f
```

---

## 🔍 Troubleshooting

### If build is slow or hangs:

```bash
# Build one service at a time
docker-compose build postgres
docker-compose build redis
docker-compose build backend

# Then start
docker-compose up -d
```

### If you see "version is obsolete" warning:

This is just a warning and can be ignored. Or remove the first line `version: '3.8'` from docker-compose.yml files.

### Check Docker resources:

```bash
# See Docker resource usage
docker stats

# Clean up if needed
docker system prune -a
```

---

## 📊 What's Available

### Minimal Setup (docker-compose.minimal.yml)
- ✅ Backend API
- ✅ PostgreSQL
- ✅ Redis
- ⏱️ Fastest startup (~30 seconds)
- 💾 Lowest resources (~1GB RAM)

### Development Setup (docker-compose.dev.yml)
- ✅ Everything in Minimal
- ✅ Prometheus
- ✅ Grafana
- ⏱️ Medium startup (~1-2 minutes)
- 💾 Medium resources (~2GB RAM)

### Production Setup (docker-compose.yml)
- ✅ Everything in Development
- ✅ Frontend (Next.js)
- ✅ Celery Worker + Beat
- ✅ Nginx
- ✅ Alertmanager
- ⏱️ Full startup (~3-5 minutes)
- 💾 Higher resources (~4GB RAM)

---

## 🎯 Recommended Workflow

### First Time:
1. Start with minimal setup to test backend
2. If working, add monitoring (dev setup)
3. Finally try full production stack

### Commands:

```bash
# Step 1: Test minimal
docker-compose -f docker-compose.minimal.yml up -d
curl http://localhost:8002/health

# Step 2: If working, stop and try dev
docker-compose -f docker-compose.minimal.yml down
docker-compose -f docker-compose.dev.yml up -d

# Step 3: If working, try full production
docker-compose -f docker-compose.dev.yml down
docker-compose up -d
```

---

## 💡 Common Issues & Solutions

### "Cannot connect to Docker daemon"
```bash
# Start Docker Desktop
open -a Docker

# Wait 30 seconds then try again
```

### "Port already in use"
```bash
# Check what's using the port
lsof -i :8002  # or :5432, :6379, etc.

# Stop the process or change the port in docker-compose.yml
```

### "Out of disk space"
```bash
# Clean up Docker
docker system prune -a --volumes

# This removes:
# - Stopped containers
# - Unused images
# - Unused volumes
# - Build cache
```

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: Wait 10 more seconds
# - Missing .env: Copy from .env.example
# - Wrong DATABASE_URL: Check format in logs
```

---

## 📖 Next Steps After Successful Deployment

1. **Access API Documentation**: http://localhost:8002/docs
2. **Check Metrics**: http://localhost:8002/metrics (if running)
3. **View Grafana Dashboards**: http://localhost:3001 (dev/prod setups)
4. **Run Database Migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
5. **Create Test User**:
   ```bash
   docker-compose exec backend python scripts/create_test_user.py
   ```

---

## 🆘 If All Else Fails

Run services manually (without Docker):

```bash
# Terminal 1: Start PostgreSQL
brew services start postgresql@15

# Terminal 2: Start Redis
brew services start redis

# Terminal 3: Start Backend
cd backend
uvicorn app.main:app --reload --port 8002
```

Then add monitoring later when you have more time to debug Docker issues.
