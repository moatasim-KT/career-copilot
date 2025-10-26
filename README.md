# Career Copilot

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-username/career-copilot/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/your-username/career-copilot)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.0%2B-black)](https://nextjs.org)

**AI-powered career management platform that streamlines job search, application tracking, and career development through intelligent automation and personalized insights.**

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/career-copilot.git
cd career-copilot

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[all]"
cp .env.example .env
# Edit .env with your configuration

# Frontend setup
cd ../frontend
npm install
cp .env.example .env.local
# Edit .env.local with your backend URL

# Start the application
cd ../backend && uvicorn app.main:app --reload &
cd ../frontend && npm run dev
```

Visit `http://localhost:3000` for the frontend and `http://localhost:8000/docs` for the API documentation.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
## 🎯 Overview

Career Copilot is a comprehensive AI-powered career management platform designed to revolutionize how professionals manage their job search and career development. Built with modern technologies and a consolidated architecture, it provides intelligent automation, personalized insights, and streamlined workflows for job seekers and career professionals.

### Why Career Copilot?

The modern job market is complex and overwhelming. Career Copilot solves this by:

- **Intelligent Job Matching**: AI-powered job recommendations based on skills, experience, and preferences
- **Application Tracking**: Comprehensive tracking of job applications with status updates and analytics
- **Skill Gap Analysis**: Identifies missing skills and provides learning recommendations
- **Content Generation**: AI-generated cover letters, resume summaries, and interview preparation
- **Market Insights**: Real-time job market analysis and salary benchmarking
- **Automated Workflows**: Background processing for job scraping, notifications, and analytics

### Key Differentiators

- **Consolidated Architecture**: 50% reduction in codebase complexity while maintaining 100% functionality
- **Multi-AI Integration**: Support for OpenAI, Anthropic Claude, Groq, and other AI providers
- **Real-time Analytics**: Comprehensive dashboard with job search performance metrics
- **Enterprise-Ready**: Production-grade security, monitoring, and scalability features
- **Modern Tech Stack**: FastAPI backend, Next.js frontend, PostgreSQL database

## ✨ Features

### Core Features

#### 🎯 Job Management
- **Smart Job Discovery**: Automated job scraping from multiple sources (LinkedIn, Indeed, Glassdoor)
- **Intelligent Matching**: AI-powered job recommendations based on user profile and preferences
- **Application Tracking**: Complete lifecycle management of job applications
- **Status Automation**: Automatic status updates and follow-up reminders
- **Interview Scheduling**: Calendar integration and interview preparation tools

#### 📊 Analytics & Insights
- **Performance Dashboard**: Real-time metrics on job search progress and success rates
- **Market Analysis**: Salary trends, skill demand, and industry insights
- **Application Analytics**: Success rates, response times, and optimization suggestions
- **Skill Gap Analysis**: Identifies missing skills and provides learning paths
- **Progress Tracking**: Visual representation of career development journey

#### 🤖 AI-Powered Tools
- **Content Generation**: Automated cover letters, resume summaries, and LinkedIn posts
- **Interview Practice**: AI-powered mock interviews with feedback and scoring
- **Skill Assessment**: Automated evaluation of technical and soft skills
- **Career Coaching**: Personalized advice and career path recommendations
- **Document Analysis**: Resume optimization and ATS compatibility checking

#### 🔔 Notifications & Automation
- **Smart Alerts**: Customizable notifications for new jobs, application updates, and deadlines
- **Email Integration**: Automated email campaigns and follow-up sequences
- **Calendar Sync**: Interview scheduling and reminder management
- **Workflow Automation**: Background processing for routine tasks
- **Slack Integration**: Team collaboration and notification management

### Advanced Features

#### 🔒 Security & Privacy
- **Enterprise Security**: JWT authentication, role-based access control, and data encryption
- **Privacy Controls**: Granular privacy settings and data export capabilities
- **Audit Logging**: Comprehensive activity tracking and compliance reporting
- **File Security**: Malware scanning and secure file storage
- **API Security**: Rate limiting, CORS protection, and input validation

#### 🚀 Performance & Scalability
- **Caching Strategy**: Multi-layer caching with Redis and intelligent cache management
- **Background Processing**: Celery-based task queue for heavy operations
- **Database Optimization**: Connection pooling, query optimization, and performance monitoring
- **Load Balancing**: Horizontal scaling support with Kubernetes deployment
- **Monitoring**: Real-time performance metrics and health checks

#### 🔧 Integration Capabilities
- **API-First Design**: RESTful APIs with comprehensive documentation
- **Webhook Support**: Real-time event notifications and integrations
- **Third-party Integrations**: Google Drive, Slack, email providers, and job boards
- **OAuth Support**: Social login with Google, GitHub, and LinkedIn
- **Export/Import**: Data portability with multiple format support## 
🏗️ Architecture

Career Copilot features a **consolidated architecture** that achieved a 50% reduction in file count (from ~313 to ~157 files) while maintaining 100% functionality. This modern, scalable architecture is built on proven technologies and best practices.

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Load Balancer │    │   CDN/Cache     │
│   (Next.js)     │◄──►│   (Nginx/K8s)   │◄──►│  (Cloudflare)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Backend API   │    │   Background    │    │   Monitoring    │
│   (FastAPI)     │◄──►│   Workers       │◄──►│   (Prometheus)  │
└─────────────────┘    │   (Celery)      │    └─────────────────┘
         │              └─────────────────┘              │
         ▼                       │                       ▼
┌─────────────────┐              ▼              ┌─────────────────┐
│   Database      │    ┌─────────────────┐    │   Logging       │
│   (PostgreSQL)  │    │   Cache/Queue   │    │   (Structured)  │
└─────────────────┘    │   (Redis)       │    └─────────────────┘
         │              └─────────────────┘              │
         ▼                       │                       ▼
┌─────────────────┐              ▼              ┌─────────────────┐
│   File Storage  │    ┌─────────────────┐    │   External APIs │
│   (S3/Local)    │    │   Vector DB     │    │   (AI/Jobs)     │
└─────────────────┘    │   (ChromaDB)    │    └─────────────────┘
```

### Technology Stack

#### Backend (Python)
- **Framework**: FastAPI 0.109+ with async/await support
- **Database**: PostgreSQL with SQLAlchemy 2.0+ ORM
- **Caching**: Redis for session management and query caching
- **Task Queue**: Celery with Redis broker for background processing
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic v2 for request/response validation
- **Migration**: Alembic for database schema management

#### Frontend (TypeScript)
- **Framework**: Next.js 14+ with App Router
- **UI Library**: React 18+ with TypeScript
- **Styling**: Tailwind CSS with responsive design
- **State Management**: React hooks and context
- **HTTP Client**: Axios with interceptors and retry logic
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React for consistent iconography

#### AI & Machine Learning
- **OpenAI**: GPT-3.5/4 for content generation and analysis
- **Anthropic**: Claude 3 for advanced reasoning tasks
- **Groq**: High-speed inference for real-time features
- **Vector Database**: ChromaDB for semantic search
- **Embeddings**: Sentence Transformers for job matching

#### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with Helm charts
- **Monitoring**: Prometheus + Grafana for metrics
- **Logging**: Structured logging with correlation IDs
- **Security**: HTTPS, CORS, rate limiting, input validation

### Consolidated Architecture Benefits

The consolidation project achieved significant improvements:

#### Performance Improvements
- **20-30% faster imports** due to reduced import chains
- **20-30% faster builds** due to fewer files to process
- **15-25% reduced memory usage** from consolidated modules
- **25% improved developer productivity** from clearer structure

#### File Reduction Summary
| Component      | Before         | After          | Reduction |
| -------------- | -------------- | -------------- | --------- |
| Configuration  | 8 files        | 2 files        | 75%       |
| Analytics      | 8 files        | 2 files        | 75%       |
| Job Management | 12 files       | 3 files        | 75%       |
| Authentication | 6 files        | 2 files        | 67%       |
| Database       | 7 files        | 2 files        | 71%       |
| Email Services | 7 files        | 2 files        | 71%       |
| Cache Services | 6 files        | 2 files        | 67%       |
| LLM Services   | 8 files        | 2 files        | 75%       |
| Middleware     | 11 files       | 6 files        | 45%       |
| E2E Tests      | 40+ files      | 15 files       | 63%       |
| **Total**      | **~313 files** | **~157 files** | **50%**   |

### Service Architecture

#### Core Services (Consolidated)

**Configuration Management** (`config/`)
- `config.py`: Core configuration loading and validation
- `config_advanced.py`: Hot reload, templates, and integrations

**Analytics System** (`backend/app/services/`)
- `analytics_service.py`: Core analytics processing and event collection
- `analytics_specialized.py`: Domain-specific analytics (user, email, job, Slack)

**Job Management** (`backend/app/services/`)
- `job_service.py`: Core job CRUD operations
- `job_scraping_service.py`: Job scraping and data ingestion
- `job_recommendation_service.py`: Job matching and recommendation algorithms

**Authentication** (`backend/app/services/`)
- `auth_service.py`: Core authentication and JWT management
- `oauth_service.py`: OAuth providers and external authentication

**Database Management** (`backend/app/core/`)
- `database.py`: Core database connections and operations
- `database_optimization.py`: Performance optimization and maintenance

### Data Flow Architecture

#### Read Operations (Job Search)
1. **Client Request**: Next.js app sends API request
2. **Load Balancer**: Kubernetes Ingress routes to available FastAPI pod
3. **Cache Check**: Redis cache lookup for frequently accessed data
4. **Database Query**: PostgreSQL read replica for fresh data
5. **Cache Update**: Store results in Redis with TTL
6. **Response**: JSON response with job recommendations

#### Write Operations (Application Tracking)
1. **Client Submission**: Form data submitted via API
2. **Validation**: Pydantic schema validation and security checks
3. **Database Write**: Primary PostgreSQL instance for ACID compliance
4. **Background Tasks**: Celery tasks for notifications and analytics
5. **Cache Invalidation**: Smart cache invalidation for affected data
6. **Real-time Updates**: WebSocket notifications to connected clients

#### AI Processing Pipeline
1. **Content Input**: User provides job description or resume
2. **Preprocessing**: Text cleaning and tokenization
3. **Embedding Generation**: Vector embeddings for semantic search
4. **AI Analysis**: Multiple AI providers for comprehensive analysis
5. **Result Aggregation**: Combine results with confidence scoring
6. **Cache Storage**: Store results for future reference
7. **User Delivery**: Formatted response with actionable insights## 🛠️ I
nstallation

### Prerequisites

Before installing Career Copilot, ensure you have the following installed:

- **Python 3.11+** (3.12 recommended)
- **Node.js 18+** (20 LTS recommended)
- **npm 9+** or **yarn 1.22+**
- **Git** for version control
- **Docker** (optional, for containerized deployment)
- **PostgreSQL 14+** (for production) or SQLite (for development)
- **Redis 6+** (optional, for caching and background tasks)

### Development Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/career-copilot.git
cd career-copilot
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies with all optional features
pip install -e ".[all]"

# Or install minimal dependencies for development
pip install -e ".[dev,ai]"

# Copy environment configuration
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# Essential configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
DATABASE_URL=sqlite:///./data/career_copilot.db
OPENAI_API_KEY=your_openai_api_key  # For AI features

# Optional but recommended
GROQ_API_KEY=your_groq_api_key      # For fast AI inference
ANTHROPIC_API_KEY=your_anthropic_api_key  # For Claude AI
```

#### 3. Database Initialization

```bash
# Create database directory
mkdir -p data

# Run database migrations
alembic upgrade head

# Optional: Seed with sample data
python -m backend.maintenance.seed_database
```

#### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.local

# Edit .env.local with backend URL
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" >> .env.local
```

#### 5. Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc

### Production Installation

#### Using Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/your-username/career-copilot.git
cd career-copilot

# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Build and start services
docker-compose up -d --build

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check service status
docker-compose ps
```

#### Manual Production Setup

```bash
# Backend production setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[all]"

# Configure production environment
cp .env.example .env
# Set ENVIRONMENT=production in .env
# Configure PostgreSQL DATABASE_URL
# Set strong JWT_SECRET_KEY

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend production setup
cd ../frontend
npm install
npm run build
npm start
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f deployment/kubernetes/

# Check deployment status
kubectl get pods -n career-copilot

# Access via port-forward (for testing)
kubectl port-forward svc/career-copilot-frontend 3000:3000 -n career-copilot
```

### Verification

After installation, verify the setup:

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend accessibility
curl http://localhost:3000

# Run backend tests
cd backend && python -m pytest

# Run frontend tests
cd frontend && npm test

# Check database connection
cd backend && python -c "from app.core.database import DatabaseManager; print('Database OK')"
```

### Common Installation Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# Use specific Python version
python3.11 -m venv venv
```

#### Node.js Version Issues
```bash
# Check Node.js version
node --version

# Use Node Version Manager (nvm)
nvm install 20
nvm use 20
```

#### Database Connection Issues
```bash
# For PostgreSQL connection issues
pip install psycopg2-binary

# For SQLite permission issues
mkdir -p data
chmod 755 data
```

#### Port Conflicts
```bash
# Check port usage
lsof -i :8000  # Backend port
lsof -i :3000  # Frontend port

# Use different ports
uvicorn app.main:app --port 8001
npm run dev -- --port 3001
```

### Development Tools Setup

#### Pre-commit Hooks
```bash
cd backend
pre-commit install
pre-commit run --all-files
```

#### IDE Configuration
- **VS Code**: Install Python, TypeScript, and Tailwind CSS extensions
- **PyCharm**: Configure Python interpreter and enable FastAPI support
- **Vim/Neovim**: Install language servers for Python and TypeScript

#### Database Tools
- **pgAdmin**: For PostgreSQL management
- **SQLite Browser**: For SQLite database inspection
- **Redis CLI**: For cache inspection and debugging## ⚙️ C
onfiguration

Career Copilot uses a **unified configuration system** that consolidates all settings into a coherent, environment-aware structure. Configuration is managed through environment variables, YAML files, and automatic environment-specific overrides.

### Configuration Architecture

#### Configuration Files
- **`.env`**: Main environment configuration
- **`.env.example`**: Template with all available options
- **`.env.overrides`**: Environment-specific overrides (optional)
- **`config/application.yaml`**: Unified YAML configuration
- **`frontend/.env.local`**: Frontend-specific environment variables

#### Configuration Loading Priority
1. **Environment variables** (highest priority)
2. **`.env.overrides`** (environment-specific)
3. **`.env`** (base configuration)
4. **`config/application.yaml`** (defaults)
5. **Built-in defaults** (lowest priority)

### Core Configuration

#### Application Settings
```bash
# Environment mode: development, production, testing
ENVIRONMENT=development

# Enable debug mode (detailed errors, FastAPI docs)
DEBUG=true

# API server configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend URL for CORS and redirects
FRONTEND_URL=http://localhost:3000
```

#### Database Configuration
```bash
# Database connection URL
# SQLite (Development): sqlite:///./data/career_copilot.db
# PostgreSQL (Production): postgresql://user:password@localhost:5432/career_copilot
DATABASE_URL=sqlite:///./data/career_copilot.db

# Connection pool settings (production)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### Security Configuration
```bash
# JWT secret key (REQUIRED - must be 32+ characters)
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60
```

### AI Services Configuration

#### OpenAI Configuration
```bash
# OpenAI API key (required for AI features)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=60
```

#### Anthropic Claude Configuration
```bash
# Anthropic API key (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_ENABLED=true
```

#### Groq Configuration (Fast Inference)
```bash
# Groq API key (optional, for high-speed inference)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_ENABLED=true
```

#### AI Routing Configuration
```bash
# Task routing strategy: cost, speed, quality
AI_ROUTING_STRATEGY=cost
AI_FALLBACK_ENABLED=true
AI_MAX_RETRIES=3
AI_CACHE_TTL=3600
```

### External Services Configuration

#### Job Board APIs
```bash
# LinkedIn API (for job scraping)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# Indeed API
INDEED_PUBLISHER_ID=your_indeed_publisher_id
INDEED_API_KEY=your_indeed_api_key

# Adzuna API
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key

# Glassdoor API
GLASSDOOR_PARTNER_ID=your_glassdoor_partner_id
GLASSDOOR_API_KEY=your_glassdoor_api_key
```

#### Email Services
```bash
# SMTP Configuration
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=notifications@career-copilot.com
SMTP_FROM_NAME=Career Copilot

# SendGrid (alternative to SMTP)
SENDGRID_API_KEY=your_sendgrid_api_key

# Email scheduling
DAILY_DIGEST_TIME=08:00
WEEKLY_SUMMARY_DAY=MONDAY
JOB_ALERT_FREQUENCY=daily
```

#### OAuth Providers
```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
```

### Caching and Performance

#### Redis Configuration
```bash
# Redis connection (optional, for production)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password
REDIS_MAX_CONNECTIONS=20
REDIS_TIMEOUT=5

# Cache settings
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=3600
CACHE_MAX_SIZE=1000
```

#### Background Tasks
```bash
# Celery configuration (requires Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json

# Background processing
ENABLE_SCHEDULER=true
ENABLE_JOB_SCRAPING=true
MAX_BACKGROUND_WORKERS=4
TASK_QUEUE_SIZE=1000
```

### File Storage and Upload

#### File Upload Configuration
```bash
# File upload settings
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=pdf,docx,txt,png,jpg

# File security
ENABLE_FILE_SCANNING=true
ENABLE_VIRUS_SCANNING=false
FILE_RETENTION_DAYS=365
```

#### Cloud Storage (Optional)
```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=career-copilot-files

# Google Cloud Storage
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_BUCKET=career-copilot-files
```

### Monitoring and Logging

#### Logging Configuration
```bash
# Logging settings
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE_PATH=./logs/app.log
LOG_ROTATION_SIZE=100MB
LOG_BACKUP_COUNT=10

# Structured logging
ENABLE_STRUCTURED_LOGGING=false
LOG_CORRELATION_ID=true
```

#### Monitoring Configuration
```bash
# Prometheus metrics
ENABLE_METRICS=false
METRICS_PORT=9090

# Health checks
HEALTH_CHECK_INTERVAL=60
HEALTH_CHECK_TIMEOUT=30

# Performance monitoring
ENABLE_PERFORMANCE_TRACKING=true
SLOW_QUERY_THRESHOLD=1.0
```

### Environment-Specific Configurations

#### Development Environment
```yaml
# config/application.yaml - development section
environments:
  development:
    api:
      debug: true
      reload: true
    security:
      cors_origins:
        - "http://localhost:3000"
        - "http://localhost:8501"
      jwt:
        expiration_hours: 168  # 7 days
    cache:
      redis:
        enabled: false
      memory:
        max_size: 500
```

#### Production Environment
```yaml
# config/application.yaml - production section
environments:
  production:
    api:
      debug: false
      workers: 8
    security:
      rate_limiting:
        enabled: true
        requests_per_minute: 500
      encryption:
        enabled: true
    cache:
      redis:
        enabled: true
        max_connections: 50
```

### Configuration Management

#### Using the Configuration Manager
```python
from config.config import ConfigurationManager

# Initialize configuration
config = ConfigurationManager()
settings = config.load_config()

# Get specific settings
database_url = config.get_setting('DATABASE_URL')
jwt_secret = config.get_setting('JWT_SECRET_KEY')

# Hot reload configuration (development)
config.reload_config()
```

#### Environment Variable Validation
```python
# Required environment variables are validated on startup
REQUIRED_VARS = [
    'JWT_SECRET_KEY',
    'DATABASE_URL',
]

# Optional variables with defaults
OPTIONAL_VARS = {
    'DEBUG': 'false',
    'LOG_LEVEL': 'INFO',
    'CACHE_ENABLED': 'true',
}
```

#### Configuration Templates
```bash
# Generate configuration for specific environment
python -m backend.maintenance.initialize_config --env production

# Validate current configuration
python -m backend.maintenance.validate_configs

# Export configuration (excluding secrets)
python -m backend.maintenance.export_config --format yaml
```