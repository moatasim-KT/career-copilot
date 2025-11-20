#!/bin/bash
# Career Copilot - Stop Local Services Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🛑 Stopping Career Copilot Services..."

# Read PIDs from file
if [ -f .local_services.pid ]; then
    read BACKEND_PID CELERY_PID FRONTEND_PID < .local_services.pid
    
    # Stop backend
    if [ -n "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    # Stop Celery
    if [ -n "$CELERY_PID" ] && kill -0 $CELERY_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping Celery (PID: $CELERY_PID)...${NC}"
        kill $CELERY_PID
        echo -e "${GREEN}✅ Celery stopped${NC}"
    fi
    
    # Stop frontend
    if [ -n "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    rm .local_services.pid
else
    echo -e "${YELLOW}No PID file found. Searching for running processes...${NC}"
    
    # Kill by process name as fallback
    pkill -f "uvicorn app.main:app" && echo -e "${GREEN}✅ Backend stopped${NC}" || true
    pkill -f "celery -A app.core.celery_app worker" && echo -e "${GREEN}✅ Celery stopped${NC}" || true
    pkill -f "npm run dev" && echo -e "${GREEN}✅ Frontend stopped${NC}" || true
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
