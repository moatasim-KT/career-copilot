#!/bin/bash

# Career Copilot - Automated Installation Script
# This script sets up the complete Career Copilot environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        REQUIRED_VERSION="3.11"
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            log_success "Python $PYTHON_VERSION found"
        else
            log_error "Python 3.11+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check pip
    if ! command_exists pip3; then
        log_error "pip3 not found. Please install pip"
        exit 1
    fi
    
    # Check Node.js (optional)
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            log_success "Node.js $(node --version) found"
            HAS_NODE=true
        else
            log_warning "Node.js 18+ recommended for Next.js frontend"
            HAS_NODE=false
        fi
    else
        log_warning "Node.js not found. Streamlit-only mode will be used"
        HAS_NODE=false
    fi
    
    # Check Git
    if ! command_exists git; then
        log_error "Git not found. Please install Git"
        exit 1
    fi
    
    log_success "System requirements check completed"
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p data/{chroma,storage,uploads,backups,logs}
    mkdir -p logs/{audit,security,performance}
    mkdir -p secrets/{ssl,keys}
    mkdir -p config/{environments,services}
    mkdir -p uploads/{generated,templates,versions}
    
    log_success "Directory structure created"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    log_success "Python environment ready"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Choose installation type
    echo "Choose installation type:"
    echo "1) Production (minimal dependencies)"
    echo "2) Development (includes testing tools)"
    echo "3) Full (all optional features)"
    read -p "Enter choice [1-3]: " INSTALL_TYPE
    
    case $INSTALL_TYPE in
        1)
            pip install -r requirements-prod.txt
            log_success "Production dependencies installed"
            ;;
        2)
            pip install -r requirements-dev.txt
            log_success "Development dependencies installed"
            ;;
        3)
            pip install -r requirements.txt
            pip install -e ".[all]"
            log_success "Full dependencies installed"
            ;;
        *)
            log_info "Installing production dependencies by default"
            pip install -r requirements-prod.txt
            ;;
    esac
}

# Install Node.js dependencies
install_node_deps() {
    if [ "$HAS_NODE" = true ]; then
        log_info "Installing Node.js dependencies..."
        
        cd frontend
        
        if [ -f "package.json" ]; then
            npm install
            log_success "Node.js dependencies installed"
        else
            log_warning "package.json not found, skipping Node.js setup"
        fi
        
        cd ..
    else
        log_info "Skipping Node.js dependencies (Node.js not available)"
    fi
}

# Setup configuration
setup_config() {
    log_info "Setting up configuration..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Environment file created from template"
        else
            log_warning "No .env.example found, creating basic .env"
            create_basic_env
        fi
    else
        log_info "Environment file already exists"
    fi
    
    # Generate JWT secret if needed
    if ! grep -q "JWT_SECRET_KEY=your-super-secret" .env; then
        JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
        log_success "JWT secret key generated"
    fi
    
    log_success "Configuration setup completed"
}

# Create basic environment file
create_basic_env() {
    cat > .env << EOF
# Career Copilot Configuration
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8002
FRONTEND_URL=http://localhost:8501

# Database
DATABASE_URL=sqlite:///./data/career_copilot.db
SQLITE_ENABLED=true

# Authentication
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_ALGORITHM=HS256
DISABLE_AUTH=false

# AI Services (REQUIRED - Add your API keys)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Optional Services
GROQ_ENABLED=false
ANTHROPIC_API_KEY=
LANGSMITH_TRACING=false

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:8501
ENABLE_RATE_LIMITING=true
MAX_FILE_SIZE_MB=50

# Features
ENABLE_MONITORING=true
ENABLE_CACHING=true
ENABLE_WEBSOCKETS=true
EOF
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Create database directory
    mkdir -p data
    
    # Run database migrations if alembic is available
    if [ -d "backend/alembic" ]; then
        cd backend
        python -m alembic upgrade head
        cd ..
        log_success "Database migrations completed"
    else
        log_info "No database migrations found, skipping"
    fi
    
    log_success "Database setup completed"
}

# Create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."
    
    # Create start script
    cat > start.sh << 'EOF'
#!/bin/bash
# Career Copilot Startup Script

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Career Copilot...${NC}"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Start backend in background
echo -e "${BLUE}Starting backend API...${NC}"
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${BLUE}Starting frontend...${NC}"
cd frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✓ Career Copilot started successfully!${NC}"
echo -e "${BLUE}Backend API: http://localhost:8002${NC}"
echo -e "${BLUE}Frontend: http://localhost:8501${NC}"
echo -e "${BLUE}API Docs: http://localhost:8002/docs${NC}"

# Create stop function
stop_services() {
    echo -e "\n${BLUE}Stopping Career Copilot...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

# Handle Ctrl+C
trap stop_services SIGINT

# Wait for processes
wait
EOF

    chmod +x start.sh
    
    # Create stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
# Career Copilot Stop Script

echo "🛑 Stopping Career Copilot services..."

# Kill backend processes
pkill -f "uvicorn app.main:app"
pkill -f "python -m uvicorn"

# Kill frontend processes
pkill -f "streamlit run"

echo "✓ All services stopped"
EOF

    chmod +x stop.sh
    
    log_success "Startup scripts created"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check if key packages are installed
    PACKAGES=("fastapi" "streamlit" "openai" "pydantic")
    
    for package in "${PACKAGES[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            log_success "$package is installed"
        else
            log_error "$package is not installed"
            return 1
        fi
    done
    
    # Check configuration
    if [ -f ".env" ]; then
        log_success "Configuration file exists"
    else
        log_error "Configuration file missing"
        return 1
    fi
    
    # Check directory structure
    if [ -d "data" ] && [ -d "logs" ]; then
        log_success "Directory structure is correct"
    else
        log_error "Directory structure is incomplete"
        return 1
    fi
    
    log_success "Installation verification completed"
}

# Main installation function
main() {
    echo "🚀 Career Copilot Installation Script"
    echo "======================================"
    
    check_requirements
    create_directories
    setup_python_env
    install_python_deps
    install_node_deps
    setup_config
    setup_database
    create_startup_scripts
    verify_installation
    
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file and add your OpenAI API key"
    echo "2. Run './start.sh' to start the application"
    echo "3. Open http://localhost:8501 in your browser"
    echo ""
    echo "For more information, see README.md"
}

# Run main function
main "$@"