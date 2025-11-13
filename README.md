# 🚀 Career Copilot

> **AI-Powered Career Management Platform for EU Tech Jobs**
>
> An intelligent job search assistant specializing in EU opportunities with visa sponsorship support for AI/Data Science professionals

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-dc382d.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](VERSION)

---

## 📸 Screenshots

<div align="center">

### Dashboard Overview
![Dashboard](docs/images/screenshots/dashboard.png)
*Comprehensive dashboard with application tracking, analytics, and job recommendations*

### Job Search & Discovery
![Job Search](docs/images/screenshots/job-search.png)
*Advanced search with filters, saved searches, and AI-powered recommendations*

### Application Tracking
![Applications](docs/images/screenshots/applications.png)
*Track all your applications with status updates and timeline view*

### AI-Powered Resume Generation
![Resume Builder](docs/images/screenshots/resume-builder.png)
*Generate tailored resumes optimized for specific job postings*

</div>

---

## ✨ What is Career Copilot?

Career Copilot is a comprehensive AI-powered platform that revolutionizes the job search process for tech professionals targeting the European market. It combines intelligent job scraping, AI-driven content generation, advanced application tracking, and real-time analytics to streamline your entire career journey from job discovery to offer acceptance.

### 🎯 Key Features

#### 🔍 **Intelligent Job Discovery**
- Automated scraping from 9 major job boards (LinkedIn, Indeed, StepStone, Glassdoor, etc.)
- Advanced search with complex filters (AND/OR logic, nested conditions)
- Saved searches with automatic alerts
- Command palette (⌘K) for instant navigation and search
- Real-time job recommendations via WebSocket

#### 📝 **AI-Powered Content Generation**
- Tailored resumes optimized for specific job postings using GPT-4/Claude
- Personalized cover letters highlighting relevant experience
- Skills gap analysis and recommendations
- Interview preparation assistance

#### 📊 **Comprehensive Application Tracking**
- Kanban board view with drag-and-drop status updates
- Timeline view showing application progress
- Bulk operations (status updates, exports, deletions)
- Application analytics and success rate tracking
- Automated status change notifications

#### 🎯 **Smart Job Matching**
- AI-powered recommendations based on profile and preferences
- Skills demand analysis with market insights
- Salary distribution visualization
- Company culture matching

#### 📈 **Advanced Analytics & Insights**
- Interactive charts (application status, timeline, salary distribution)
- Success rate funnel analysis
- Response time tracking
- Market trend analysis
- Exportable reports (CSV, PDF)

#### 🔔 **Real-Time Notifications**
- WebSocket-powered instant updates
- Browser push notifications
- Email digests (immediate, daily, weekly)
- Customizable notification preferences per category
- In-app notification center with history

#### 🎨 **Modern User Experience**
- Beautiful dark mode with smooth transitions
- Responsive design (mobile, tablet, desktop)
- Smooth animations and micro-interactions
- Accessibility compliant (WCAG 2.1 AA)
- Onboarding wizard for new users

#### 🌍 **EU Market Specialization**
- Visa sponsorship support tracking
- Multi-country job search
- EU work permit guidance
- Salary comparison across EU countries

### 🚀 Quick Start (5 Minutes)

#### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. Add your API keys to .env files
# Required: OPENAI_API_KEY or ANTHROPIC_API_KEY

# 4. Start all services with Docker
docker-compose up -d

# 5. Initialize the database
docker-compose exec backend alembic upgrade head

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3001
```

That's it! The application is now running with all services configured.

#### Option 2: Local Development

```bash
# 1. Clone and setup
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
alembic upgrade head

# 3. Start backend services (separate terminals)
uvicorn app.main:app --reload --port 8000
celery -A app.celery worker --loglevel=info
celery -A app.celery beat --loglevel=info

# 4. Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### 📋 Prerequisites

#### For Docker Deployment (Recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

#### For Local Development
- **Backend**:
  - Python 3.11+
  - PostgreSQL 14+
  - Redis 7+
- **Frontend**:
  - Node.js 18.0+ (LTS recommended)
  - npm 9+ or pnpm 8+
- **AI Services**:
  - OpenAI API key (GPT-4 access) OR
  - Anthropic API key (Claude access)

## 📚 Documentation

Comprehensive documentation is available in the [[docs/index.md|docs/]] directory.

### 🤖 AI Agent Coordination (New!)

- **[Quick Start for Contributors](.agents/START_HERE.md)** - Immediate action steps with examples
- **[Coordination System Overview](.agents/README.md)** - Complete guide to multi-agent development
- **[Coordination Rules](.agents/coordination-rules.md)** - File locking, branching, and conflict prevention
- **[Task Assignments](.agents/task-partition-plan.md)** - Detailed task breakdown (18 Gemini + 16 Copilot tasks)
- **[Real-Time Status](.agents/task-assignments.json)** - Live agent state and progress tracking

### � Documentation Hub

For complete documentation, visit the [[docs/index.md|Documentation Index]] which provides organized access to all guides, API references, and technical documentation.

- **[Deployment Guide](docs/deployment/DEPLOYMENT.md)** - Production deployment instructions
- **[Docker Deployment](docs/deployment/DEPLOYMENT.md#docker-compose-deployment)** - Deploy with Docker Compose
- **[Kubernetes](docs/deployment/DEPLOYMENT.md#kubernetes-deployment)** - Deploy to Kubernetes
- **[Cloud Platforms](docs/deployment/DEPLOYMENT.md#cloud-platform-deployment)** - AWS, GCP, Render, etc.

### 🔧 Troubleshooting

- **[Common Issues](docs/troubleshooting/COMMON_ISSUES.md)** - Solutions to common problems
- **[Installation Issues](docs/troubleshooting/COMMON_ISSUES.md#installation-issues)** - Setup problems
- **[API Issues](docs/troubleshooting/COMMON_ISSUES.md#api-issues)** - API troubleshooting
- **[Performance](docs/troubleshooting/COMMON_ISSUES.md#performance-issues)** - Performance optimization

## 🛠️ Technology Stack

### Backend

- **Framework**: FastAPI 0.109+ (Python 3.11+)
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0 ORM
- **Cache & Message Broker**: Redis 7+
- **Task Queue**: Celery 5.3+ with Redis backend
- **AI/ML**: 
  - OpenAI GPT-4 for content generation
  - Anthropic Claude for advanced reasoning
  - ChromaDB for vector embeddings and semantic search
- **Web Scraping**: BeautifulSoup4, Selenium, Playwright
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Documentation**: OpenAPI 3.0 (Swagger/ReDoc)

### Frontend

- **Framework**: Next.js 16.0 with App Router
- **UI Library**: React 18.3
- **Language**: TypeScript 5.0+
- **Styling**: 
  - Tailwind CSS 4.1 with custom design tokens
  - Framer Motion 12.23 for animations
- **UI Components**: 
  - Custom design system (Button2, Card2, Input suite)
  - Radix UI primitives
  - Lucide React icons
- **State Management**: 
  - TanStack Query 5.90 (server state)
  - Zustand 5.0 (client state)
  - React Hook Form 7.66 + Zod 4.1 (forms)
- **Data Visualization**: Recharts 3.3
- **Drag & Drop**: @dnd-kit 6.3
- **Command Palette**: cmdk 1.1
- **Virtualization**: @tanstack/react-virtual 3.13

### Infrastructure & DevOps

- **Containerization**: Docker & Docker Compose
- **Web Server**: Uvicorn (dev), Gunicorn (prod)
- **Reverse Proxy**: Nginx with SSL/TLS
- **Monitoring**: 
  - Sentry for error tracking
  - Prometheus + Grafana for metrics
  - Web Vitals for performance monitoring
- **CI/CD**: GitHub Actions
- **Testing**: 
  - Backend: pytest
  - Frontend: Jest, Playwright, Storybook
  - Lighthouse CI for performance audits

## 📁 Project Structure

```
career-copilot/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── core/           # Configuration & security
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helper functions
│   ├── alembic/            # Database migrations
│   └── tests/              # Backend tests
│
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities & API client
│   │   └── types/         # TypeScript types
│   └── tests/             # Frontend tests
│
├── docs/                   # Documentation
│   ├── setup/             # Installation & configuration
│   ├── architecture/      # System architecture
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   └── troubleshooting/   # Common issues & solutions
│
├── config/                 # Configuration files
│   ├── environments/      # Environment-specific configs
│   ├── services/          # Service configurations
│   └── llm_config.json    # AI provider configuration
│
├── deployment/             # Deployment configurations
│   ├── docker/            # Docker files
│   ├── k8s/               # Kubernetes manifests
│   └── nginx/             # Nginx configurations
│
├── data/                   # Application data
│   ├── databases/         # SQLite/test databases
│   ├── logs/              # Application logs
│   ├── uploads/           # User-uploaded files
│   ├── chroma/            # Vector database
│   └── backups/           # Database backups
│
├── scripts/                # Utility scripts
│   ├── database/          # Database scripts
│   ├── initialization/    # Setup scripts
│   └── verify/            # Verification scripts
│
├── docker-compose.yml      # Main Docker Compose file
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🚀 Deployment

### Production Deployment

#### Vercel (Frontend) + Render (Backend)

**Frontend (Vercel)**:
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy frontend
cd frontend
vercel --prod

# 3. Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

**Backend (Render)**:
1. Create new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
5. Add environment variables from `.env.example`
6. Add PostgreSQL and Redis services

#### Docker Compose (Self-Hosted)

```bash
# 1. Clone on production server
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Configure environment
cp .env.example .env
# Edit .env with production values

# 3. Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Initialize database
docker-compose exec backend alembic upgrade head

# 5. Setup SSL with Let's Encrypt
./scripts/setup-ssl.sh your-domain.com
```

#### Kubernetes

```bash
# 1. Apply configurations
kubectl apply -f deployment/k8s/namespace.yaml
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/secrets.yaml
kubectl apply -f deployment/k8s/

# 2. Check deployment status
kubectl get pods -n career-copilot
kubectl get services -n career-copilot
```

See [Deployment Guide](docs/deployment/DEPLOYMENT.md) for detailed instructions.

## 🔧 Development

### Local Development Setup

See [Quick Start](#-quick-start-5-minutes) above for initial setup.

### Development Workflow

```bash
# Start development environment
docker-compose up -d

# Watch logs
docker-compose logs -f backend frontend

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Stop services
docker-compose down
```

### Environment Variables

Create `.env` files from templates:

```bash
# Root
cp .env.example .env

# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env.local
```

**Required variables:**

```env
# AI Provider (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/career_copilot

# Redis
REDIS_URL=redis://localhost:6379/0
```

See [Configuration Guide](docs/setup/CONFIGURATION.md) for complete details.

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```

## 🌐 API Documentation

Interactive API documentation is available when the backend is running:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI Schema**: <http://localhost:8000/openapi.json>

See the complete [API Documentation](docs/api/API.md) for detailed endpoint information.

## 🔐 Security

- **Authentication**: JWT-based with access and refresh tokens
- **Authorization**: Role-Based Access Control (RBAC)
- **Data Protection**: Password hashing with bcrypt, SQL injection prevention
- **CORS**: Configurable Cross-Origin Resource Sharing
- **Rate Limiting**: API rate limiting to prevent abuse
- **SSL/TLS**: HTTPS support in production

See [Security Best Practices](docs/deployment/DEPLOYMENT.md#security) for more details.

## 📈 Current Status

**Version**: 1.0.0 (Production Ready)

**Core Platform Features**:
- ✅ Job scraping from 9 sources
- ✅ AI-powered resume generation
- ✅ Application tracking system
- ✅ User profile management
- ✅ Job recommendations
- ✅ Analytics dashboard
- ✅ Email notifications
- ✅ Docker deployment ready
- ✅ Comprehensive API (70+ endpoints)
- ✅ Single-user mode (User ID: 1)


**🎯 Phase 1: Enterprise Frontend Upgrade (COMPLETE)**

**Design System Foundation**:
- ✅ Complete design tokens in `globals.css` (5-level color palettes, spacing, typography, shadows)
- ✅ Button2 component (7 variants, 5 sizes)
- ✅ Card2 component (5 elevation levels)

**Migration Progress**:
- ✅ **Task 1.4 Complete** (6/6 files migrated)
  - Layout & navigation components
  - Dashboard & analytics
  - Forms & profile management
  - Settings & advanced features
  - Job tracking & AI-powered tools

**Copilot Phase 1 (Tasks 1.5–1.7):**
- ✅ 16 new enterprise components (Skeleton2, Input2, Select2, MultiSelect2, DatePicker2, FileUpload2, PasswordInput2, Textarea2, Modal2, Dialog2, Drawer2, AlertDialog2, and all skeleton variants) built, tested, and merged to main

**Main branch is now unified and up to date.**

See [TODO.md](TODO.md) for complete 320+ task breakdown across 6 phases.

**Other Features In Development**:
- 🔄 Multi-user authentication system
- 🔄 Real-time notifications (WebSocket)
- 🔄 Advanced analytics & reporting
- 🔄 Mobile application
- 🔄 Interview preparation tools

## � AI Agent Coordination

This project uses a **File-Level Task Partitioning** strategy for parallel development with multiple AI agents:

- **Gemini CLI**: Focused on migrations and architectural tasks (Task 1.4 ✅ complete)
- **GitHub Copilot**: Built and merged new components (Tasks 1.5–1.7 ✅ complete)
- **Zero-Conflict Design**: Each agent works on different files simultaneously
- **Git Workflow**: Dedicated branches (`agent/gemini/*`, `agent/copilot/*`) with daily integration

**For Contributors & AI Agents**:
- **Quick Start**: See [.agents/START_HERE.md](.agents/START_HERE.md) for immediate action steps
- **Coordination Rules**: [.agents/coordination-rules.md](.agents/coordination-rules.md)
- **Task Assignments**: [.agents/task-partition-plan.md](.agents/task-partition-plan.md)
- **Real-Time Status**: Run `.agents/shared/quick-status.sh`

**Benefits**:
- ⚡ 4-5x speedup (3-4 days vs 10-14 days)
- 🎯 Zero merge conflicts by design
- 💰 $0 cost (free tier AI tools only)
- 📊 Real-time progress tracking with JSON state

## �🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](frontend/CONTRIBUTING.md) for details.

### Development Workflow

**For Human Contributors**:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**For AI Agent Contributors**:
1. Read [.agents/START_HERE.md](.agents/START_HERE.md)
2. Check task assignments in [.agents/task-assignments.json](.agents/task-assignments.json)
3. Follow your agent-specific instructions (`.agents/gemini/` or `.agents/copilot/`)
4. Use designated branch (`agent/gemini/*` or `agent/copilot/*`)
5. Run sync checks before committing (`.agents/shared/sync-check.sh`)

### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting
- **TypeScript**: Follow project ESLint configuration
- **React**: Use functional components, TypeScript interfaces, proper prop typing
- **Design System**: Use tokens from `globals.css`, follow Button2/Card2 patterns
- **Commits**: Use conventional commits format (`feat:`, `fix:`, `docs:`, etc.)

## 🔗 Project Links

- [[TODO.md]] - Current development tasks and progress
- [[PLAN.md]] - Implementation plan and roadmap
- [[RESEARCH.md]] - Research findings and analysis
- [[CHANGELOG.md]] - Version history and changes
- [[./CONTRIBUTING.md]] - Contribution guidelines
- [[docs/DEVELOPER_GUIDE.md|Developer Guide]] - Comprehensive development documentation
- [[docs/USER_GUIDE.md|User Guide]] - User documentation and tutorials
- [[docs/FRONTEND_QUICK_START.md|Frontend Quick Start]] - Frontend development setup

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support & Contact

- **Email**: <moatasimfarooque@gmail.com>
- **GitHub Issues**: [Report bugs or request features](https://github.com/moatasim-KT/career-copilot/issues)
- **Documentation**: [Full documentation](docs/)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Next.js](https://nextjs.org/)
- AI capabilities by [OpenAI](https://openai.com/) and [Anthropic](https://anthropic.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)

---

<div align="center">

**[Documentation](docs/)** • **[API Reference](docs/api/API.md)** • **[Deployment](docs/deployment/DEPLOYMENT.md)** • **[Troubleshooting](docs/troubleshooting/COMMON_ISSUES.md)**

Made with ❤️ for job seekers in the EU tech market

</div>
