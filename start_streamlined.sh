#!/bin/bash

# Career Copilot - Streamlined Startup Script
# This script starts the application with minimal dependencies and error handling

set -e  # Exit on any error

echo "🚀 Starting Career Copilot (Streamlined Mode)..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run from the project root directory."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements-prod.txt > /dev/null 2>&1

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/logs
mkdir -p data/uploads
mkdir -p data/backups
mkdir -p logs

# Create basic .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating basic .env file..."
    cat > .env << EOF
# Basic Configuration
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8002
FRONTEND_URL=http://localhost:8501

# Database
DATABASE_URL=sqlite:///./data/career_copilot.db

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# AI Services (Optional - add your keys)
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key

# Features
ENABLE_MONITORING=false
API_DEBUG=true
EOF
    echo "⚠️  Please edit .env file with your API keys and configuration"
fi

# Function to start backend
start_backend() {
    echo "🔧 Starting backend API server..."
    cd backend
    
    # Use streamlined main if available, otherwise fallback to regular main
    if [ -f "app/main_streamlined.py" ]; then
        echo "📡 Using streamlined backend..."
        python -c "
import sys
sys.path.append('.')
from app.main_streamlined import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8002, reload=True)
" &
    else
        echo "📡 Using regular backend..."
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
    fi
    
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend started (PID: $BACKEND_PID)"
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd frontend
    
    # Install frontend requirements if needed
    if [ -f "requirements-prod.txt" ]; then
        pip install -r requirements-prod.txt > /dev/null 2>&1
    fi
    
    streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
}

# Function to check if services are running
check_services() {
    echo "🔍 Checking services..."
    
    # Check backend
    if curl -s http://localhost:8002/api/v1/health > /dev/null 2>&1; then
        echo "✅ Backend is running on http://localhost:8002"
    else
        echo "⚠️  Backend health check failed"
    fi
    
    # Check frontend
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "✅ Frontend is running on http://localhost:8501"
    else
        echo "⚠️  Frontend health check failed"
    fi
}

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "✅ Frontend stopped"
    fi
    
    echo "👋 Career Copilot stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services
start_backend
sleep 3  # Give backend time to start

start_frontend
sleep 3  # Give frontend time to start

# Check services
check_services

echo ""
echo "🎉 Career Copilot is running!"
echo "📡 Backend API: http://localhost:8002"
echo "🎨 Frontend UI: http://localhost:8501"
echo "📚 API Docs: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait