# Career Copilot - Project Structure

This document explains the root directory organization and where to find specific files.

## 📁 Root Directory Structure

```
career-copilot/
├── 📄 Core Files
│   ├── README.md              # Main project documentation
│   ├── LICENSE                # MIT License
│   ├── VERSION                # Current version number
│   ├── .env.example           # Environment variables template
│   ├── .dockerignore          # Docker ignore patterns
│   └── .gitignore             # Git ignore patterns
│
├── 🔧 Configuration Files
│   ├── docker-compose.yml     # Docker Compose configuration
│   ├── pyproject.toml         # Python project configuration
│   ├── poetry.lock            # Poetry lock file
│   └── Makefile               # Make commands
│
├── 📂 Application Code
│   ├── backend/               # FastAPI backend application
│   ├── frontend/              # Next.js frontend application
│   └── tests/                 # Integration & E2E tests
│
├── 📂 Infrastructure
│   ├── deployment/            # Deployment configurations
│   │   ├── docker/           # Dockerfile configurations
│   │   ├── k8s/              # Kubernetes manifests
│   │   ├── nginx/            # Nginx configurations
│   │   ├── render.yaml       # Render.com deployment
│   │   └── ...
│   ├── monitoring/            # Monitoring configurations
│   │   ├── prometheus/       # Prometheus config
│   │   ├── grafana/          # Grafana dashboards
│   │   └── ...
│   └── secrets/               # Secret management
│
├── 📂 Development
│   ├── scripts/               # Utility scripts (organized by function)
│   ├── config/                # Application configurations
│   ├── bin/                   # Executable scripts
│   │   ├── start_backend.sh  # Start backend server
│   │   ├── start_frontend.sh # Start frontend server
│   │   ├── start_celery.sh   # Start Celery worker
│   │   └── deploy.sh         # Deployment script
│   └── .tools/                # Tool configurations
│       ├── .bandit           # Bandit security config
│       ├── .codecov.yml      # Code coverage config
│       └── ruff.toml         # Ruff linter config
│
├── 📂 Data & Logs
│   ├── data/                  # Application data
│   │   ├── databases/        # Database files
│   │   ├── chroma/           # Vector database
│   │   ├── uploads/          # User uploads
│   │   ├── logs/             # Application logs
│   │   └── backups/          # Backups
│   ├── logs/                  # Legacy logs directory
│   └── reports/               # Generated reports
│
├── 📂 Documentation
│   ├── docs/                  # Comprehensive documentation
│   │   ├── setup/            # Installation & configuration
│   │   ├── architecture/     # System architecture
│   │   ├── api/              # API documentation
│   │   ├── development/      # Development guides
│   │   ├── deployment/       # Deployment guides
│   │   └── troubleshooting/  # Common issues
│   └── .github/               # GitHub-specific files
│       ├── workflows/        # GitHub Actions
│       └── ISSUE_TEMPLATE/   # Issue templates
│
├── 📂 Hidden/Archive
│   ├── .archive/              # Reports, backups, completed tasks
│   ├── .venv/                 # Python virtual environment
│   ├── .pytest_cache/         # Pytest cache
│   ├── .ruff_cache/           # Ruff cache
│   ├── .git/                  # Git repository
│   └── .vscode/               # VS Code settings
│
└── 🔒 Private (git-ignored)
    └── .env                   # Local environment variables
```

## 🗂️ Directory Purposes

### Application Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `backend/` | FastAPI backend application | Python 3.11+, PostgreSQL, Redis |
| `frontend/` | Next.js frontend application | React 19.2, TypeScript 5.0+ |
| `tests/` | Integration and E2E tests | Shared test infrastructure |

### Infrastructure Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `deployment/` | Deployment configurations | Docker, K8s, cloud platforms |
| `monitoring/` | Monitoring & observability | Prometheus, Grafana configs |
| `secrets/` | Secret management | Git-ignored, encryption keys |

### Development Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `scripts/` | Utility scripts | Organized by function (setup, testing, etc.) |
| `config/` | Application configurations | Environment-specific configs |
| `bin/` | Executable scripts | Startup and deployment scripts |
| `.tools/` | Tool configurations | Linters, formatters, security tools |

### Data Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `data/` | Application data | Databases, uploads, logs, backups |
| `logs/` | Legacy logs | Being migrated to `data/logs/` |
| `reports/` | Generated reports | Test reports, analysis results |

### Documentation Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `docs/` | Comprehensive documentation | Setup, architecture, API, guides |
| `.github/` | GitHub-specific files | Workflows, issue templates |

### Hidden/Archive Directories

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `.archive/` | Old reports and backups | Audit reports, completion summaries |
| `.venv/` | Python virtual environment | Git-ignored |
| `.git/` | Git repository | Version control |

## 📄 Important Files

### Core Configuration Files

| File | Purpose | Notes |
|------|---------|-------|
| `README.md` | Main project documentation | Start here! |
| `docker-compose.yml` | Docker services configuration | Quick start with Docker |
| `pyproject.toml` | Python project config | Dependencies, tools |
| `Makefile` | Common commands | `make help` for all commands |
| `.env.example` | Environment template | Copy to `.env` |

### Executable Scripts (bin/)

| File | Purpose | Usage |
|------|---------|-------|
| `start_backend.sh` | Start backend server | `./bin/start_backend.sh` |
| `start_frontend.sh` | Start frontend server | `./bin/start_frontend.sh` |
| `start_celery.sh` | Start Celery worker | `./bin/start_celery.sh` |
| `deploy.sh` | Deploy application | `./bin/deploy.sh` |

### Tool Configurations (.tools/)

| File | Purpose | Notes |
|------|---------|-------|
| `.bandit` | Security linter config | Python security scanning |
| `.codecov.yml` | Code coverage config | Coverage reporting |
| `ruff.toml` | Ruff linter config | Python linting and formatting |

## 🚀 Quick Navigation

### Getting Started
```bash
# 1. Read documentation
cat README.md
cat docs/setup/INSTALLATION.md

# 2. Set up environment
cp .env.example .env
# Edit .env with your settings

# 3. Start with Docker
docker-compose up -d

# OR start manually
./bin/start_backend.sh &
./bin/start_frontend.sh &
```

### Development Workflow
```bash
# Backend development
cd backend/
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend development
cd frontend/
npm run dev

# Run tests
cd scripts/testing/
python test_runner.py
```

### Common Tasks
```bash
# Database operations
cd scripts/database/
python initialize_database.py
python seed.py

# Run security audit
cd scripts/security/
python security_audit.py

# Performance testing
cd scripts/performance/
python stress_test.py

# Deployment
./bin/deploy.sh
```

## 📖 Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Installation Guide | `docs/setup/INSTALLATION.md` | How to install |
| Configuration Guide | `docs/setup/CONFIGURATION.md` | How to configure |
| Architecture | `docs/architecture/ARCHITECTURE.md` | System design |
| API Reference | `docs/api/API.md` | API documentation |
| Development Guide | `docs/development/DEVELOPMENT.md` | Developer handbook |
| Deployment Guide | `docs/deployment/DEPLOYMENT.md` | Production deployment |
| Troubleshooting | `docs/troubleshooting/COMMON_ISSUES.md` | Common problems |

## 🔍 Finding Files

### "Where is...?"

**Configuration files?**
- Root: `docker-compose.yml`, `pyproject.toml`, `.env.example`
- Application: `config/`
- Tool-specific: `.tools/`

**Scripts?**
- All scripts: `scripts/`
- Startup scripts: `bin/`
- See: `scripts/README.md`

**Logs?**
- Application logs: `data/logs/`
- Legacy logs: `logs/`

**Database files?**
- SQLite databases: `data/databases/`
- Vector database: `data/chroma/`

**Documentation?**
- Comprehensive docs: `docs/`
- Main README: `README.md`
- Scripts README: `scripts/README.md`

**Reports?**
- Current reports: `reports/`
- Archived reports: `.archive/`

**Deployment configs?**
- All deployment: `deployment/`
- Docker: `deployment/docker/`
- Kubernetes: `deployment/k8s/`

## 🧹 Maintenance

### Cleanup Commands

```bash
# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Remove Node modules (rebuild with npm install)
rm -rf frontend/node_modules

# Clean Docker
docker system prune -a

# Clear logs (CAUTION)
rm -rf data/logs/*
rm -rf logs/*
```

### What's Git-Ignored?

- `.env` (secrets)
- `.venv/` (virtual environment)
- `data/` (application data)
- `.archive/` (reports and backups)
- `__pycache__/`, `*.pyc` (Python cache)
- `node_modules/` (Node dependencies)
- `*.log` (log files)
- `.DS_Store` (macOS)

See `.gitignore` for complete list.

## 📝 Adding New Files

### Where should I put...?

**A new Python script?**
- Utility script: `scripts/<category>/`
- Backend code: `backend/app/`

**A new configuration file?**
- App config: `config/`
- Tool config: `.tools/`
- Deployment config: `deployment/`

**A new document?**
- User docs: `docs/<category>/`
- Code docs: In code as docstrings

**A new test?**
- Unit tests: `backend/tests/` or `frontend/tests/`
- Integration tests: `tests/integration/`
- E2E tests: `tests/e2e/`

**A new deployment config?**
- Docker: `deployment/docker/`
- Kubernetes: `deployment/k8s/`
- Cloud-specific: `deployment/<platform>/`

## 🔗 Related Documentation

- [Installation Guide](docs/setup/INSTALLATION.md) - Get started
- [Scripts README](scripts/README.md) - Script organization
- [Contributing Guide](frontend/CONTRIBUTING.md) - How to contribute
- [Architecture](docs/architecture/ARCHITECTURE.md) - System design

## 📞 Support

- **Documentation**: Start with `README.md` and `docs/`
- **Issues**: [GitHub Issues](https://github.com/moatasim-KT/career-copilot/issues)
- **Email**: <moatasimfarooque@gmail.com>

---

**Last Updated**: November 7, 2025  
**Version**: 1.0.0
