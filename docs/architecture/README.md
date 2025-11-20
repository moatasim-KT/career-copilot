# Architecture Documentation

> **Navigation Hub**: This directory contains all architecture-related documentation.

**Quick Links**: [[/index|Documentation Hub]] | [[/DEVELOPER_GUIDE|Developer Guide]] | [[/GETTING_STARTED|Getting Started]]

---

## Overview

Career Copilot is built with a modern, scalable architecture using FastAPI (backend) and Next.js 14 (frontend). This directory contains comprehensive documentation of all architectural decisions, system design, and component interactions.

---

## Architecture Documents

### Core System Architecture

* **[[ARCHITECTURE|System Architecture Overview]]** - High-level system design, component interactions, and architectural patterns
* **[[project-overview|Project Overview]]** - Project goals, features, and technology stack
* **[[project-status|Project Status]]** - Current implementation status and roadmap

### Component Architecture

* **[[frontend-architecture|Frontend Architecture]]** - Next.js 14 App Router, React components, state management
* **[[backend-architecture|Backend Architecture]]** - FastAPI services, dependency injection, async patterns
* **[[api-architecture|API Architecture]]** - REST API design, endpoints, request/response patterns

### Data & Storage

* **[[data-architecture|Data Architecture]]** - Data models, relationships, caching strategy
* **[[database-schema|Database Schema]]** - PostgreSQL tables, indexes, migrations

### Security & Integration

* **[[security-architecture|Security Architecture]]** - Authentication, authorization, data protection
* **[[AI_AND_INTEGRATIONS|AI & Integration Services]]** - LLM providers (Groq), job board APIs, third-party integrations
  - Consolidates: `AI_COMPONENTS_REVIEW.md`, `PROMPT_ENGINEERING_GUIDE.md`, `job-services-architecture.md`

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
