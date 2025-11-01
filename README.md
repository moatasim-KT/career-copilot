# 🚀 Career Copilot

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **AI-Powered Job Application Tracking and Career Management System**

Career Copilot is an intelligent, enterprise-grade career management platform designed to help job seekers streamline their job search, track applications, prepare for interviews, and receive personalized career guidance through AI-powered insights.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture & Design](#️-architecture--design)
- [Components & Modules](#-components--modules)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [External APIs & Services](#-external-apis--services)
- [Configuration](#️-configuration)
- [Usage & Functionality](#-usage--functionality)
- [API Documentation](#-api-documentation)
- [Development Guidelines](#-development-guidelines)
- [Troubleshooting](#-troubleshooting)
- [Production Deployment](#-production-deployment)
- [Additional Resources](#-additional-resources)

---

## 🎯 Project Overview

### What is Career Copilot?

Career Copilot is a comprehensive career management platform that transforms the job search experience. It combines a modern web stack (FastAPI and Next.js) with powerful AI capabilities to provide intelligent job discovery, application tracking, and career development tools. It helps users manage their career journey with features like personalized job recommendations, tailored resume and cover letter generation, interview practice, and insightful analytics—all in one place.

### Key Features

#### Core Functionality
- **📊 Application Tracking**: Manage the entire job application lifecycle with a Kanban-style board (Interested, Applied, Interview, Offer, etc.).
- **🎯 Smart Job Recommendations**: AI-powered job matching based on user skills, experience, and preferences.
- **📝 AI Content Generation**: Automatically generate resumes and cover letters tailored to specific job postings.
- **🎤 Interview Practice**: Interactive, AI-driven mock interviews with real-time feedback.
- **📈 Analytics Dashboard**: Visualize application progress, success rates, and market trends.
- **🔍 Job Search & Scraping**: Discover jobs from multiple sources like LinkedIn, Indeed, and Adzuna.
- **🔔 Smart Notifications**: Receive customizable email alerts for deadlines, follow-ups, and new job matches.

#### Advanced Features
- **🤖 Multi-LLM Support**: Integrates with OpenAI (GPT-4), Groq (Llama 3), Anthropic (Claude), and Google (Gemini).
- **💾 Vector Storage**: Utilizes ChromaDB for semantic search and advanced job matching.
- **🔐 Enterprise Security**: Features OAuth2, JWT authentication, and Role-Based Access Control (RBAC).
- **📤 Export & Backup**: Automated database backups and data export capabilities.
- **⚡ Background Task Processing**: Uses Celery for asynchronous jobs like web scraping and sending emails.

### Target Audience

- **Job Seekers**: Professionals actively looking for new career opportunities.
- **Career Changers**: Individuals transitioning into new fields, especially data science, ML, or AI.
- **Recent Graduates**: Entry to mid-level candidates navigating the tech job market.
- **European Job Market**: Optimized for positions in Germany, the Netherlands, France, the UK, and other EU countries.

### Technology Highlights

- **Modern Stack**: FastAPI + Next.js + PostgreSQL
- **AI Integration**: OpenAI GPT-4, Groq (Llama 3), Google Gemini
- **Real-time Updates**: WebSocket support for live notifications
- **Scalable Architecture**: Async operations, background tasks with Celery
- **Secure**: OAuth 2.0, JWT authentication, encrypted API keys
- **Production-Ready**: Docker support, monitoring with Prometheus/Grafana

---

## 🏗️ Architecture & Design

### High-Level Architecture

Career Copilot follows a modern, decoupled architecture with a clear separation of concerns between the frontend and backend.

-   **Frontend**: A Next.js (React) single-page application that provides a rich, interactive user interface.
-   **Backend**: A FastAPI (Python) application that serves a RESTful API for all business logic, data processing, and AI integrations.
-   **Database**: A PostgreSQL database for primary data storage.
-   **Cache**: Redis for caching frequently accessed data and managing sessions.
-   **Task Queue**: Celery with a Redis broker for handling long-running, asynchronous tasks.
-   **Vector Store**: ChromaDB for storing embeddings and performing semantic searches.

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│  - React Components - TypeScript - TailwindCSS - Recharts  │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / WebSocket
┌────────────────────▼────────────────────────────────────────┐
│                  API Layer (FastAPI)                        │
│  - Endpoints - Validation - Authentication - Rate Limiting  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Service Layer                             │
│  - Business Logic - AI Services - External Integrations     │
│  - Job Service - Analytics - Email - Content Generation     │
└─────┬──────────────┬──────────────┬────────────────────┬────┘
      │              │              │                    │
┌─────▼────┐  ┌─────▼─────┐  ┌────▼─────┐  ┌──────────▼─────┐
│PostgreSQL│  │   Redis   │  │ ChromaDB │  │  External APIs │
│ (Primary)│  │  (Cache)  │  │ (Vector) │  │ OpenAI, Groq   │
└──────────┘  └───────────┘  └──────────┘  │ LinkedIn, etc. │
                                            └────────────────┘
┌─────────────────────────────────────────────────────────────┐
│              Background Workers (Celery)                    │
│  - Job Scraping - Email Sending - Report Generation         │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

-   **Repository Pattern**: Abstracting the data access layer with SQLAlchemy repositories to decouple business logic from data storage.
-   **Service Layer Pattern**: Encapsulating business logic within dedicated service classes for better organization and reusability.
-   **Dependency Injection**: Leveraging FastAPI's built-in dependency injection system to manage dependencies and improve testability.
-   **Factory Pattern**: Dynamically instantiating LLM services based on configuration, allowing for flexible AI model selection.

### Directory Structure

```
career-copilot/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/                # API endpoints (v1 versioning)
│   │   ├── core/               # Core functionality (config, db, logging)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic data validation schemas
│   │   ├── services/           # Business logic services
│   │   ├── repositories/       # Data access layer
│   │   ├── tasks/              # Celery background tasks
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # Database migrations
│   └── tests/                  # Backend tests
├── frontend/                   # Next.js React frontend
│   ├── src/
│   │   ├── app/                # Next.js 14 app directory
│   │   ├── components/         # Reusable React components
│   │   ├── lib/                # Utility functions and helpers
│   │   └── hooks/              # Custom React hooks
│   └── public/                 # Static assets
├── deployment/                 # Deployment configurations (Docker, Nginx)
├── monitoring/                 # Monitoring configs (Prometheus, Grafana)
├── scripts/                    # Automation and utility scripts
├── .env.example                # Environment variable template
└── pyproject.toml              # Python project configuration and dependencies
```

---

## 🛠️ Components & Modules

### Technology Stack

| Category      | Technology                                       |
|---------------|--------------------------------------------------|
| **Backend**   | FastAPI, SQLAlchemy, Pydantic, Celery            |
| **Frontend**  | Next.js, React, TypeScript, TailwindCSS          |
| **Database**  | PostgreSQL (Production), SQLite (Development)    |
| **AI/ML**     | OpenAI, Groq, ChromaDB, Sentence Transformers    |
| **DevOps**    | Docker, Nginx, Prometheus, Grafana               |
| **Testing**   | Pytest, Jest, React Testing Library              |

### Backend Components

| Component         | Responsibility                                                                    |
|-------------------|-----------------------------------------------------------------------------------|
| **API (FastAPI)** | Handles all incoming HTTP requests, performs data validation, and manages routing.    |
| **Services**      | Contains the core business logic for features like job management and AI processing. |
| **Repositories**  | Abstracts database interactions, providing a clean API for data access.           |
| **Models**        | Defines the SQLAlchemy ORM models, representing the database schema.              |
| **Schemas**       | Defines the Pydantic models for data validation and serialization.                |
| **Celery Tasks**  | Manages asynchronous background jobs such as web scraping and email notifications.  |

### Frontend Components

| Component          | Responsibility                                                                   |
|--------------------|----------------------------------------------------------------------------------|
| **App Router**     | Handles routing and layouts for the Next.js application.                         |
| **Components**     | Contains reusable UI elements like buttons, cards, and modals.                   |
| **Hooks**          | Implements custom React hooks for managing state and side effects.               |
| **Lib**            | Provides utility functions, API clients, and type definitions.                   |
| **State Mgmt**     | Manages global application state using React Context or a dedicated library.       |

---

## 📦 Prerequisites

### Required Software

| Software   | Minimum Version | Purpose              |
|------------|-----------------|----------------------|
| Python     | 3.11+           | Backend runtime      |
| Node.js    | 18.x+           | Frontend runtime     |
| npm        | 9.x+            | Package management   |
| PostgreSQL | 13+             | Production database  |
| Redis      | 6.x+            | Caching & task queue |
| Git        | 2.x+            | Version control      |

### Operating System Requirements

-   **macOS**: 10.15+ (Catalina or later)
-   **Linux**: Ubuntu 20.04+, Debian 11+, or equivalent
-   **Windows**: Windows 10/11 with WSL2 (recommended)

### Required Accounts & API Keys

To use all features, you will need accounts and API keys for the following services (see the [External APIs & Services](#-external-apis--services) section for more details):

-   **Essential**: An API key from either **OpenAI** or **Groq** for core AI functionality.
-   **Optional**: Keys for Anthropic, Google Gemini, LinkedIn, Adzuna, and SendGrid to enable enhanced features.

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/career-copilot.git
cd career-copilot
```

### 2. Set Up the Backend

```bash
# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -e ".[dev,ai,all]"

# Install pre-commit hooks for code quality
pre-commit install
```

### 3. Set Up the Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install frontend dependencies
npm install

# Return to the root directory
cd ..
```

### 4. Configure the Environment

```bash
# Copy the example environment file
cp .env.example .env

# Generate a secure JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Open the .env file and add the generated key to JWT_SECRET_KEY
# Also, add your API keys for OpenAI, Groq, or other services.
```

### 5. Set Up the Database

For development, you can use the default SQLite database. To set it up, run the following commands:

```bash
# Create the data directory
mkdir -p data

# Apply database migrations
cd backend
alembic upgrade head
cd ..
```

For production, it is recommended to use PostgreSQL. See the [Production Deployment](#-production-deployment) section for more details.

---

## 🔌 External APIs & Services

This project integrates with several external APIs for its core functionality. You will need to obtain API keys for these services and add them to your `.env` file.

### LLM Providers

#### 1. OpenAI (GPT-4, GPT-3.5)
-   **Purpose**: High-quality text generation, analysis, and reasoning.
-   **Get API Key**: Visit the [OpenAI Platform](https://platform.openai.com/api-keys) to create an API key.
-   **Configuration**:
    ```bash
    OPENAI_API_KEY=sk-...your-key-here...
    ```

#### 2. Groq (Llama 3.1, Mixtral)
-   **Purpose**: Fast and cost-effective alternative to OpenAI.
-   **Get API Key**: Visit the [Groq Console](https://console.groq.com/keys) to create an API key.
-   **Configuration**:
    ```bash
    GROQ_API_KEY=gsk_...your-key-here...
    ```

### Job Boards

#### 3. Adzuna API
-   **Purpose**: Job search aggregation.
-   **Get Credentials**: Sign up at the [Adzuna Developer Portal](https://developer.adzuna.com/).
-   **Configuration**:
    ```bash
    ADZUNA_APP_ID=your_app_id
    ADZUNA_APP_KEY=your_api_key
    ```

### Email Services

#### 4. SendGrid
-   **Purpose**: Transactional email delivery for notifications.
-   **Get API Key**: Create a free account at [SendGrid](https://sendgrid.com/) and generate an API key.
-   **Configuration**:
    ```bash
    SENDGRID_API_KEY=SG....your-key-here...
    ```

### OAuth Providers

#### 5. Google OAuth
-   **Purpose**: Social login and Google account integration.
-   **Setup**: Create an OAuth 2.0 Client ID in the [Google Cloud Console](https://console.cloud.google.com/).
-   **Configuration**:
    ```bash
    GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
    GOOGLE_CLIENT_SECRET=your_client_secret
    ```

---

## ⚙️ Configuration

Career Copilot is configured using environment variables. Copy the `.env.example` file to `.env` and customize it to your needs.

### Core Application Settings
-   `ENVIRONMENT`: The application environment (`development`, `production`, or `testing`).
-   `DEBUG`: Enable or disable debug mode.
-   `API_HOST`: The host for the backend API.
-   `API_PORT`: The port for the backend API.

### Database Configuration
-   `DATABASE_URL`: The connection string for your database (e.g., `sqlite:///./data/career_copilot.db` or `postgresql://user:password@host:port/dbname`).

### Authentication & Security
-   `JWT_SECRET_KEY`: A secret key for signing JWT tokens (must be at least 32 characters).
-   `JWT_ALGORITHM`: The algorithm to use for JWT signing (default: `HS256`).
-   `JWT_EXPIRATION_HOURS`: The number of hours a JWT token is valid.

### AI/LLM Configuration
-   `OPENAI_API_KEY`: Your API key for OpenAI services.
-   `GROQ_API_KEY`: Your API key for Groq services.
-   `CHROMA_PERSIST_DIRECTORY`: The directory to store ChromaDB data.

### Email & Notifications
-   `SMTP_ENABLED`: Enable or disable email notifications.
-   `SENDGRID_API_KEY`: Your API key for SendGrid (if using).

---

## 📖 Usage & Functionality

### Starting the Application

To run the application in development mode, you can use the provided `Makefile` for convenience.

```bash
# Start both the backend and frontend servers
make run-dev
```

Alternatively, you can run them separately:

```bash
# Terminal 1: Start the backend server
make run-backend

# Terminal 2: Start the frontend server
make run-frontend
```

Once running, the application will be available at the following URLs:

-   **Frontend UI**: `http://localhost:3000`
-   **Backend API Docs**: `http://localhost:8002/docs`

### Running Tests

To run the entire test suite, use the following command:

```bash
make test
```

---

## 🐛 Troubleshooting

### `ModuleNotFoundError`
-   **Problem**: You see an error like `ModuleNotFoundError: No module named 'app'`.
-   **Solution**: Make sure you have activated your Python virtual environment (`source venv/bin/activate`) and have installed the project in editable mode (`pip install -e .`).

### Database Connection Error
-   **Problem**: The application fails to connect to the database.
-   **Solution**: Ensure that your `DATABASE_URL` in the `.env` file is correct and that the database server is running. If using the default SQLite setup, make sure you have run `alembic upgrade head`.

### Frontend Can't Connect to Backend
-   **Problem**: The frontend shows a "Network Error" or CORS-related errors.
-   **Solution**: Verify that the backend server is running and that the `CORS_ORIGINS` variable in your `.env` file includes the frontend URL (`http://localhost:3000`).

---

## 🚀 Production Deployment

### Pre-Deployment Checklist

-   [ ] Set `ENVIRONMENT=production` and `DEBUG=false` in your environment variables.
-   [ ] Use a robust database like PostgreSQL instead of SQLite.
-   [ ] Generate a new, strong `JWT_SECRET_KEY`.
-   [ ] Configure `CORS_ORIGINS` to only allow your production frontend domain.
-   [ ] Set up a reverse proxy like Nginx to handle HTTPS and serve static files.

### Deployment Options

-   **Render**: The project includes a `render.yaml` file for easy deployment on Render.
-   **Docker Compose**: Use the provided `docker-compose.yml` file in the `deployment/docker` directory to deploy the application with Docker.
-   **Kubernetes**: For large-scale deployments, you can use the Kubernetes manifests in the `deployment/k8s` directory.

---

## Additional Resources

-   **License**: This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
-   **Contributing**: We welcome contributions! Please see the `CONTRIBUTING.md` file for more information.