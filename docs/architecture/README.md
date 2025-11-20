# Architecture Documentation

> **Navigation Hub**: This directory contains all architecture-related documentation.

**Quick Links**: [[/index|Documentation Hub]] | [[/DEVELOPER_GUIDE|Developer Guide]] | [[/GETTING_STARTED|Getting Started]]

---

## Overview

Career Copilot is built with a modern, scalable architecture using FastAPI (backend) and Next.js 14 (frontend). This directory contains comprehensive documentation of all architectural decisions, system design, and component interactions.

---

## Architecture Documents

### Core System Architecture

* **[[ARCHITECTURE|System Architecture]]** - Comprehensive system architecture with diagrams (system overview, component interaction, data flow, deployment)
* **[[SYSTEM_COMPONENTS|System Components]]** - Detailed component architecture (frontend, backend, API, data layer, database schema)
* **[[AI_AND_INTEGRATIONS|AI & Integration Services]]** - AI/LLM architecture, prompt engineering, job board integrations

### Related Architecture Documentation

* **Security**: [[/security/ARCHITECTURE|Security Architecture]] - Authentication, authorization, data protection
* **Performance**: [[/performance/ARCHITECTURE|Performance Architecture]] - Optimization strategies, caching, scaling
* **Project Information**: [[/project/OVERVIEW|Project Overview]] & [[/project/STATUS|Project Status]]

---

## Quick Reference

### Technology Stack

**Backend**:
- FastAPI (Python 3.11+)
- PostgreSQL 14+ (database)
- Redis 7+ (caching, async tasks)
- Celery (background jobs)
- Alembic (database migrations)

**Frontend**:
- Next.js 14+ (App Router)
- React 18+
- TypeScript
- Tailwind CSS v4
- Framer Motion

**Infrastructure**:
- Docker & Docker Compose
- GitHub Actions (CI/CD)

### Key Architectural Patterns

1. **Repository Pattern**: Data access layer abstraction
2. **Dependency Injection**: Service dependencies via FastAPI
3. **Async/Await**: Non-blocking I/O throughout
4. **Event-Driven**: Celery tasks for background processing
5. **API-First**: RESTful API with OpenAPI/Swagger docs

### System Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Next.js   │────────▶│   FastAPI    │────────▶│ PostgreSQL  │
│  Frontend   │  HTTP   │   Backend    │  SQL    │  Database   │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  WebSocket  │◀────────│    Redis     │◀────────│   Celery    │
│Real-time UI │         │Cache/PubSub  │         │ Background  │
└─────────────┘         └──────────────┘         └─────────────┘
```

---

## Getting Started with Architecture

1. **New to the project?** Start with [[project-overview|Project Overview]]
2. **Building features?** Read [[ARCHITECTURE|System Architecture]] and relevant component docs
3. **Contributing?** Review [[/DEVELOPER_GUIDE|Developer Guide]] and [[/CONTRIBUTING|Contributing Guidelines]]
4. **Debugging?** Check [[/troubleshooting/RUNBOOK|Operations Runbook]]

---

## Related Documentation

- **Setup**: [[/GETTING_STARTED|Getting Started Guide]]
- **Development**: [[/DEVELOPER_GUIDE|Developer Guide]]
- **Testing**: [[/TESTING_GUIDE|Testing Guide]]
- **Deployment**: [[/deployment/README|Deployment Guide]]
- **API Reference**: [[/api/API|API Documentation]]

---

**Last Updated**: November 2025
