#!/bin/bash
# Career Copilot - Local Services Startup Script
# Starts backend and frontend services locally (without Docker)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting Career Copilot Services Locally..."

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if redis-cli ping &> /dev/null && psql -h localhost -U postgres -d career_copilot -c "SELECT 1;" &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo "Please start PostgreSQL:"
    echo "  brew services start postgresql@14"
    exit 1
fi

# Check if Redis is running
echo -e "${YELLOW}Checking Redis...${NC}"
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Please start Redis:"
    echo "  brew services start redis"
    exit 1
fi

# Apply database migrations
echo -e "${YELLOW}Applying database migrations...${NC}"
cd backend
alembic upgrade head
cd ..
echo -e "${GREEN}✅ Database migrations applied${NC}"

# Start backend in background
echo -e "${YELLOW}Starting backend API...${NC}"
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo "   Logs: tail -f logs/backend.log"

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check logs/backend.log for errors"
    exit 1
fi

# Start Celery worker in background (optional)
echo -e "${YELLOW}Starting Celery worker (optional)...${NC}"
cd backend
celery -A app.core.celery_app worker --loglevel=info --concurrency=2 > ../logs/celery.log 2>&1 &
CELERY_PID=$!
cd ..
echo -e "${GREEN}✅ Celery worker started (PID: $CELERY_PID)${NC}"
echo "   Logs: tail -f logs/celery.log"

# Add delay before starting frontend (as requested)
echo -e "${YELLOW}Waiting 5 seconds before starting frontend...${NC}"
sleep 5

# Start frontend
echo -e "${YELLOW}Starting frontend...${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "   Logs: tail -f logs/frontend.log"

# Save PIDs for cleanup
echo "$BACKEND_PID $CELERY_PID $FRONTEND_PID" > .local_services.pid

echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 Log files:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Celery:   tail -f logs/celery.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./scripts/stop-local-services.sh"
echo ""
echo "⚠️  Authentication is DISABLED (single-user mode)"
echo "   You can access the dashboard directly without login"
echo ""
