# Installation Guide

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 7 or higher
- **Git**: Latest version

### System Requirements

- **OS**: Linux, macOS, or Windows (with WSL2)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for API services

## Quick Start (5 Minutes)

The fastest way to get started with Career Copilot:

```bash
# 1. Clone the repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Start all services with Docker
docker-compose up -d

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Standard Installation

### 1. Clone Repository

```bash
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

### 4. Background Services

```bash
# In a new terminal - Start Celery worker
cd backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info

# In another terminal - Start Celery beat scheduler
celery -A app.core.celery_app beat --loglevel=info
```

## Docker Installation

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Individual Service Containers

```bash
# Backend only
docker build -f deployment/docker/Dockerfile.backend -t career-copilot-backend .
docker run -p 8000:8000 career-copilot-backend

# Frontend only
docker build -f deployment/docker/Dockerfile.frontend -t career-copilot-frontend .
docker run -p 3000:3000 career-copilot-frontend
```

## Database Setup

### PostgreSQL

```bash
# Create database
createdb career_copilot

# Run migrations
cd backend
alembic upgrade head

# Initialize demo data (optional)
python scripts/initialize_demo_data.py
```

### Redis

```bash
# Start Redis server
redis-server

# Verify connection
redis-cli ping
# Should return: PONG
```

## Verification

### Backend Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Frontend Access

Open browser: http://localhost:3000

### API Documentation

Open browser: http://localhost:8000/docs

## Post-Installation

### Create User Account

The system operates in single-user mode (User ID: 1):

```bash
cd backend
python scripts/create_test_user.py
```

### Configure AI Providers

Edit `.env` to add your API keys:

```env
# OpenAI (required for resume generation)
OPENAI_API_KEY=sk-...

# Anthropic Claude (optional, for enhanced analysis)
ANTHROPIC_API_KEY=sk-ant-...
```

### Test the Installation

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd frontend
npm test
```

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Find process using port 3000
lsof -ti:3000 | xargs kill -9
```

**Database Connection Error**
```bash
# Verify PostgreSQL is running
pg_isready

# Check connection string in .env
DATABASE_URL=postgresql://user:password@localhost:5432/career_copilot
```

**Redis Connection Error**
```bash
# Verify Redis is running
redis-cli ping

# Check Redis URL in .env
REDIS_URL=redis://localhost:6379/0
```

**Module Not Found Errors**
```bash
# Backend: Reinstall dependencies
pip install -r requirements.txt

# Frontend: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- [Configuration Guide](CONFIGURATION.md) - Configure environment variables
- [Development Guide](../development/DEVELOPMENT.md) - Start developing
- [API Documentation](../api/API.md) - Explore the API
- [Troubleshooting](../troubleshooting/COMMON_ISSUES.md) - Common problems

## Support

For installation issues:
- Check [Troubleshooting Guide](../troubleshooting/COMMON_ISSUES.md)
- Open an issue on [GitHub](https://github.com/moatasim-KT/career-copilot/issues)
- Contact: moatasimfarooque@gmail.com
