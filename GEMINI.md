# Career Copilot GEMINI.md

This document provides instructional context for interacting with the Career Copilot project.

## Project Overview

Career Copilot is an AI-powered career management platform designed for tech professionals seeking employment in the European Union. It automates the job search process by scraping job boards, generating tailored resumes and cover letters using AI, and providing a centralized dashboard for application tracking.

The project is a full-stack application with the following components:

*   **Backend:** A FastAPI application written in Python. It uses PostgreSQL for the database, Redis for caching and message brokering, and Celery for asynchronous task processing. The backend also integrates with AI services like OpenAI and Anthropic for content generation.
*   **Frontend:** A Next.js application written in TypeScript. It uses React for the user interface, TailwindCSS for styling, and `shadcn/ui` for UI components.
*   **Infrastructure:** The application is containerized using Docker and can be deployed with Docker Compose. It uses Gunicorn as the production web server and Nginx as a reverse proxy.

## Building and Running

### Docker (Recommended)

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

### Local Development

For local development, you will need to set up the backend and frontend separately.

**Prerequisites:**

*   Python 3.11+
*   Node.js 18.0+
*   PostgreSQL 14+
*   Redis 7+

**Backend:**

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

**Frontend:**

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

## Development Conventions

### Coding Style

*   **Python:** Follows the PEP 8 style guide. `ruff` is used for linting and formatting.
*   **TypeScript:** Follows the configuration in the `.eslintrc.json` file. `prettier` is used for formatting.

### Testing

*   **Backend:** Tests are located in the `backend/tests` directory and are run with `pytest`.
*   **Frontend:** Tests are located in the `frontend` directory and are run with `jest`.

### Commit Messages

Commit messages should follow the Conventional Commits format.
