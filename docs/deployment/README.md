# Deployment

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

This directory contains documentation related to deploying the application.

## Deployment Documentation

### Production Deployment
**Checklist**: [[PRODUCTION_CHECKLIST.md]]

Pre-deployment verification:
- Code review completion
- Test coverage requirements
- Security scanning
- Performance benchmarks
- Database migrations
- Environment configuration
- Monitoring setup
- Rollback procedures

### Docker Deployment
**Location**: [[../../deployment/docker/README.md]]

Container-based deployment with Docker Compose:
- Backend service configuration
- Frontend service configuration  
- PostgreSQL database
- Redis cache
- Celery workers
- Nginx reverse proxy

### Rollback Procedure

In the event of a failed deployment or a critical bug in production, follow these steps to roll back to a previous version of the application.

### 1. Identify the last stable version

Look at the git history to identify the commit hash of the last stable version.

### 2. Revert the deployment

How you revert the deployment will depend on your deployment strategy.

*   **If you are using a blue-green deployment strategy:** Switch traffic back to the blue environment.
*   **If you are using a rolling deployment strategy:** Redeploy the last stable version.
*   **If you are deploying manually:** Revert the commit that caused the issue and redeploy.

### 3. Verify the rollback

Ensure that the application is running the correct version and that the issue has been resolved.

### 4. Communicate the rollback

Inform the team that a rollback has occurred and that the issue is being investigated.
