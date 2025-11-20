# Running Career Copilot Locally (Without Docker)

## Quick Start

### 1. Ensure Prerequisites Are Running

Make sure PostgreSQL and Redis are installed and running:

```bash
# Check if services are running
psql -h localhost -U postgres -d career_copilot -c "SELECT 1;"
redis-cli ping

# If not running, start them:
brew services start postgresql@14
brew services start redis
```

### 2. Start All Services

Simply run the startup script:

```bash
./scripts/start-local-services.sh
```

This will:
- ✅ Check PostgreSQL and Redis are running
- ✅ Apply database migrations
- ✅ Start backend API on port 8000
- ✅ Start Celery worker for background jobs
- ✅ Wait 5 seconds (ensuring backend is fully ready)
- ✅ Start frontend on port 3000

### 3. Access the Application

**No login required!** Authentication is disabled in single-user mode.

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Stop All Services

```bash
./scripts/stop-local-services.sh
```

---

## Configuration

### Single-User Mode (No Authentication)

Authentication is **disabled** via `backend/.env`:

```bash
DISABLE_AUTH=true
```

This allows you to access the entire dashboard without login/password.

### Service Ports

- **Frontend**: 3000
- **Backend**: 8000
- **PostgreSQL**: 5432
- **Redis**: 6379

---

## Logs

All services log to the `logs/` directory:

```bash
# Watch backend logs
tail -f logs/backend.log

# Watch frontend logs
tail -f logs/frontend.log

# Watch Celery logs
tail -f logs/celery.log
```

---

## Troubleshooting

### PostgreSQL Not Running

```bash
# Start PostgreSQL
brew services start postgresql@14

# Or manually:
pg_ctl -D /usr/local/var/postgresql@14 start
```

### Redis Not Running

```bash
# Start Redis
brew services start redis

# Or manually:
redis-server
```

### Backend Fails to Start

1. Check logs: `cat logs/backend.log`
2. Ensure database migrations ran: `cd backend && alembic upgrade head`
3. Verify .env file has correct settings

### Frontend Fails to Start

1. Check logs: `cat logs/frontend.log`
2. Ensure dependencies installed: `cd frontend && npm install`
3. Verify `NEXT_PUBLIC_API_URL=http://localhost:8000` in frontend/.env.local

---

## Manual Service Management

If you prefer to run services manually:

### Backend

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Celery Worker

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm run dev
```

---

## Environment Variables

Key settings in `backend/.env`:

```bash
# Authentication
DISABLE_AUTH=true                # No login required

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot

# Redis
REDIS_URL=redis://localhost:6379/0

# API Port
API_PORT=8000
```
