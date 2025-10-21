# 🚀 Career Copilot

**AI-Powered Job Application Tracking and Career Management System**

Career Copilot is an intelligent, proactive system that transforms the job search process from a passive, manual activity into a guided, goal-oriented workflow. The system centralizes job opportunities, automates job discovery, provides personalized recommendations, and offers career development insights through a serverless, cost-effective architecture.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Security](#-security)
- [Monitoring](#-monitoring)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 Core Features
- **Centralized Job Dashboard**: View and manage all job opportunities in one place
- **Automated Job Discovery**: Daily ingestion of new opportunities from multiple sources
- **AI-Powered Recommendations**: Personalized job suggestions based on your profile
- **Smart Notifications**: Proactive email updates and progress tracking
- **Skill Gap Analysis**: Identify missing skills and get learning recommendations
- **Career Analytics**: Track application progress and market insights

### 🔧 Technical Features
- **Serverless Architecture**: Cost-effective, auto-scaling cloud functions
- **Real-time Updates**: WebSocket-powered live progress tracking
- **Advanced Security**: Enterprise-grade security with comprehensive audit logging
- **Mobile Responsive**: Optimized for all devices and screen sizes
- **Offline Support**: Continue working even without internet connection
- **Multi-source Integration**: APIs, web scraping, and manual entry

### 📊 Analytics & Insights
- **Application Tracking**: Monitor success rates and response times
- **Market Analysis**: Salary trends and industry insights
- **Skill Demand**: Most requested skills in your target market
- **Progress Reports**: Weekly and monthly career development summaries
- **Performance Metrics**: System health and optimization recommendations

## 🏗️ Architecture

Career Copilot implements a modern, serverless architecture designed for scalability and cost-efficiency:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   External      │
│   Dashboard     │◄──►│   Functions      │◄──►│   Services      │
│                 │    │                  │    │                 │
│ • HTML/CSS/JS   │    │ • FastAPI        │    │ • Job APIs      │
│ • Streamlit     │    │ • Cloud Functions│    │ • Email Service │
│ • Responsive UI │    │ • Authentication │    │ • Web Scraping  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │   Data Layer     │
                    │                  │
                    │ • Firestore DB   │
                    │ • Vector Store   │
                    │ • File Storage   │
                    │ • Cache Layer    │
                    └──────────────────┘
```

### Key Components

1. **Frontend Dashboard** (`frontend/`)
   - Interactive job tracking interface
   - Real-time progress monitoring
   - Analytics and reporting dashboards
   - Mobile-responsive design

2. **Backend API** (`backend/`)
   - RESTful API endpoints
   - Authentication and authorization
   - Business logic and data processing
   - Integration with external services

3. **Data Layer**
   - Firestore for primary data storage
   - ChromaDB for vector embeddings
   - Redis for caching
   - File storage for documents

4. **External Integrations**
   - Job APIs (Adzuna, Indeed, etc.)
   - Email services (SendGrid, SMTP)
   - AI/ML services (OpenAI, Anthropic)
   - Cloud services (GCP, AWS)

## 🛠️ Technology Stack

### Frontend
- **Framework**: Streamlit, Next.js (React)
- **Styling**: Tailwind CSS, Custom CSS
- **JavaScript**: Vanilla JS, TypeScript
- **Charts**: Chart.js, D3.js
- **Real-time**: WebSockets, Server-Sent Events

### Backend
- **Framework**: FastAPI (Python)
- **Runtime**: Python 3.11+
- **API**: RESTful APIs, GraphQL
- **Authentication**: JWT, Firebase Auth
- **Task Queue**: Celery, Redis

### Database & Storage
- **Primary DB**: Firestore (NoSQL)
- **Vector DB**: ChromaDB
- **Cache**: Redis
- **File Storage**: Google Cloud Storage
- **Search**: Elasticsearch (optional)

### AI & ML
- **LLM**: OpenAI GPT-4, Anthropic Claude
- **Embeddings**: Sentence Transformers
- **NLP**: spaCy, NLTK
- **Recommendations**: Custom algorithms

### Infrastructure
- **Cloud**: Google Cloud Platform
- **Serverless**: Cloud Functions, Cloud Run
- **Monitoring**: Cloud Monitoring, Prometheus
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Node.js 18+ (for frontend development)
- Google Cloud account (for deployment)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/career-copilot.git
cd career-copilot
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Install Dependencies
```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies (if using Next.js)
cd ../frontend
npm install
```

### 4. Start Development Servers
```bash
# Terminal 1: Backend API
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# Terminal 2: Frontend (Streamlit)
cd frontend
streamlit run app.py --server.port 8501

# Terminal 3: Frontend (Next.js - optional)
cd frontend
npm run dev
```

### 5. Access the Application
- **Streamlit Frontend**: http://localhost:8501
- **Next.js Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs

## 📦 Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18+ (for Next.js frontend development)
- **Git**: Latest version
- **Docker**: Optional, for containerized deployment
- **Google Cloud SDK**: Optional, for cloud deployment

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/career-copilot.git
cd career-copilot

# Install all dependencies at once
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Start the application
./start.sh
```

### Development Setup

#### 1. **Clone and Setup**
```bash
git clone https://github.com/yourusername/career-copilot.git
cd career-copilot
```

#### 2. **Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production dependencies
pip install -r requirements-prod.txt

# Or install development dependencies (includes testing tools)
pip install -r requirements-dev.txt

# Setup database
python -m alembic upgrade head

# Create initial data (optional)
python scripts/setup_initial_data.py
```

#### 3. **Frontend Setup**

**Option A: Streamlit (Recommended for quick start)**
```bash
cd frontend

# Install Streamlit dependencies
pip install -r requirements-prod.txt

# Start Streamlit app
streamlit run app.py --server.port 8501
```

**Option B: Next.js (Advanced UI)**
```bash
cd frontend

# Install Node.js dependencies
npm install
# Or use production package.json
npm install --production

# Build and start
npm run build
npm start
```

#### 4. **Configuration**
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Configure your settings
nano .env
```

**Required Environment Variables:**
```bash
# Core API Configuration
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./data/career_copilot.db

# Optional Services
GROQ_API_KEY=your-groq-api-key  # Alternative AI provider
LANGSMITH_API_KEY=your-langsmith-key  # Tracing
SENDGRID_API_KEY=your-sendgrid-key  # Email notifications
```

### Production Setup

#### 1. **Docker Deployment (Recommended)**
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual containers
docker build -t career-copilot-backend ./backend
docker build -t career-copilot-frontend ./frontend

# Run containers
docker run -d -p 8002:8002 career-copilot-backend
docker run -d -p 8501:8501 career-copilot-frontend
```

#### 2. **Manual Production Setup**
```bash
# Install production dependencies only
pip install -r requirements-prod.txt

# Set production environment
export ENVIRONMENT=production
export PRODUCTION_MODE=true

# Start with production server
gunicorn backend.app.main:app --host 0.0.0.0 --port 8002 --workers 4
```

#### 3. **Cloud Deployment**

**Google Cloud Platform:**
```bash
# Deploy backend to Cloud Run
gcloud run deploy career-copilot-api \
    --source ./backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

# Deploy frontend to Cloud Run
gcloud run deploy career-copilot-frontend \
    --source ./frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

**AWS Deployment:**
```bash
# Using AWS CDK
cd infrastructure/aws
cdk deploy

# Or using Serverless Framework
cd backend
serverless deploy
```

### Package Management

#### Python Dependencies

- **`requirements.txt`**: Unified dependencies for all environments
- **`requirements-prod.txt`**: Production-only dependencies (minimal)
- **`requirements-dev.txt`**: Development dependencies (includes testing)
- **`docker-requirements.txt`**: Minimal dependencies for containers
- **`pyproject.toml`**: Modern Python project configuration

#### Node.js Dependencies

- **`package.json`**: Standard Next.js dependencies
- **`package-prod.json`**: Production-optimized dependencies

#### Installation Commands

```bash
# Install specific requirement sets
pip install -r requirements-prod.txt     # Production only
pip install -r requirements-dev.txt      # Development (includes prod)
pip install -r docker-requirements.txt   # Minimal for containers

# Install with optional dependencies
pip install -e ".[dev]"                  # Development extras
pip install -e ".[ai]"                   # AI/ML extras
pip install -e ".[cloud]"                # Cloud services
pip install -e ".[all]"                  # Everything

# Node.js installations
npm install                               # Standard dependencies
npm ci --production                       # Production only
```

### Automated Installation (Recommended)

```bash
# Clone and run automated installer
git clone https://github.com/yourusername/career-copilot.git
cd career-copilot
./install.sh
```

The installer will:
- Check system requirements
- Create virtual environment
- Install dependencies
- Setup configuration
- Create startup scripts
- Verify installation

### Using Make Commands

```bash
# Quick development setup
make dev-setup

# Start application
make run

# Run tests
make test

# View all available commands
make help
```

### Package Management Summary

| File | Purpose | Usage |
|------|---------|-------|
| `requirements.txt` | Unified dependencies | `pip install -r requirements.txt` |
| `requirements-prod.txt` | Production minimal | `pip install -r requirements-prod.txt` |
| `requirements-dev.txt` | Development + testing | `pip install -r requirements-dev.txt` |
| `docker-requirements.txt` | Container optimized | Used in Dockerfile |
| `pyproject.toml` | Modern Python config | `pip install -e ".[dev]"` |
| `package.json` | Next.js dependencies | `npm install` |
| `package-prod.json` | Production Next.js | `npm install --production` |

### Verification

```bash
# Check system status
make status

# Check backend health
curl http://localhost:8002/api/v1/health

# Check frontend
curl http://localhost:8501

# Run comprehensive tests
make test
make test-coverage

# Check code quality
make lint
make format-check
```

### Troubleshooting

**Common Issues:**

1. **Missing Dependencies**
   ```bash
   # Reinstall all dependencies
   pip install --upgrade -r requirements.txt
   ```

2. **Database Issues**
   ```bash
   # Reset database
   rm -f data/career_copilot.db
   python -m alembic upgrade head
   ```

3. **Port Conflicts**
   ```bash
   # Change ports in .env file
   API_PORT=8003
   FRONTEND_PORT=8502
   ```

4. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod +x start.sh
   chmod +x scripts/*.sh
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# =============================================================================
# Application Settings
# =============================================================================
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8002
FRONTEND_URL=http://localhost:8501
PRODUCTION_MODE=false
DEVELOPMENT_MODE=true

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL=sqlite:///./data/career_copilot.db
SQLITE_DATABASE_PATH=data/career_copilot.db
SQLITE_ENABLED=true

# PostgreSQL (Production)
# DATABASE_URL=postgresql://user:password@localhost:5432/career_copilot

# Firestore (Optional)
FIRESTORE_PROJECT_ID=your-project-id
FIRESTORE_CREDENTIALS_PATH=./secrets/firestore-key.json
FIREBASE_ENABLED=false

# =============================================================================
# Authentication & Security
# =============================================================================
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
DISABLE_AUTH=false

# Firebase Authentication (Optional)
FIREBASE_PROJECT_ID=your-firebase-project
FIREBASE_SERVICE_ACCOUNT_KEY=path/to/service-account.json
FIREBASE_WEB_API_KEY=your-web-api-key

# =============================================================================
# AI/LLM Services
# =============================================================================
# OpenAI (Required)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1

# Anthropic Claude (Optional)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Groq (Optional - Fast inference)
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=mixtral-8x7b-32768
GROQ_ENABLED=false

# Ollama (Optional - Local models)
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# =============================================================================
# Vector Database
# =============================================================================
CHROMA_PERSIST_DIRECTORY=data/chroma
CHROMA_COLLECTION_NAME=job_embeddings

# =============================================================================
# Caching & Performance
# =============================================================================
ENABLE_REDIS_CACHING=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=20

# =============================================================================
# External Job APIs
# =============================================================================
ADZUNA_API_ID=your-adzuna-api-id
ADZUNA_API_KEY=your-adzuna-api-key

# =============================================================================
# Email & Notifications
# =============================================================================
# SendGrid (Recommended)
SENDGRID_API_KEY=your-sendgrid-api-key

# SMTP (Alternative)
SMTP_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Gmail API (Advanced)
GMAIL_ENABLED=false
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret

# Slack Integration
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=your-slack-webhook
SLACK_BOT_TOKEN=your-slack-bot-token

# =============================================================================
# Cloud Services
# =============================================================================
# Google Cloud Storage
GOOGLE_DRIVE_ENABLED=false
GOOGLE_DRIVE_CLIENT_ID=your-drive-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-drive-client-secret

# Backup Configuration
AUTO_BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=90
DEFAULT_BACKUP_PROVIDER=google_drive

# =============================================================================
# Security Settings
# =============================================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:8501
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=pdf,docx,txt

# Content Security Policy
ENABLE_CSP=true
ENABLE_HTTPS=false
FORCE_HTTPS=false

# Input Validation
MAX_INPUT_LENGTH=10000
ENABLE_INPUT_SANITIZATION=true
STRICT_VALIDATION=true

# =============================================================================
# Monitoring & Observability
# =============================================================================
ENABLE_MONITORING=true
ENABLE_PROMETHEUS=true
ENABLE_OPENTELEMETRY=true
METRICS_PORT=9090

# LangSmith Tracing (Optional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=career-copilot

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
AUDIT_LOG_FILE=logs/audit.log
SECURITY_LOG_FILE=logs/security.log
ENABLE_AUDIT_LOGGING=true

# =============================================================================
# Feature Flags
# =============================================================================
ENABLE_WEBSOCKETS=true
ENABLE_CACHING=true
ENABLE_ANALYTICS=true
ENABLE_REAL_TIME_UPDATES=true
ENABLE_ADVANCED_SEARCH=true
ENABLE_SKILL_MATCHING=true
ENABLE_SALARY_INSIGHTS=true

# =============================================================================
# Development Settings
# =============================================================================
API_DEBUG=false
ENABLE_HOT_RELOAD=true
ENABLE_PROFILING=false
ENABLE_TESTING_MODE=false
```

### Service Configuration

The application uses YAML configuration files in the `config/` directory:

- `config/base.yaml` - Base configuration
- `config/environments/development.yaml` - Development settings
- `config/environments/production.yaml` - Production settings
- `config/services/` - Individual service configurations

## 📖 Usage

### Getting Started

1. **Create Your Profile**
   - Set up your skills, experience level, and location preferences
   - Configure notification settings
   - Upload your resume (optional)

2. **Job Discovery**
   - The system automatically discovers jobs daily
   - Manually add jobs you find interesting
   - Review AI-generated recommendations

3. **Application Tracking**
   - Mark jobs as "Applied" when you submit applications
   - Track response rates and interview progress
   - Get insights on your job search performance

4. **Skill Development**
   - Review skill gap analysis
   - Get learning resource recommendations
   - Track skill acquisition progress

### Key Workflows

#### 1. Job Management
```python
# Add a new job opportunity
POST /api/v1/jobs
{
    "company": "TechCorp",
    "title": "Senior Software Engineer",
    "location": "San Francisco, CA",
    "tech_stack": ["Python", "React", "AWS"],
    "link": "https://company.com/jobs/123"
}

# Update job status
PUT /api/v1/jobs/{job_id}/status
{
    "status": "Applied",
    "application_date": "2024-01-15"
}
```

#### 2. Getting Recommendations
```python
# Get personalized job recommendations
GET /api/v1/recommendations?limit=10

# Response includes scored recommendations
{
    "recommendations": [
        {
            "job_id": "job_123",
            "score": 0.95,
            "match_reasons": ["Python", "Senior Level", "Remote OK"]
        }
    ]
}
```

#### 3. Analytics and Insights
```python
# Get skill gap analysis
GET /api/v1/analytics/skill-gaps

# Get application statistics
GET /api/v1/analytics/applications

# Get market insights
GET /api/v1/analytics/market-trends
```

### Frontend Features

#### Dashboard Overview
- **Job Pipeline**: Visual representation of your job application funnel
- **Recent Activity**: Latest jobs added and applications submitted
- **Quick Stats**: Application count, response rate, and success metrics
- **Recommendations**: AI-suggested jobs based on your profile

#### Job Management
- **Filter & Search**: Find jobs by company, title, location, or skills
- **Bulk Actions**: Apply filters or status updates to multiple jobs
- **Export Data**: Download your job data in CSV or JSON format
- **Import Jobs**: Bulk import from spreadsheets or other tools

#### Analytics Dashboard
- **Application Trends**: Track your application volume over time
- **Success Metrics**: Monitor response rates and interview conversion
- **Skill Analysis**: See which skills are most in demand
- **Market Insights**: Salary trends and job market analysis

## 🔌 API Documentation

### Authentication

All API endpoints require authentication via JWT tokens:

```bash
# Login to get token
POST /api/v1/auth/login
{
    "username": "user@example.com",
    "password": "your-password"
}

# Use token in subsequent requests
Authorization: Bearer <your-jwt-token>
```

### Core Endpoints

#### Jobs API
```bash
# List jobs with filtering
GET /api/v1/jobs?status=not_applied&location=remote&limit=20

# Get specific job
GET /api/v1/jobs/{job_id}

# Create new job
POST /api/v1/jobs

# Update job
PUT /api/v1/jobs/{job_id}

# Delete job
DELETE /api/v1/jobs/{job_id}
```

#### Recommendations API
```bash
# Get recommendations
GET /api/v1/recommendations?limit=10&min_score=0.7

# Provide feedback on recommendation
POST /api/v1/recommendations/{job_id}/feedback
{
    "rating": 5,
    "applied": true,
    "notes": "Great match!"
}
```

#### Analytics API
```bash
# Application statistics
GET /api/v1/analytics/applications

# Skill gap analysis
GET /api/v1/analytics/skill-gaps

# Market trends
GET /api/v1/analytics/market-trends

# Progress reports
GET /api/v1/analytics/reports/weekly
GET /api/v1/analytics/reports/monthly
```

#### User Profile API
```bash
# Get user profile
GET /api/v1/users/profile

# Update profile
PUT /api/v1/users/profile
{
    "skills": ["Python", "React", "AWS"],
    "experience_level": "senior",
    "locations": ["San Francisco", "Remote"]
}
```

### WebSocket Events

Real-time updates via WebSocket connection:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8002/ws');

// Listen for job updates
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'job_update') {
        updateJobInUI(data.job);
    }
};

// Send job status update
ws.send(JSON.stringify({
    type: 'update_job_status',
    job_id: 'job_123',
    status: 'Applied'
}));
```

## 🧪 Development

### Project Structure

```
career-copilot/
├── backend/                 # Backend API and services
│   ├── app/                # FastAPI application
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Data models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   ├── tests/             # Backend tests
│   ├── scripts/           # Utility scripts
│   └── requirements.txt   # Python dependencies
├── frontend/               # Frontend applications
│   ├── components/        # Reusable components
│   ├── pages/            # Application pages
│   ├── utils/            # Frontend utilities
│   ├── app.py            # Streamlit app
│   └── package.json      # Node.js dependencies
├── config/                # Configuration files
├── data/                 # Data storage
├── docs/                 # Documentation
├── scripts/              # Build and deployment scripts
├── tests/                # Integration tests
├── .env.example          # Environment template
├── docker-compose.yml    # Docker configuration
└── README.md            # This file
```

### Development Workflow

1. **Feature Development**
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
python -m pytest tests/
npm test

# Commit and push
git commit -m "Add new feature"
git push origin feature/new-feature
```

2. **Code Quality**
```bash
# Format code
black backend/
prettier --write frontend/

# Lint code
flake8 backend/
eslint frontend/

# Type checking
mypy backend/
tsc --noEmit frontend/
```

3. **Testing**
```bash
# Run all tests
make test

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
npm test -- --coverage
```

### Adding New Features

#### 1. Backend API Endpoint
```python
# backend/app/api/v1/new_feature.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint(user = Depends(get_current_user)):
    return {"message": "New feature"}
```

#### 2. Frontend Component
```python
# frontend/components/new_component.py
import streamlit as st

def render_new_component():
    st.subheader("New Feature")
    # Component implementation
```

#### 3. Database Model
```python
# backend/app/models/new_model.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class NewModel(Base):
    __tablename__ = "new_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
```

### Environment Setup

#### Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt
npm install --dev

# Setup pre-commit hooks
pre-commit install

# Start development services
docker-compose -f docker-compose.dev.yml up -d
```

#### Testing Environment
```bash
# Setup test database
export DATABASE_URL=sqlite:///./test.db
python -m alembic upgrade head

# Run tests with coverage
pytest --cov=app tests/
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                  # Unit tests
│   ├── test_models.py    # Model tests
│   ├── test_services.py  # Service tests
│   └── test_utils.py     # Utility tests
├── integration/          # Integration tests
│   ├── test_api.py       # API endpoint tests
│   ├── test_database.py  # Database tests
│   └── test_external.py  # External service tests
├── e2e/                  # End-to-end tests
│   ├── test_workflows.py # Complete user workflows
│   └── test_ui.py        # UI interaction tests
└── fixtures/             # Test data and fixtures
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-e2e

# Run with coverage
make test-coverage

# Run performance tests
make test-performance
```

### Test Configuration

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user():
    return {
        "username": "test@example.com",
        "password": "testpass123"
    }
```

### Writing Tests

#### Unit Test Example
```python
# tests/unit/test_recommendation_engine.py
import pytest
from app.services.recommendation_engine import RecommendationEngine

def test_calculate_job_score():
    engine = RecommendationEngine()
    user_profile = {"skills": ["Python", "React"]}
    job = {"tech_stack": ["Python", "Django"]}
    
    score = engine.calculate_job_score(user_profile, job)
    assert 0 <= score <= 1
    assert score > 0  # Should have some match
```

#### Integration Test Example
```python
# tests/integration/test_jobs_api.py
def test_create_job(client, auth_headers):
    job_data = {
        "company": "TestCorp",
        "title": "Software Engineer",
        "location": "Remote"
    }
    
    response = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["company"] == "TestCorp"
```

## 🚀 Deployment

### Local Deployment

#### Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Deployment
```bash
# Start backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8002

# Start frontend
cd frontend
streamlit run app.py --server.port 8501
```

### Cloud Deployment

#### Google Cloud Platform

1. **Setup GCP Project**
```bash
# Create project
gcloud projects create career-copilot-prod

# Enable APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable run.googleapis.com
```

2. **Deploy Backend**
```bash
# Deploy API to Cloud Run
gcloud run deploy career-copilot-api \
    --source ./backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

# Deploy scheduled functions
gcloud functions deploy job-ingestion \
    --runtime python311 \
    --trigger-topic job-ingestion-topic \
    --source ./backend/functions/job_ingestion
```

3. **Deploy Frontend**
```bash
# Deploy Streamlit app to Cloud Run
gcloud run deploy career-copilot-frontend \
    --source ./frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

4. **Setup Database**
```bash
# Create Firestore database
gcloud firestore databases create --region=us-central1

# Setup security rules
gcloud firestore rules deploy firestore.rules
```

#### AWS Deployment

1. **Deploy with AWS CDK**
```bash
# Install CDK
npm install -g aws-cdk

# Deploy infrastructure
cd infrastructure/aws
cdk deploy
```

2. **Deploy with Serverless Framework**
```bash
# Install Serverless
npm install -g serverless

# Deploy functions
cd backend
serverless deploy
```

### Environment-Specific Configuration

#### Production Settings
```yaml
# config/environments/production.yaml
environment: production
debug: false
database:
  host: production-db-host
  ssl_mode: require
security:
  enable_rate_limiting: true
  cors_origins: ["https://career-copilot.com"]
monitoring:
  enable_metrics: true
  log_level: INFO
```

#### Staging Settings
```yaml
# config/environments/staging.yaml
environment: staging
debug: true
database:
  host: staging-db-host
security:
  enable_rate_limiting: false
  cors_origins: ["https://staging.career-copilot.com"]
```

### CI/CD Pipeline

#### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GCP
        run: |
          gcloud run deploy career-copilot \
            --source . \
            --platform managed
```

## 🔒 Security

### Authentication & Authorization

#### JWT Authentication
```python
# JWT token generation and validation
from jose import JWTError, jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

#### Role-Based Access Control
```python
# User roles and permissions
class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

def require_role(required_role: UserRole):
    def decorator(func):
        def wrapper(current_user: User = Depends(get_current_user)):
            if current_user.role != required_role:
                raise HTTPException(403, "Insufficient permissions")
            return func(current_user)
        return wrapper
    return decorator
```

### Data Protection

#### Input Validation
```python
# Pydantic models for input validation
from pydantic import BaseModel, validator

class JobCreate(BaseModel):
    company: str
    title: str
    location: str
    
    @validator('company')
    def validate_company(cls, v):
        if len(v) < 2:
            raise ValueError('Company name too short')
        return v.strip()
```

#### SQL Injection Prevention
```python
# Using SQLAlchemy ORM prevents SQL injection
from sqlalchemy.orm import Session

def get_jobs(db: Session, user_id: int, filters: dict):
    query = db.query(Job).filter(Job.user_id == user_id)
    
    if filters.get('company'):
        query = query.filter(Job.company.ilike(f"%{filters['company']}%"))
    
    return query.all()
```

### Security Headers

```python
# Security middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://career-copilot.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["career-copilot.com", "*.career-copilot.com"]
)
```

### Secrets Management

```bash
# Using environment variables for secrets
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_PASSWORD=$(gcloud secrets versions access latest --secret="db-password")

# Google Cloud Secret Manager
gcloud secrets create openai-api-key --data-file=openai-key.txt
```

### Security Checklist

- [ ] All API endpoints require authentication
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention via ORM
- [ ] XSS prevention with CSP headers
- [ ] HTTPS enforced in production
- [ ] Secrets stored securely (not in code)
- [ ] Regular dependency updates
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Audit logging enabled

## 📊 Monitoring

### Application Monitoring

#### Health Checks
```python
# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "database": await check_database_health(),
        "external_apis": await check_external_apis(),
        "memory_usage": get_memory_usage()
    }
```

#### Metrics Collection
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.inc()
    REQUEST_DURATION.observe(duration)
    
    return response
```

### Logging

#### Structured Logging
```python
# Structured logging configuration
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "Job application created",
    user_id=user.id,
    job_id=job.id,
    company=job.company,
    timestamp=datetime.utcnow()
)
```

#### Log Aggregation
```yaml
# Fluentd configuration for log aggregation
<source>
  @type tail
  path /var/log/career-copilot/*.log
  pos_file /var/log/fluentd/career-copilot.log.pos
  tag career-copilot.*
  format json
</source>

<match career-copilot.**>
  @type elasticsearch
  host elasticsearch.logging.svc.cluster.local
  port 9200
  index_name career-copilot
</match>
```

### Performance Monitoring

#### Database Performance
```python
# Database query monitoring
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    logger.info("Query executed", duration=total, query=statement[:100])
```

#### API Performance
```python
# API response time monitoring
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    if process_time > 1.0:  # Log slow requests
        logger.warning(
            "Slow request detected",
            path=request.url.path,
            method=request.method,
            duration=process_time
        )
    
    return response
```

### Alerting

#### Alert Configuration
```yaml
# Prometheus alerting rules
groups:
  - name: career-copilot
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: DatabaseConnectionFailure
        expr: up{job="database"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
```

#### Notification Channels
```python
# Slack notifications for alerts
import requests

def send_slack_alert(message: str, severity: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    payload = {
        "text": f"🚨 {severity.upper()}: {message}",
        "channel": "#alerts",
        "username": "Career Copilot Monitor"
    }
    
    requests.post(webhook_url, json=payload)
```

### Monitoring Dashboard

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Career Copilot Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## 🤝 Contributing

We welcome contributions to Career Copilot! Here's how you can help:

### Getting Started

1. **Fork the Repository**
```bash
git clone https://github.com/yourusername/career-copilot.git
cd career-copilot
```

2. **Set Up Development Environment**
```bash
# Install dependencies
pip install -r requirements-dev.txt
npm install

# Setup pre-commit hooks
pre-commit install

# Run tests to ensure everything works
make test
```

3. **Create a Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

### Development Guidelines

#### Code Style
- **Python**: Follow PEP 8, use Black for formatting
- **JavaScript**: Use Prettier and ESLint
- **Documentation**: Write clear docstrings and comments
- **Testing**: Write tests for new features

#### Commit Messages
Use conventional commit format:
```
feat: add job recommendation algorithm
fix: resolve database connection issue
docs: update API documentation
test: add unit tests for user service
```

#### Pull Request Process

1. **Before Submitting**
   - Run all tests: `make test`
   - Format code: `make format`
   - Update documentation if needed
   - Add tests for new features

2. **PR Description Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Areas for Contribution

#### 🐛 Bug Fixes
- Check the [Issues](https://github.com/yourusername/career-copilot/issues) page
- Look for bugs labeled `good first issue`
- Fix and submit PR with test cases

#### ✨ New Features
- **Job Sources**: Add new job board integrations
- **AI Models**: Improve recommendation algorithms
- **UI/UX**: Enhance user interface and experience
- **Analytics**: Add new metrics and insights
- **Integrations**: Connect with more external services

#### 📚 Documentation
- Improve API documentation
- Add tutorials and guides
- Create video walkthroughs
- Translate documentation

#### 🧪 Testing
- Increase test coverage
- Add performance tests
- Create end-to-end test scenarios
- Improve test infrastructure

### Community Guidelines

- **Be Respectful**: Treat all contributors with respect
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Patient**: Remember that everyone is learning
- **Follow Code of Conduct**: Maintain a welcoming environment

### Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Special mentions in project updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

```
MIT License

Copyright (c) 2024 Career Copilot Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **OpenAI** for GPT models and API
- **Anthropic** for Claude AI assistance
- **Google Cloud Platform** for infrastructure
- **Streamlit** for rapid frontend development
- **FastAPI** for modern Python web framework
- **All Contributors** who have helped improve this project

## 📞 Support

### Getting Help

- **Documentation**: Check this README and inline documentation
- **Issues**: Create an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Email**: Contact us at support@career-copilot.com

### Reporting Issues

When reporting issues, please include:
- Operating system and version
- Python version
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages and logs
- Screenshots if applicable

### Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Describe the problem you're trying to solve
- Explain your proposed solution
- Consider the impact on existing users
- Be open to discussion and iteration

---

**Made with ❤️ by the Career Copilot Team**

*Transform your job search from reactive to proactive with AI-powered career guidance.*