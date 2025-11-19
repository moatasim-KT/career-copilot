
# 🚀 Career Copilot

---
## 🧭 Quick Navigation

- [[PLAN]] – Project Plan
- [[TESTING_AND_UI_REFACTORING_OVERVIEW]] – Testing & UI Refactoring Overview
- [[COMPONENT_LIBRARY_INVENTORY.md]] – Component Inventory
- [[DESIGN_SYSTEM.md]] – Design System Guide
- [[ERROR_HANDLING_GUIDE.md]] – Error Handling Guide
- [[E2E_TESTING_MIGRATION.md]] – E2E Testing Migration Guide
- [[docs/DEVELOPER_GUIDE]] – Developer Guide
- [[TODO.md]] – Todo List
- [[FRONTEND_QUICK_START.md]] – Frontend Quick Start
- [[USER_GUIDE.md]] – User Guide
- [[ENVIRONMENT_CONFIGURATION.md]] – Environment Configuration
---

## 🚀 Key Entry Points

**Backend**: [[backend/app/main.py|FastAPI Main App]]
**Frontend**: [[frontend/src/app/layout.tsx|Next.js Layout]] | [[frontend/src/app/page.tsx|Home Page]]
**Scripts**: [[scripts/README.md|Scripts Directory]]

## ⚙️ Key Configuration Files

**Backend**: [[backend/pyproject.toml|Backend Config]] | [[config/llm_config.json|LLM Config]] | [[config/application.yaml|App Config]]
**Frontend**: [[frontend/package.json|Frontend Config]] | [[frontend/tsconfig.json|TypeScript Config]] | [[frontend/tailwind.config.ts|Tailwind Config]]
**Project**: [[config/feature_flags.json|Feature Flags]] | [[docker-compose.yml|Docker Compose]]

## 📚 Core Documentation
>
> An intelligent job search assistant specializing in EU opportunities with visa sponsorship support for AI/Data Science professionals

**💰 100% FREE to run!** No credit card required - see [[FREE_TIER_SETUP|Free Tier Setup Guide]]


**Quick Links**: [[LOCAL_SETUP.md]] | [[FREE_TIER_SETUP.md]] | [[PROJECT_STATUS.md]] | [[docs/index.md]] | [[CONTRIBUTING.md]]

**Documentation**:
- [[FREE_TIER_SETUP|🆓 Free Tier Setup]] - **Zero-cost deployment guide** (5 minutes!)
- [[docs/USER_GUIDE|User Guide]] - User guide and tutorials
- [[DEVELOPER_GUIDE|Developer Guide]] - Developer documentation
- [[docs/architecture/ARCHITECTURE|Architecture]] - System architecture
- [[docs/api/API|API Reference]] - API reference
- [[backend/README|Backend Guide]] - Backend guide
- [[frontend/README|Frontend Guide]] - Frontend guide

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

#### 📅 **Calendar Integration** ✨ NEW
- **Two-way Sync**: Sync interviews with Google Calendar and Microsoft Outlook
- **Event Management**: Create, view, edit, and delete interview events
- **Multiple Views**: Month, week, and day calendar views
- **Automatic Reminders**: 15 minutes, 1 hour, or 1 day before events
- **Application Linking**: Connect events directly to job applications
- [📖 Calendar Integration Guide](docs/features/CALENDAR_INTEGRATION_GUIDE.md)

#### 🎛️ **Customizable Dashboard** ✨ NEW
- **8 Interactive Widgets**: Status overview, recent jobs, statistics, calendar, recommendations, activity timeline, skills progress, goals tracker
- **Drag-and-Drop**: Rearrange widgets to match your workflow
- **Resizable Widgets**: Adjust sizes for your preferred layout
- **Layout Persistence**: Your custom layout saves automatically
- **Responsive Design**: Adapts to desktop, tablet, and mobile
- [📖 Dashboard Customization Guide](docs/features/DASHBOARD_CUSTOMIZATION_GUIDE.md)

#### 🔐 **Authentication & Security** ✨ NEW
- **Single-User Mode**: Perfect for personal deployment (default)
- **Default Credentials**: `user@career-copilot.local` / `changeme123`
- **Secure JWT Tokens**: Industry-standard authentication
- **Multi-User Support**: Optional for team deployments
- **Password Security**: Bcrypt hashing with configurable rounds

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

### 🚀 Quick Start

**For free deployment** (recommended): See [[FREE_TIER_SETUP|🆓 Free Tier Setup Guide]] - 5 minutes, $0/month

**For full setup**: See [[LOCAL_SETUP|Local Setup Guide]] - Complete guide with all features

#### Option 1: Free Tier (Zero Cost) ⭐

```bash
# 1. Clone repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Copy free tier configuration
cp .env.free-tier-example .env

# 3. Get FREE Groq API key (no credit card)
# Visit: https://console.groq.com/keys
# Edit .env and add your key to GROQ_API_KEY

# 4. Generate security keys and add to .env
openssl rand -hex 32  # Add to SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"  # Add to JWT_SECRET_KEY

# 5. Start services
docker-compose up -d
docker-compose exec backend alembic upgrade head

# 6. Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8002/docs
```

**💰 Monthly Cost: $0.00** - Full features with free services!

#### Option 2: Full Setup (With Paid Services)

```bash
# 1-3: Clone, configure .env files
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot
cp .env.example .env
# Edit .env with your API keys (OpenAI, etc.)

# 4. Start all services with Docker
docker-compose up -d

# 5. Initialize the database
docker-compose exec backend alembic upgrade head

# 6. Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8002/docs
```

For detailed setup, architecture, and troubleshooting: [[LOCAL_SETUP|Local Setup Guide]]

---

### 💰 Cost Breakdown

#### Free Tier (Recommended for Personal Use)

| Component         | Service             | Cost            | Notes               |
| ----------------- | ------------------- | --------------- | ------------------- |
| **Database**      | PostgreSQL (Docker) | $0.00           | Runs locally        |
| **Cache**         | Redis (Docker)      | $0.00           | Runs locally        |
| **AI Provider**   | Groq                | $0.00           | 14,400 requests/day |
| **Job Scraping**  | Web Scraping        | $0.00           | 12+ job boards      |
| **Job APIs**      | Adzuna + 4 others   | $0.00           | All have free tiers |
| **Notifications** | Console/Gmail/Slack | $0.00           | Optional            |
| **Total**         |                     | **$0.00/month** | ✨                   |

**What you get for free:**
- ✅ All core features
- ✅ 14,400 AI requests/day (Groq - more than enough for personal use)
- ✅ Unlimited job tracking
- ✅ Automatic job scraping (12+ boards via web scraping)
- ✅ **BONUS**: 5 FREE job board APIs:
  - Adzuna (1,000 calls/month - 22 countries)
  - RapidAPI JSearch (1,000 requests/month - aggregates Google Jobs)
  - The Muse (500/hour - curated jobs)
  - Remotive (unlimited - remote jobs)
  - RemoteOK (unlimited - 100k+ remote jobs)
- ✅ AI resume generation & cover letters
- ✅ Job recommendations & skill analysis
- ✅ **Total**: 50,000+ job postings/month for FREE!

#### Optional Paid Services (For Enhanced Features)

| Component       | Service          | Cost            | When You Need It      |
| --------------- | ---------------- | --------------- | --------------------- |
| **AI Provider** | OpenAI GPT-4     | $5-15/1M tokens | Advanced reasoning    |
| **AI Provider** | Anthropic Claude | $3-15/1M tokens | Complex writing       |
| **Email**       | SendGrid         | Free-$15/mo     | >100 emails/day       |
| **Monitoring**  | Sentry           | Free-$26/mo     | Production deployment |
| **Job APIs**    | Various          | Free tiers      | API rate limits       |

**Typical monthly cost for single user with free tier: $0.00**
**Typical monthly cost with paid AI: $5-20** (if you generate 100+ resumes/month)

---

### 📋 Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM, 10GB disk space
- API keys: OpenAI OR Anthropic (for AI features)

## 📚 Documentation

**Start here**: [[LOCAL_SETUP]] - Complete local development guide with code references

### Core Documentation
- **Local Setup**: [[LOCAL_SETUP]] - Docker, configuration, troubleshooting, architecture
- **Testing**: [[backend/tests/TESTING_NOTES|Testing Notes]] - Test infrastructure and known issues
- **Coding Standards**: [[.github/copilot-instructions|Copilot Instructions]] - Project conventions and patterns
- **API Reference**: http://localhost:8000/docs (OpenAPI, when backend running)
- **Documentation Hub**: [[docs/index|Documentation Hub]] - Central documentation index

- **[[docs/deployment/DEPLOYMENT|Deployment Guide]]** - Production deployment instructions
  - Docker Compose deployment
  - Kubernetes deployment
  - Cloud platforms (AWS, GCP, Render, etc.)

### 🔧 Troubleshooting

- **[[docs/troubleshooting/COMMON_ISSUES|Common Issues]]** - Solutions to common problems
  - Installation issues
  - API troubleshooting
  - Performance optimization

## 🛠️ Technology Stack

### Backend

- **Framework**: FastAPI 0.109+ (Python 3.11+)
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0 ORM
- **Cache & Message Broker**: Redis 7+
- **Task Queue**: Celery 5.3+ with Redis backend
- **AI/ML**: 
  - **Multi-Provider LLM**: OpenAI GPT-4, Anthropic Claude, Groq (intelligent routing) → [[backend/app/services/llm_service.py|LLM Service]]
  - **Vector Database**: ChromaDB for embeddings and semantic search → [[backend/app/services/vector_store_service.py|Vector Store]]
  - **Content Generation**: Resume & cover letter AI generation
  - **Job Matching**: AI-powered job recommendations with skill analysis
- **Web Scraping**: BeautifulSoup4, Selenium, Playwright
- **Authentication**: JWT tokens with bcrypt password hashing
- **Job Preview API**: `/api/v1/jobs/available` returns lightweight `JobPreview` cards for onboarding widgets and personalization flows.
- **Recommendation Feedback API**: `/api/v1/recommendations/{job_id}/feedback` accepts thumbs up/down payloads (`is_positive`, optional `reason`) aligned with the new frontend client.
- **Credential Auth Flow**: `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/logout`, and `/api/v1/auth/me` expose the simplified username/email + password flow used by the React AuthContext.
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

See [Quick Start](#-quick-start) above for initial setup.

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
npm run test:a11y

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
- **JWT & RBAC**: All `/api/v1` routes now validate `Authorization: Bearer <token>` headers issued by `/auth/login` unless `DISABLE_AUTH=true` (dev only). Use `JWT_SECRET_KEY`, `JWT_ALGORITHM`, and `JWT_EXPIRATION_HOURS` to tune cryptography and expiration, and set `DISABLE_AUTH=false` for staging/production to enforce RBAC via `User.is_admin`.
- **Dependency & SAST Scanning**: `make security` now runs Bandit, Safety (`reports/safety-report.json`), `pip-audit` (`reports/pip_audit_report.json`), Semgrep SAST (`reports/semgrep-report.json`), and `npm audit --audit-level=high` (`reports/npm_audit_report.json`).
- **Manual Run**:
  ```bash
  make security
  ```
  Install the dev extras (`pip install -e .[dev,ai,all]`) for Bandit/Safety/pip-audit and use `pipx install semgrep` (or `pip install semgrep` inside a virtualenv) to enable the SAST step locally.

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

See [[TODO]] for the current phase-by-phase roadmap.

**Other Features In Development**:
- 🔄 Multi-user authentication system
- 🔄 Real-time notifications (WebSocket)
- 🔄 Advanced analytics & reporting
- 🔄 Mobile application
- 🔄 Interview preparation tools

## 🤝 Contributing

We welcome contributions! Please see our [[CONTRIBUTING|Contributing Guide]] for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
6. Run `make quality-check` before submitting to catch issues early

**Coordination Guidelines**:
- Review [[TODO]] before starting work to avoid duplicate efforts
- Record decisions or progress in [[TODO]] / [[PROJECT_STATUS]] or the associated issue
- Keep changes scoped per task and link to the relevant section in PR summaries
- Follow branching strategy: `feature/*`, `fix/*`, `docs/*`, `chore/*`

### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting
- **TypeScript**: Follow project ESLint configuration
- **React**: Use functional components, TypeScript interfaces, proper prop typing
- **Design System**: Use tokens from `globals.css`, follow Button2/Card2 patterns
- **Commits**: Use conventional commits format (`feat:`, `fix:`, `docs:`, etc.)

## 🔗 Project Links

- [[TODO]] - Current development tasks and progress
- [[PLAN]] - Implementation plan and roadmap
- [[RESEARCH]] - Research findings and analysis
- [[CHANGELOG]] - Version history and changes
- [[CONTRIBUTING]] - Contribution guidelines
- [[DEVELOPER_GUIDE|Developer Guide]] - Comprehensive development documentation
- [[docs/USER_GUIDE|User Guide]] - User documentation and tutorials
- [[docs/FRONTEND_QUICK_START|Frontend Quick Start]] - Frontend development setup

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support & Contact

- **Email**: <moatasimfarooque@gmail.com>
- **GitHub Issues**: [Report bugs or request features](https://github.com/moatasim-KT/career-copilot/issues)
