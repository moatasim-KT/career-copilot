# Career Copilot Project Overview

This document provides an overview of the Career Copilot project, its architecture, how to set up and run it, and key development conventions.

## Project Purpose

Career Copilot is an AI-powered career management tool designed to assist users with various aspects of their job search and career development. Its features include:

*   **Dashboard:** Quick overview of job search progress.
*   **Jobs:** Tracking of job applications.
*   **Recommendations:** Personalized job recommendations.
*   **Analytics:** Detailed job search performance analysis.
*   **Skill Gap:** Identification of skill gaps and learning recommendations.
*   **Content Generation:** AI-powered cover letter and resume summary generation.
*   **Interview Practice:** AI-powered interview practice.

## Technologies and Architecture

The project follows a monorepo structure with distinct backend and frontend components:

*   **Backend:** Developed using Python with the FastAPI framework.
*   **Frontend:** Developed using Node.js with the Next.js framework.

## Building and Running the Application

### Prerequisites

*   Python 3.9+
*   Node.js 16+
*   Docker (optional)

### Installation

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
    # Fill in the .env file with your credentials
    ```

3.  **Frontend Setup:**
    ```bash
    cd frontend
    npm install
    ```

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

## Development Conventions

*   **Pre-commit Hooks:** The project utilizes `pre-commit` hooks for code quality and consistency, configured via `.pre-commit-config.yaml`.
*   **CI/CD Workflows:** Continuous Integration and Continuous Deployment workflows are defined in the `.github/workflows/` directory.
*   **Makefile:** Common development tasks and commands are likely automated using the `Makefile`.
