# Career Copilot

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-username/career-copilot/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/your-username/career-copilot)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

AI-powered career management tool to assist users with job search and career development.

## Table of Contents

- [1. Project Title & Badges](#1-project-title--badges)
- [2. Description](#2-description)
- [3. Architecture](#3-architecture)
- [4. Features](#4-features)
- [5. Installation](#5-installation)
- [6. Quick Start / Usage](#6-quick-start--usage)
- [7. API Documentation](#7-api-documentation)
- [8. Configuration](#8-configuration)
- [9. Deployment](#9-deployment)
- [10. Development](#10-development)
- [11. Testing](#11-testing)
- [12. Roadmap](#12-roadmap)
- [13. Contributing](#13-contributing)
- [14. License](#14-license)
- [15. Authors & Acknowledgments](#15-authors--acknowledgments)
- [16. Support & Contact](#16-support--contact)

## 2. Description

Career Copilot is an AI-powered career management tool designed to assist users with various aspects of their job search and career development. It aims to streamline the job application process, provide personalized insights, and help users identify and bridge skill gaps.

The project follows a monorepo structure with distinct backend and frontend components.

**Why it exists:** The modern job market can be overwhelming. Career Copilot solves the problem of managing multiple applications, understanding market trends, and continuously improving one's professional profile by leveraging AI to provide intelligent assistance.

**What makes it unique:** Career Copilot integrates a comprehensive suite of AI-driven tools into a single platform, offering a holistic approach to career management from application tracking to skill development and interview preparation.

## 3. Architecture

The project follows a monorepo structure with distinct backend and frontend components:

*   **Backend:** Developed using Python with the FastAPI framework.
*   **Frontend:** Developed using Node.js with the Next.js framework.

## 4. Features

### Core Features
- **Dashboard:** Quick overview of job search progress.
- **Jobs & Applications:** Tracking of job applications and personalized recommendations.
- **Recommendations:** Personalized job recommendations.
- **Analytics:** Detailed job search performance analysis.
- **Skill Gap:** Identification of skill gaps and learning recommendations.
- **Content Generation:** AI-powered cover letter and resume summary generation.
- **Interview Practice:** AI-powered interview practice.

### Frontend Specific Features
- **Modern Stack**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Responsive Design**: Mobile-first design that works on all devices
- **Job Management**: Add, edit, delete, and track job opportunities
- **Application Tracking**: Monitor application status and progress
- **Analytics Dashboard**: View key metrics and insights
- **User Authentication**: Secure login and registration
- **Real-time Updates**: Live data synchronization with backend

## 5. Installation

### Prerequisites

*   Python 3.9+
*   Node.js 16+
*   Docker (optional, for containerized deployment)
*   Redis and PostgreSQL (for Celery and database)

### Step-by-step Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/career-copilot.git
    cd career-copilot
    ```

2.  **Backend Setup:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    # Fill in the .env file with your credentials (e.g., database URL, API keys)
    ```

3.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install
    cp .env.local.example .env.local
    # Edit .env.local with your backend URL
    ```

### Verification Steps

After installation, you can verify the setup by running the application in development mode as described in the [Quick Start / Usage](#6-quick-start--usage) section.

## 6. Quick Start / Usage

### Running in Development Mode

1.  **Start the Backend API:**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```

2.  **Start the Frontend Application:**
    ```bash
    cd frontend
    npm run dev
    ```
    The application will be available at `http://localhost:3000`.

### Running with `start.sh` (Production-like)

The `start.sh` script can be used to run both the backend and frontend in a more production-like manner:

```bash
./start.sh
```
This script starts the backend on `http://0.0.0.0:8000` and the frontend using `npm run start`.

## 7. API Documentation

The backend API documentation (Swagger UI) is automatically generated and available at `/docs` when the FastAPI application is running. For example, if running locally, visit `http://localhost:8000/docs`.

The frontend communicates with the FastAPI backend through a typed API client (`src/lib/api.ts`). All API calls are properly typed and include error handling.

### Key API Features:
- Authentication with JWT tokens
- Automatic token refresh
- Error handling and retry logic
- TypeScript interfaces for all data types

## 8. Configuration

Key configuration options are managed through environment variables. A `.env.example` file is provided in the `backend/` directory, which you should copy to `.env` and populate with your specific settings. Similarly, for the frontend, copy `.env.local.example` to `.env.local`.

**Common Backend Environment Variables:**
- `DATABASE_URL`: Connection string for the PostgreSQL database.
- `CELERY_BROKER_URL`: URL for the Celery message broker (e.g., Redis).
- `CELERY_RESULT_BACKEND`: URL for the Celery result backend (e.g., Redis).
- `JWT_SECRET_KEY`: Secret key for JWT token generation.
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins for the frontend.
- `OPENAI_API_KEY`: API key for OpenAI services (if used for content generation).

**LinkedIn Scraping Environment Variables:**
- `LINKEDIN_EMAIL`: Your LinkedIn account email for scraping.
- `LINKEDIN_PASSWORD`: Your LinkedIn account password for scraping.


**Common Frontend Environment Variables:**
- `NEXT_PUBLIC_BACKEND_URL`: Backend API URL.
- `NEXT_PUBLIC_APP_ENV`: Environment (development/production).

## 9. Deployment

This section covers deploying the Career Copilot application to a production environment, including Celery services.

### Prerequisites for Deployment

- A server with Docker and Docker Compose installed.
- A domain name pointing to your server's IP address.
- Redis and PostgreSQL services running and accessible.

### 9.1. Main Application Deployment

1.  **Configuration:**
    *   Create a `.env` file in the root of the project and fill in the necessary environment variables for both backend and frontend.
    *   Update the `nginx/nginx.conf` file with your domain name if you are using Nginx for reverse proxy.

2.  **Build and Run with Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```
    This will build the Docker images and start the backend, frontend, and database containers.

3.  **Database Migrations:**
    Run the following command to apply database migrations:
    ```bash
    docker-compose exec backend alembic upgrade head
    ```

### 9.2. Celery Worker and Beat Deployment

The `deployment/celery/docker-compose.yml` file defines services for the Celery worker and Celery Beat.

1.  **Ensure Docker Network:** Ensure your Redis and PostgreSQL services are running and accessible on a Docker network named `career_copilot_network`. You might need to create this network and connect your database/redis containers to it if they are not already.
    ```bash
    docker network create career_copilot_network
    # Example: connect your existing redis/postgres containers to this network
    # docker network connect career_copilot_network <your_redis_container_name>
    # docker network connect career_copilot_network <your_postgres_container_name>
    ```

2.  **Start the Celery worker and beat services:**
    ```bash
    docker-compose -f deployment/celery/docker-compose.yml up -d
    ```
    This will build the backend Docker image (if not already built) and start the Celery worker and beat in detached mode.

### 9.3. Monitoring Celery Logs

You can monitor the logs of your Celery worker and beat services using Docker Compose.

1.  **View logs for both services:**
    ```bash
    docker-compose -f deployment/celery/docker-compose.yml logs -f
    ```
    This will show the combined logs from both the worker and beat services.

2.  **View logs for a specific service (e.g., worker):**
    ```bash
    docker-compose -f deployment/celery/docker-compose.yml logs -f celery_worker
    ```

### 9.4. Stopping Celery Services

To stop the Celery worker and beat services:

```bash
docker-compose -f deployment/celery/docker-compose.yml down
```

## 10. Development

### Setting up Development Environment

Follow the [Installation](#5-installation) steps to set up your local development environment.

### Development Conventions

*   **Pre-commit Hooks:** The project utilizes `pre-commit` hooks for code quality and consistency, configured via `.pre-commit-config.yaml`.
*   **CI/CD Workflows:** Continuous Integration and Continuous Deployment workflows are defined in the `.github/workflows/` directory.
*   **Makefile:** Common development tasks and commands are likely automated using the `Makefile`.

### Documentation Guidelines

All Python code in this project must follow our docstring standards as outlined in `docs/DOCSTRING_GUIDE.md`. Key requirements include:
- All modules, classes, methods, and functions MUST have docstrings.
- Use Google-style docstring format.
- Include type hints in function/method signatures.
- Document exceptions that may be raised.
- Provide usage examples for complex functions.

### Frontend Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

- TypeScript for type safety
- ESLint for code quality
- Prettier for formatting
- Tailwind CSS for styling

## 11. Testing

The project includes a comprehensive testing suite:

*   **Unit Tests:** Located in `backend/tests/unit/` and `frontend/src/**/*.test.js`.
*   **Integration Tests:** Located in `backend/tests/integration/`.
*   **End-to-End (E2E) Tests:** Located in `frontend/cypress/`.
*   **Code Quality:** Enforced via `pre-commit` hooks and CI/CD workflows.

### Running Tests

*   **Backend Tests:**
    ```bash
    cd backend
    pytest
    ```
*   **Frontend Tests:**
    ```bash
    cd frontend
    npm test
    # For E2E tests
    npm run cypress:open
    ```

### Manually Triggering a Celery Task (for testing)

You can manually trigger a Celery task from within the running backend container.

1.  **Find the backend container ID:**
    ```bash
    docker ps
    ```
    Look for the container running your FastAPI application (if you have it running via Docker) or the `celery_worker` container.

2.  **Access the backend container's shell:**
    ```bash
    docker exec -it <backend_container_id> bash
    ```
    Replace `<backend_container_id>` with the actual ID or name of your backend container.

3.  **Inside the container, open a Python shell and trigger a task:**
    ```python
    python
    >>> from app.celery import celery_app
    >>> from app.tasks.example_task import example_task
    >>> example_task.delay("Manual trigger from live test!")
    # You should see a task ID returned, e.g., <AsyncResult: 01234567-89ab-cdef-0123-456789abcdef>
    ```

## 12. Roadmap

- Enhanced AI models for content generation and recommendations.
- Integration with more job boards and career platforms.
- Advanced analytics and reporting features.
- Mobile application development.
- Further migration of legacy Streamlit features to Next.js frontend.

## 13. Contributing

We welcome contributions to Career Copilot! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started, our code of conduct, and the pull request process. Adherence to [Documentation Guidelines](#documentation-guidelines) is expected.

## 14. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 15. Authors & Acknowledgments

*   **Main Contributors:** [Your Name/Team Name]
*   **Acknowledgments:** Special thanks to all contributors and the open-source community for their invaluable tools and libraries.

## 16. Support & Contact

If you encounter any issues or have questions, please:
- Open an issue on our [GitHub Issue Tracker](https://github.com/your-username/career-copilot/issues).
- Reach out to the development team at [your-email@example.com].