# 🚀 Career Copilot

> **AI-Powered Career Management Platform for EU Tech Jobs**
>
> An intelligent job search assistant specializing in EU opportunities with visa sponsorship support for AI/Data Science professionals

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-dc382d.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](VERSION)

---

## ✨ What is Career Copilot?

Career Copilot is an AI-powered platform that automates the job search process for tech professionals targeting the European market. It combines intelligent job scraping, AI-driven content generation, and comprehensive application tracking to streamline your career journey.

### 🎯 Key Features

- **🔍 Intelligent Job Discovery**: Automated scraping from 9 major job boards (LinkedIn, Indeed, StepStone, etc.)
- **📝 AI Resume Generation**: Tailored resumes optimized for specific job postings using GPT-4
- **✉️ Smart Cover Letters**: Personalized cover letters highlighting relevant experience
- **📊 Application Tracking**: Comprehensive dashboard to manage all applications in one place
- **🎯 Job Matching**: AI-powered job recommendations based on your profile and preferences
- **📈 Analytics & Insights**: Track application success rates, response times, and market trends
- **🔔 Smart Notifications**: Real-time alerts for new matching jobs and application updates
- **🌍 EU-Focused**: Specialized in European tech market with visa sponsorship support

### 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone the repository
git clone https://github.com/moatasim-KT/career-copilot.git
cd career-copilot

# 2. Start all services with Docker
docker-compose up -d

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! The application is now running with all services configured.

### 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** for local development:
  - Python 3.11+
  - Node.js 18.0+
  - PostgreSQL 14+
  - Redis 7+

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

### 📖 Setup & Installation

- **[Installation Guide](docs/setup/INSTALLATION.md)** - Complete setup instructions
- **[Configuration Guide](docs/setup/CONFIGURATION.md)** - Environment variables and configuration
- **[Quick Start](docs/setup/INSTALLATION.md#quick-start-5-minutes)** - Get running in 5 minutes

### 🏗️ Architecture & Design

- **[System Architecture](docs/architecture/ARCHITECTURE.md)** - Technical architecture and design patterns
- **[Database Schema](docs/architecture/ARCHITECTURE.md#database-schema)** - Database structure and relationships
- **[API Design](docs/architecture/ARCHITECTURE.md#api-architecture)** - RESTful API architecture

### 🔌 API Reference

- **[API Documentation](docs/api/API.md)** - Complete API reference
- **[Authentication](docs/api/API.md#authentication)** - JWT authentication flow
- **[Endpoints](docs/api/API.md#endpoints)** - All available endpoints
- **[Code Examples](docs/api/API.md#code-examples)** - Integration examples

### 🚀 Deployment

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
- **Database**: PostgreSQL 14+ (with SQLAlchemy 2.0 ORM)
- **Cache**: Redis 7+ (caching & message broker)
- **Task Queue**: Celery 5.3+ (background jobs)
- **AI/ML**: OpenAI GPT-4, Anthropic Claude, ChromaDB (vector embeddings)

### Frontend

- **Framework**: Next.js 15.5 (React 19.2)
- **Language**: TypeScript 5.0+
- **Styling**: TailwindCSS 3.4+
- **UI Components**: shadcn/ui
- **State Management**: React Context + Hooks

### Infrastructure

- **Containerization**: Docker & Docker Compose
- **Web Server**: Uvicorn (dev), Gunicorn (prod)
- **Reverse Proxy**: Nginx (production)
- **Monitoring**: Prometheus + Grafana

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

## 🔧 Development

### Local Development Setup

```bash
# 1. Clone repository
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
uvicorn app.main:app --reload

# 3. Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your configuration
npm run dev

# 4. Start background services (new terminals)
cd backend
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info
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

**Features**:
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

**In Development**:
- 🔄 Multi-user authentication system
- 🔄 Real-time notifications (WebSocket)
- 🔄 Advanced analytics & reporting
- 🔄 Mobile application
- 🔄 Interview preparation tools

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](frontend/CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting
- **TypeScript**: Follow project ESLint configuration
- **Commits**: Use conventional commits format

## 📄 License

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
