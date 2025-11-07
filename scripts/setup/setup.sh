#!/bin/bash
# =============================================================================
# Career Copilot - Quick Setup Script
# =============================================================================
# This script automates the initial setup for Career Copilot
# Run this script from the project root directory
# =============================================================================

set -e  # Exit on error

echo "=================================="
echo "Career Copilot - Quick Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# =============================================================================
# Step 1: Check Prerequisites
# =============================================================================
echo "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python ${PYTHON_VERSION} found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 18 or higher"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Node.js ${NODE_VERSION} found"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "${RED}Error: npm is not installed${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✓ npm ${NPM_VERSION} found"

echo ""

# =============================================================================
# Step 2: Setup Backend Environment
# =============================================================================
echo "${YELLOW}Step 2: Setting up backend environment...${NC}"

cd "$PROJECT_ROOT/backend"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo "${YELLOW}⚠️  Please edit backend/.env and add your API keys${NC}"
else
    echo "✓ .env file already exists"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Created virtual environment"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "Installing backend dependencies..."
echo "This may take a few minutes..."
pip install -e ".[all]" > /dev/null 2>&1 || {
    echo "${YELLOW}Warning: Some optional dependencies may have failed to install${NC}"
    echo "Installing core dependencies only..."
    pip install -e . > /dev/null 2>&1
}
echo "✓ Backend dependencies installed"

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    mkdir -p data
    echo "✓ Created data directory"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || {
    echo "${YELLOW}Warning: Database migrations failed${NC}"
    echo "You may need to run 'alembic upgrade head' manually"
}

echo "✓ Backend setup complete"
echo ""

# =============================================================================
# Step 3: Setup Frontend Environment
# =============================================================================
echo "${YELLOW}Step 3: Setting up frontend environment...${NC}"

cd "$PROJECT_ROOT/frontend"

# Create .env.local file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file from template..."
    cp .env.local.example .env.local
    echo "✓ Created .env.local file"
else
    echo "✓ .env.local file already exists"
fi

# Install dependencies
echo "Installing frontend dependencies..."
echo "This may take a few minutes..."
npm install > /dev/null 2>&1 || {
    echo "${RED}Error: Failed to install frontend dependencies${NC}"
    exit 1
}
echo "✓ Frontend dependencies installed"

echo ""

# =============================================================================
# Step 4: Setup Summary
# =============================================================================
echo "${GREEN}=================================="
echo "Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment variables:"
echo "   - Edit ${YELLOW}backend/.env${NC} (add API keys, database URL, etc.)"
echo "   - Edit ${YELLOW}frontend/.env.local${NC} (usually default values are fine)"
echo ""
echo "2. Start the backend server:"
echo "   ${YELLOW}cd backend${NC}"
echo "   ${YELLOW}source venv/bin/activate${NC}  # Activate virtual environment"
echo "   ${YELLOW}uvicorn app.main:app --reload --host 0.0.0.0 --port 8002${NC}"
echo ""
echo "3. In a new terminal, start the frontend:"
echo "   ${YELLOW}cd frontend${NC}"
echo "   ${YELLOW}npm run dev${NC}"
echo ""
echo "4. Access the application:"
echo "   - Frontend: ${GREEN}http://localhost:3000${NC}"
echo "   - Backend API: ${GREEN}http://localhost:8002${NC}"
echo "   - API Docs: ${GREEN}http://localhost:8002/docs${NC}"
echo ""
echo "${YELLOW}For a small team deployment, you can use SQLite (default)${NC}"
echo "${YELLOW}For production, configure PostgreSQL in backend/.env${NC}"
echo ""
