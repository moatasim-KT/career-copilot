#!/bin/bash

# Career Copilot - Startup Script
# This script starts the comprehensive job tracking system

set -e

echo "🚀 Starting Career Copilot..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from .env.example${NC}"
    else
        echo -e "${YELLOW}⚠️  Generating .env template...${NC}"
        python scripts/system_manager.py config --action template
        if [ -f .env.template ]; then
            cp .env.template .env
            echo -e "${GREEN}✅ Created .env from generated template${NC}"
        else
            echo -e "${RED}❌ Could not create .env file. Please create manually.${NC}"
            exit 1
        fi
    fi
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo -e "${GREEN}✅ Virtual environment created and dependencies installed${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source backend/venv/bin/activate

# Check if database exists and is initialized
if [ ! -f "data/career_copilot.db" ] && [ ! -f "backend/data/career_copilot.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Initializing...${NC}"
    cd backend
    alembic upgrade head
    cd ..
    echo -e "${GREEN}✅ Database initialized${NC}"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down Career Copilot...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    echo -e "${GREEN}✅ Shutdown complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Validate environment before starting
echo -e "${BLUE}🔍 Validating environment...${NC}"
if python scripts/system_manager.py validate --type env > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Environment validation passed${NC}"
else
    echo -e "${YELLOW}⚠️  Environment validation warnings (continuing...)${NC}"
fi
echo ""

# Start backend
echo -e "${BLUE}🔧 Starting backend API...${NC}"
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
sleep 5

# Check if backend is running
if curl -s http://localhost:8002/health > /dev/null; then
    echo -e "${GREEN}✅ Backend API is running on http://localhost:8002${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:8002/docs${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    echo ""
fi

# Start frontend
echo -e "${BLUE}🎨 Starting frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
sleep 5

echo ""
echo -e "${GREEN}✅ Career Copilot is running!${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🌐 Frontend:${NC}        http://localhost:3000"
echo -e "${GREEN}🔧 Backend API:${NC}     http://localhost:8002"
echo -e "${GREEN}📚 API Docs:${NC}        http://localhost:8002/docs"
echo -e "${GREEN}🔍 Health Check:${NC}    http://localhost:8002/health"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for processes
wait
