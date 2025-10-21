# Career Copilot 🚀

An intelligent, proactive job application tracking system that transforms your job search from a manual activity into a guided, goal-oriented workflow.

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/yourusername/career-copilot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/github/actions/workflow/status/yourusername/career-copilot/test-runner.yml?branch=main)](https://github.com/yourusername/career-copilot/actions/workflows/test-runner.yml)

---

## 🎯 Quick Start (Local Development)

1.  **Clone repository:**
    ```bash
    git clone <repository-url>
    cd career-copilot
    ```
2.  **Set up environment:**
    ```bash
    cp backend/.env.example backend/.env
    # Edit backend/.env with your database URL, API keys, etc.
    ```
3.  **Install dependencies:**
    ```bash
    pip install .[all]
    ```
4.  **Initialize database & migrations:**
    ```bash
    # Create the data directory if it doesn't exist
    mkdir -p backend/data
    # Create initial database file and stamp it with the first migration
    python manual_stamp.py
    # Apply any pending migrations (e.g., if you pull new changes)
    cd backend && alembic upgrade head && cd ..
    ```
5.  **Seed initial data (optional):**
    ```bash
    python backend/app/scripts/seed_data.py
    ```
6.  **Start Backend API:**
    ```bash
    cd backend
    uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
    # Access API Docs at http://localhost:8002/docs
    ```
7.  **Start Frontend (Streamlit):**
    ```bash
    streamlit run frontend/app.py --server.port 8501
    # Access Frontend at http://localhost:8501
    ```

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)

---

## Overview

Career Copilot helps you manage your job search with AI-powered recommendations, skill gap analysis, and automated workflows.

**What Makes It Different?**
- **Proactive**: Automatically finds and recommends jobs based on your profile
- **Intelligent**: Analyzes skill gaps and provides learning recommendations
- **Automated**: Daily email briefings and progress summaries
- **Data-Driven**: Makes career decisions based on market insights

---

## Features

### Core Features

-   **User Authentication** - Secure JWT-based account management (Register, Login)
-   **User Profile Management** - Manage skills, locations, and experience level (`GET/PUT /api/v1/profile`)
-   **Job Tracking** - Save and organize opportunities with detailed information (Create, List, Update, Delete jobs)
-   **Application Management** - Track status and progress through the pipeline (Create, List, Update applications)
-   **Personalized Job Recommendations** - AI-powered job matching based on profile and job data (`GET /api/v1/recommendations`)
-   **Skill Gap Analysis** - Identify missing skills and market demands, with learning recommendations (`GET /api/v1/skill-gap`)
-   **Analytics Dashboard** - Visualize job search metrics and trends, including daily application goals (`GET /api/v1/analytics/summary`)
-   **Automated Job Ingestion** - Scheduled scraping from external APIs based on user preferences
-   **Daily Notifications** - Morning briefings with recommendations, evening summaries with progress via email
-   **Comprehensive Health Check** - API endpoint to monitor database and scheduler status (`GET /api/v1/health`)
-   **Structured Error Handling** - Consistent JSON error responses for API failures.
-   **Structured Logging** - Detailed logs to console and rotating files.

---

## Architecture

### System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Frontend    │────▶│     Backend     │────▶│     Database    │
│   (Streamlit)   │     │    (FastAPI)    │     │   (PostgreSQL)  │
└─────────────────┘     └─────────┬───────┘     └─────────────────┘
                                  │
                           ┌──────┴──────┐
                           │   Services  │
                           ├─────────────┤
                           │ • Recommend │
                           │ • Skill Gap │
                           │ • Scraper   │
                           │ • Notifier  │
                           └──────┬──────┘
                                  │
                           ┌──────┴──────┐
                           │   Scheduler │
                           ├─────────────┤
                           │ 4AM: Ingest │
                           │ 7:30AM: Recs│
                           │ 8AM: Brief  │
                           │ 8PM: Summary│
                           └─────────────┘
```

### Technology Stack

**Backend**: FastAPI • SQLAlchemy • APScheduler • Pydantic • JWT • Celery
**Frontend**: Streamlit • Requests
**Database**: SQLite (dev) / PostgreSQL (prod)

### Project Structure

```
career-copilot/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # API endpoints (auth, jobs, profile, recommendations, skill-gap, analytics)
│   │   ├── core/                # Core components (config, database, security, logging)
│   │   ├── models/              # Database models (user, job, application)
│   │   ├── services/            # Business logic (recommendation_engine, skill_gap_analyzer, job_scraper, job_analytics_service, notification_service)
│   │   ├── tasks/               # Celery tasks (job_ingestion_tasks, notification_tasks, recommendation_tasks)
│   │   ├── scheduler.py         # APScheduler setup
│   │   └── main.py              # FastAPI application entry point
│   ├── alembic/                 # Database migrations
│   └── .env.example             # Environment variables template
├── frontend/
│   └── app.py                   # Streamlit application
│   └── requirements.txt         # Streamlit app dependencies
├── tests/                       # Unit and integration tests
├── .pre-commit-config.yaml      # Code quality hooks
├── pyproject.toml               # Project metadata and Python dependencies
└── README.md                    # Project documentation
```

---

## Installation (Local Development)

### Prerequisites

-   Python 3.11+
-   `pip`
-   `git`

### Setup

1.  **Clone repository:**
    ```bash
    git clone <repository-url>
    cd career-copilot
    ```
2.  **Set up environment:**
    ```bash
    cp backend/.env.example backend/.env
    # IMPORTANT: Edit backend/.env to configure your database URL, JWT secret, API keys, etc.
    # For local development, you can keep DATABASE_URL=sqlite:///./data/career_copilot.db
    ```
3.  **Install dependencies:**
    ```bash
    pip install .[all]
    ```
4.  **Initialize database & migrations:**
    ```bash
    # Create the data directory if it doesn't exist
    mkdir -p backend/data
    # Create initial database file and stamp it with the first migration
    python manual_stamp.py
    # Apply any pending migrations (e.g., if you pull new changes)
    cd backend && alembic upgrade head && cd ..
    ```
5.  **Seed initial data (optional):**
    ```bash
    python backend/app/scripts/seed_data.py
    ```
6.  **Start Backend API:**
    ```bash
    cd backend
    uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
    # Access API Docs at http://localhost:8002/docs
    ```
7.  **Start Frontend (Streamlit):**
    ```bash
    streamlit run frontend/app.py --server.port 8501
    # Access Frontend at http://localhost:8501
    ```

---

## Configuration

All configuration is managed via environment variables, loaded by `pydantic-settings`. Refer to `backend/.env.example` for a comprehensive list and documentation.

**Key Variables:**
-   `ENVIRONMENT`: `development`, `production`, or `testing`
-   `DATABASE_URL`: Connection string for your database.
-   `JWT_SECRET_KEY`: **CRITICAL** for security. Change in production.
-   `SMTP_ENABLED`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`: For email notifications.
-   `ENABLE_SCHEDULER`: `True` to enable background tasks.
-   `ENABLE_JOB_SCRAPING`, `JOB_API_KEY`: For automated job discovery.

---

## API Reference

All API endpoints are documented using OpenAPI (Swagger UI) at `/docs` when `DEBUG=True`.

### Authentication
-   `POST /api/v1/auth/register`: Register a new user.
-   `POST /api/v1/auth/login`: Authenticate user and get JWT token.

### User Profile
-   `GET /api/v1/profile`: Retrieve current user's profile.
-   `PUT /api/v1/profile`: Update current user's profile (skills, locations, experience).

### Jobs
-   `POST /api/v1/jobs`: Create a new job entry.
-   `GET /api/v1/jobs`: List user's jobs with pagination.
-   `GET /api/v1/jobs/{job_id}`: Retrieve a specific job.
-   `PUT /api/v1/jobs/{job_id}`: Update a job.
-   `DELETE /api/v1/jobs/{job_id}`: Delete a job.

### Applications
-   `POST /api/v1/applications`: Create a new application entry.
-   `GET /api/v1/applications`: List user's applications with pagination.
-   `PUT /api/v1/applications/{app_id}`: Update an application (e.g., status).

### Recommendations
-   `GET /api/v1/recommendations`: Get personalized job recommendations based on user profile.

### Skill Gap Analysis
-   `GET /api/v1/skill-gap`: Get analysis of user's skill gaps and learning recommendations.

### Analytics
-   `GET /api/v1/analytics/summary`: Get a summary of job application analytics.

### Health Check
-   `GET /api/v1/health`: Get application health status (database, scheduler).

---

## Deployment (Zero-Cost Cloud)

This project is designed for zero-cost deployment using Render (for backend) and Streamlit Community Cloud (for frontend).

1.  **Backend (FastAPI on Render):**
    *   Create a free account on [Render](https://render.com).
    *   Create a **New Blueprint** and connect your GitHub repository.
    *   Render will automatically detect and use the `render.yaml` file in the project root to provision a free web service for your FastAPI backend and a free PostgreSQL database.
    *   **Important:** Configure environment variables on Render (e.g., `JWT_SECRET_KEY`, `SMTP_PASSWORD`, `JOB_API_KEY`) matching your `backend/.env` file. Render will automatically set `DATABASE_URL` from its PostgreSQL service.

2.  **Frontend (Streamlit on Streamlit Community Cloud):**
    *   Create a free account on [Streamlit Community Cloud](https://streamlit.io/cloud).
    *   Click **New app** and connect your GitHub repository.
    *   Set the "Main file path" to `frontend/app.py`.
    *   **Important:** In the app settings, add a secret/environment variable named `BACKEND_URL` and set its value to the public URL of your deployed Render backend (e.g., `https://your-backend.onrender.com`).
    *   Deploy the application.

---

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Install pre-commit hooks
pre-commit install

# Run checks manually
pre-commit run --all-files
```

---

## Testing

-   **Unit Tests**: Located in `tests/unit/`. Verify individual components and services.
-   **Integration Tests**: Located in `tests/integration/`. Verify interactions between multiple components and API flows.

---

## Troubleshooting

-   **Backend not starting**: Check `backend/logs/app.log` for errors. Verify `backend/.env` configuration.
-   **Frontend not connecting**: Ensure `BACKEND_URL` is correctly set in Streamlit Cloud secrets.
-   **Scheduler not running**: Check `ENABLE_SCHEDULER=True` in `backend/.env`. Review backend logs for APScheduler messages.
-   **Email not sending**: Verify `SMTP_ENABLED=True` and all SMTP credentials in `backend/.env`.

---

## Changelog

### v2.0 (Current) - Feature Blueprint Implementation

-   ✨ **User Profile Management**: Comprehensive profile creation and updates.
-   ✨ **Personalized Job Recommendations**: AI-powered matching based on skills, location, and experience.
-   ✨ **Skill Gap Analysis**: Identify missing skills and get learning recommendations.
-   ✨ **Enhanced Job & Application Tracking**: Detailed job fields, application status validation, and job status updates.
-   ✨ **Analytics Dashboard**: Summary metrics, daily application goals, and status breakdown.
-   ✨ **Automated Job Ingestion**: Scheduled scraping from external APIs.
-   ✨ **Daily Notifications**: Morning briefings with recommendations, evening summaries with progress.
-   ✨ **Robust Error Handling**: Structured API error responses and improved logging.
-   ✨ **Comprehensive Health Check**: API endpoint for system health monitoring.
-   ✨ **Zero-Cost Cloud Deployment**: Optimized for Render (backend) and Streamlit Cloud (frontend).
-   ✨ **Cleaned Codebase**: Consolidated dependencies, removed obsolete scripts and Docker files.
-   ✅ **Automated Testing**: Integrated `pytest` with GitHub Actions for continuous validation.

### v1.1 (Previous) - Initial Blueprint

-   Initial project structure and basic features.

---

## License

MIT License - see [LICENSE](LICENSE) file

---

**Built with ❤️ for job seekers everywhere**