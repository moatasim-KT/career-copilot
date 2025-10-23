# Career Copilot

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-username/career-copilot/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/your-username/career-copilot/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An AI-powered career management tool designed to assist users with various aspects of their job search and career development.

## Description

Career Copilot is a comprehensive platform built to streamline and enhance the job search experience. It leverages artificial intelligence to provide personalized insights and automation, helping users navigate the complexities of career development more effectively.

**Problem it solves:** The modern job market can be overwhelming, with countless listings, complex application processes, and the constant need to tailor applications. Career Copilot aims to simplify this by centralizing job management, offering intelligent recommendations, and automating tedious tasks.

**Key Features:**
*   **Dashboard:** Provides a quick overview of job search progress and key metrics.
*   **Job Tracking:** Efficiently track job applications, statuses, and important dates.
*   **Personalized Recommendations:** AI-driven job recommendations tailored to your profile and preferences.
*   **Skill Gap Analysis:** Identifies skill deficiencies and suggests relevant learning resources.
*   **Content Generation:** AI-powered assistance for crafting cover letters and resume summaries.
*   **Interview Practice:** AI-guided interview simulations to hone your skills.

**What makes it unique:** Career Copilot stands out by offering an integrated AI-first approach to career management, combining job tracking with intelligent automation and personalized guidance in a single, intuitive platform.

## Table of Contents

*   [Installation](#installation)
*   [Quick Start / Usage](#quick-start--usage)
*   [API Documentation](#api-documentation)
*   [Configuration](#configuration)
*   [Development](#development)
*   [Testing](#testing)
*   [License](#license)
*   [Authors & Acknowledgments](#authors--acknowledgments)
*   [Support & Contact](#support--contact)

## Installation

### Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.9+**: For the backend services.
*   **Node.js 16+**: For the frontend application.
*   **npm**: Node package manager, usually installed with Node.js.
*   **Docker (Optional)**: For containerized deployment.

### Step-by-step Installation Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/career-copilot.git
    cd career-copilot
    ```

2.  **Backend Setup:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows, use `.\venv\Scripts\activate`
    pip install -r requirements.txt
    cp .env.example .env
    # Open the newly created .env file and fill in your credentials (e.g., database URL, API keys).
    ```

3.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install
    ```

## Quick Start / Usage

### Running in Development Mode

To run the backend and frontend concurrently for development:

1.  **Start the Backend API:**
    Open a new terminal, navigate to the `backend` directory, activate your virtual environment, and run:
    ```bash
    cd backend
    source venv/bin/activate
    uvicorn app.main:app --reload --port 8000
    ```
    The backend API will be available at `http://localhost:8000`.

2.  **Start the Frontend Application:**
    Open another terminal, navigate to the `frontend` directory, and run:
    ```bash
    cd frontend
    npm run dev
    ```
    The frontend application will be available at `http://localhost:3000`.

### Running with `start.sh` (Production-like)

For a more production-like local setup, you can use the provided `start.sh` script:

```bash
./start.sh
```
This script starts both the backend (on `http://0.0.0.0:8000`) and the frontend using `npm run start`.

## API Documentation

The FastAPI backend automatically generates interactive API documentation. Once the backend is running, you can access it at:

*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

## Configuration

The project uses environment variables for configuration, primarily managed through a `.env` file in the `backend` directory. A `.env.example` file is provided as a template.

**Key Configuration Variables:**

*   `DATABASE_URL`: Connection string for your database (e.g., `sqlite:///./data/career_copilot.db` for SQLite, `postgresql://user:password@host:port/dbname` for PostgreSQL).
*   `JWT_SECRET_KEY`: A strong, random secret key for JWT token signing.
*   `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`: API keys for integrated AI/LLM services.
*   `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`: Credentials for the Adzuna job scraping API.
*   `SMTP_ENABLED`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`: SMTP settings for email notifications.
*   `SENDGRID_API_KEY`: API key for SendGrid email service (if used).
*   `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: URLs for the Celery message broker and result backend (e.g., Redis).
*   `REDIS_URL`: URL for Redis caching.
*   `CORS_ORIGINS`: Comma-separated list of allowed origins for CORS (e.g., `http://localhost:3000,http://localhost:8000`).

Refer to `backend/.env.example` and `backend/app/config/settings.py` for a complete list of configurable options.

## Development

### Setting up the Development Environment

1.  Follow the [Installation](#installation) steps.
2.  Ensure your `.env` file is correctly configured with development-specific settings.
3.  The project utilizes `pre-commit` hooks for code quality. Install them after setting up the backend virtual environment:
    ```bash
    pip install pre-commit
    pre-commit install
    ```

### Running Tests

*   **Backend Tests (Python):**
    ```bash
    cd backend
    source venv/bin/activate
    pytest
    ```
*   **Frontend Tests (JavaScript/TypeScript):**
    ```bash
    cd frontend
    npm test
    ```

### Building the Project

(Further build instructions for production deployment will be detailed in `docs/DEPLOYMENT_GUIDE.md`)

### Contributing

We welcome contributions to Career Copilot! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for guidelines on how to submit issues, propose features, and contribute code.

## Testing

The project includes a comprehensive test suite to ensure reliability and functionality.

*   **Unit Tests:** Verify individual components and functions.
*   **Integration Tests:** Ensure different modules and services interact correctly.
*   **End-to-End (E2E) Tests:** Simulate user flows to validate the entire application.

To run all tests, follow the instructions in [Running Tests](#running-tests).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors & Acknowledgments

*   **Main Contributors:** [Your Name/Team Name Here]
*   **Acknowledgments:** Special thanks to the open-source community and the creators of FastAPI, Next.js, SQLAlchemy, and all other libraries used in this project.

## Support & Contact

If you encounter any issues or have questions, please use the project's [issue tracker](https://github.com/your-username/career-copilot/issues).