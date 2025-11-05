#!/bin/bash
# Quick Start Script for Career Copilot Services
# Run this to start Celery Worker and Beat scheduler

set -e

echo "=================================================="
echo "  Career Copilot - Starting Background Services"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Redis
echo -n "Checking Redis connection... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo "Please start Redis first: redis-server"
    exit 1
fi

# Check if Celery is already running
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${YELLOW}⚠️  Celery Worker is already running${NC}"
    echo "To restart, first kill it: pkill -f 'celery.*worker'"
else
    echo "Starting Celery Worker..."
    nohup celery -A app.celery worker --loglevel=info > logs/celery/worker.log 2>&1 &
    WORKER_PID=$!
    sleep 2
    if ps -p $WORKER_PID > /dev/null; then
        echo -e "${GREEN}✅ Celery Worker started (PID: $WORKER_PID)${NC}"
        echo "   Logs: logs/celery/worker.log"
    else
        echo -e "${RED}❌ Failed to start Celery Worker${NC}"
        exit 1
    fi
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo -e "${YELLOW}⚠️  Celery Beat is already running${NC}"
    echo "To restart, first kill it: pkill -f 'celery.*beat'"
else
    echo "Starting Celery Beat..."
    nohup celery -A app.celery beat --loglevel=info > logs/celery/beat.log 2>&1 &
    BEAT_PID=$!
    sleep 2
    if ps -p $BEAT_PID > /dev/null; then
        echo -e "${GREEN}✅ Celery Beat started (PID: $BEAT_PID)${NC}"
        echo "   Logs: logs/celery/beat.log"
    else
        echo -e "${RED}❌ Failed to start Celery Beat${NC}"
        exit 1
    fi
fi

echo ""
echo "=================================================="
echo "  All services started successfully!"
echo "=================================================="
echo ""
echo "Scheduled Tasks:"
echo "  • Job Scraping: Daily at 4:00 AM"
echo "  • Morning Briefings: Daily at 8:00 AM"
echo "  • Evening Summaries: Daily at 8:00 PM"
echo ""
echo "Monitor with:"
echo "  • Worker logs: tail -f logs/celery/worker.log"
echo "  • Beat logs: tail -f logs/celery/beat.log"
echo "  • Check tasks: celery -A app.celery inspect active"
echo ""
echo "To stop services:"
echo "  pkill -f 'celery.*worker'"
echo "  pkill -f 'celery.*beat'"
echo ""
