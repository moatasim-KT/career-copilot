# Architectural Decision Records (ADRs)

This directory contains records of architectural decisions made during the development of Career Copilot.

## ADR Template

```markdown
# ADR [Number]: [Title]

## Status
[Proposed | Accepted | Rejected | Deprecated | Superseded]

## Context
[Describe the context and forces at play]

## Decision
[Describe the decision made]

## Consequences
[Describe the positive and negative consequences]

## Alternatives Considered
[List alternatives and why they were rejected]

## Related
- [Links to related ADRs, issues, or documents]
```

## Current ADRs

### ADR 001: Service Layer Architecture
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
The application needed a clear separation between API endpoints and business logic to improve maintainability and testability.

#### Decision
Implement a Service Layer pattern where all business logic resides in service classes, and API endpoints only handle HTTP concerns.

#### Consequences
- **Positive**: Better testability, cleaner code separation, easier refactoring
- **Negative**: Additional abstraction layer, learning curve for new developers

#### Alternatives Considered
- Fat Controllers: Rejected due to tight coupling
- Repository Pattern: Considered but service layer provides more flexibility

#### Related
- [[../../backend/app/services/|Service Classes]]
- [[../architecture/ARCHITECTURE.md|Architecture Overview]]

### ADR 002: Multi-LLM Provider Support
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
AI content generation needed to be reliable and cost-effective, requiring fallback between providers.

#### Decision
Implement a unified LLM service that automatically selects the best provider based on task complexity, cost, and availability.

#### Consequences
- **Positive**: Improved reliability, cost optimization, seamless provider switching
- **Negative**: Increased complexity, provider-specific error handling

#### Alternatives Considered
- Single Provider: Rejected due to vendor lock-in and reliability concerns
- Manual Provider Selection: Rejected due to poor user experience

#### Related
- [[../../backend/app/services/llm_service.py|LLM Service]]
- [[../../config/llm_config.json|LLM Configuration]]

### ADR 003: Async Database Operations
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
The application needed to handle high concurrency and improve response times for database operations.

#### Decision
Migrate all database operations to async/await using SQLAlchemy 2.0 with asyncpg.

#### Consequences
- **Positive**: Better concurrency, improved response times, non-blocking I/O
- **Negative**: Migration complexity, async/await throughout codebase

#### Alternatives Considered
- Synchronous Operations: Rejected due to blocking nature
- Mixed Sync/Async: Rejected due to complexity and potential deadlocks

#### Related
- [[../../backend/app/core/database.py|Database Configuration]]
- [[../../backend/app/api/v1/jobs.py|Async Jobs API]]

### ADR 004: JSONB for Flexible Data Storage
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
Job data contains variable structures (tech stacks, interview feedback) that don't fit rigid relational schemas.

#### Decision
Use PostgreSQL JSONB fields for flexible data storage with GIN indexing for efficient querying.

#### Consequences
- **Positive**: Schema flexibility, rich querying capabilities, easy data evolution
- **Negative**: Less type safety, potential data inconsistency

#### Alternatives Considered
- Normalized Tables: Rejected due to complexity and performance
- Text Fields: Rejected due to poor queryability

#### Related
- [[../architecture/database-schema.md#key-design-patterns|JSONB Usage]]
- [[../../backend/app/models/job.py|Job Model]]

### ADR 005: Celery for Background Tasks
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
Job scraping and AI content generation are long-running operations that shouldn't block user requests.

#### Decision
Use Celery with Redis as message broker for all background processing.

#### Consequences
- **Positive**: Non-blocking operations, scalable task processing, reliable job queues
- **Negative**: Additional infrastructure complexity, monitoring requirements

#### Alternatives Considered
- ThreadPoolExecutor: Rejected due to blocking and scalability limits
- FastAPI Background Tasks: Rejected due to lack of persistence and monitoring

#### Related
- [[../../backend/app/celery.py|Celery Configuration]]
- [[../../backend/app/tasks/|Background Tasks]]

### ADR 006: JWT Authentication with Refresh Tokens
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
The application needed secure, stateless authentication with good user experience.

#### Decision
Implement JWT access tokens with separate refresh tokens for session management.

#### Consequences
- **Positive**: Stateless, scalable, good security practices
- **Negative**: Token management complexity, refresh token storage

#### Alternatives Considered
- Session-based Auth: Rejected due to scalability concerns
- API Keys: Rejected due to poor user experience

#### Related
- [[../../backend/app/security/|Security Module]]
- [[../../backend/app/api/v1/auth.py|Auth API]]

### ADR 007: Docker Compose for Development
**Status**: Accepted  
**Date**: November 12, 2025

#### Context
Development environment needed to match production while being easy to set up.

#### Decision
Use Docker Compose for full-stack development environment with hot reloading.

#### Consequences
- **Positive**: Consistent environments, easy onboarding, production parity
- **Negative**: Resource usage, learning curve for Docker

#### Alternatives Considered
- Local Installation: Rejected due to environment differences
- Vagrant: Rejected due to complexity and performance

#### Related
- [[../../docker-compose.yml|Docker Compose Configuration]]
- [[../setup/INSTALLATION.md|Installation Guide]]

## ADR Process

1. **Create**: Use the template above to document new decisions
2. **Review**: Technical leads review and provide feedback
3. **Accept/Reject**: Decision is formally accepted or rejected
4. **Implement**: Changes are implemented according to the decision
5. **Update**: ADRs are updated if decisions change or are superseded

## Categories

- **Architecture**: System design and structure
- **Technology**: Framework and library choices
- **Data**: Database and storage decisions
- **Security**: Authentication and authorization
- **Performance**: Optimization and scaling decisions
- **Development**: Tooling and process decisions

---

*See also: [[../README.md|Project Overview]], [[../PLAN.md|Implementation Plan]]*"