# Development Workflow

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

This document outlines the development workflow for the Career Copilot project.

## Coding Style

- **Python**: Follows the PEP 8 style guide. `ruff` is used for linting and formatting.
- **TypeScript**: Follows the configuration in the `.eslintrc.json` file. `prettier` is used for formatting.

## Testing

- **Backend**: Tests are located in the `backend/tests` directory and are run with `pytest`.
- **Frontend**: Tests are located in the `frontend` directory and are run with `jest` and `vitest`.

## Commit Messages

Commit messages should follow the Conventional Commits format.

## Adding New Features

### Backend

1.  **Create Model** (`app/models/`)
2.  **Create Schema** (`app/schemas/`)
3.  **Create Repository** (`app/repositories/`)
4.  **Create Service** (`app/services/`)
5.  **Create API Route** (`app/api/`)
6.  **Add Tests**

### Frontend

1.  **Create Component**
2.  **Add Types**
3.  **Create API Client**
4.  **Create Hook**
5.  **Create Page**
6.  **Add Tests**

[[../index]]