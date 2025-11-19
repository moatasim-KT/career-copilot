# Getting Started

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

This guide will walk you through the process of setting up and running the Career Copilot application.

## Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** for local development:
  - Python 3.11+
  - Node.js 18.0+
  - PostgreSQL 14+
  - Redis 7+

## Docker (Recommended)

The recommended way to run the application is with Docker Compose.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/moatasim-KT/career-copilot.git
    cd career-copilot
    ```

2.  **Start all services:**
    ```bash
    docker-compose up -d
    ```

3.  **Access the application:**
    *   Frontend: `http://localhost:3000`
    *   Backend API: `http://localhost:8000`
    *   API Docs: `http://localhost:8000/docs`

## Local Development

For local development, you will need to set up the backend and frontend separately.

### Backend

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```

2.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up the environment variables:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file with your database and AI provider credentials.

5.  Run the database migrations:
    ```bash
    alembic upgrade head
    ```

6.  Start the backend server:
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  Install the dependencies:
    ```bash
    npm install
    ```

3.  Set up the environment variables:
    ```bash
    cp .env.example .env.local
    ```
    Edit the `.env.local` file with your backend API URL.

4.  Start the frontend server:
    ```bash
    npm run dev
    ```

[[../index]]