# Backend Architecture

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

The backend of Career Copilot is a FastAPI-based application that provides a robust and scalable API for the frontend.

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery

## Design Patterns

- **Repository Pattern**: Data access abstraction (`repositories/`)
- **Service Layer**: Business logic separation (`services/`)
- **Dependency Injection**: FastAPI dependencies (`dependencies.py`)
- **Schema Validation**: Pydantic models (`schemas/`)
- **Background Tasks**: Celery tasks (`tasks/`)

## API Structure

```
/api/v1/
├── /auth          # Authentication (login, register, tokens)
├── /users         # User management
├── /profiles      # User profiles
├── /jobs          # Job listings & search
├── /applications  # Job applications
├── /resumes       # Resume management
├── /analytics     # User analytics
├── /market        # Market analysis
└── /health        # Health checks
```

[[Architecture]]