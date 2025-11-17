# Project Overview

Career Copilot is an AI-powered platform designed to automate and streamline the job search process for tech professionals targeting the European market. It provides a comprehensive suite of tools for intelligent job scraping, AI-driven content generation, and application tracking.

## Key Features

- **Intelligent Job Discovery**: Automated scraping from 9 major job boards (LinkedIn, Indeed, StepStone, etc.)
- **AI Resume Generation**: Tailored resumes optimized for specific job postings using GPT-4
- **Smart Cover Letters**: Personalized cover letters highlighting relevant experience
- **Application Tracking**: Comprehensive dashboard to manage all applications in one place
- **Job Matching**: AI-powered job recommendations based on your profile and preferences
- **Analytics & Insights**: Track application success rates, response times, and market trends
- **Smart Notifications**: Real-time alerts for new matching jobs and application updates
- **EU-Focused**: Specialized in the European tech market with visa sponsorship support

## Technology Stack

### Backend

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Cache**: Redis
- **Task Queue**: Celery
- **AI/ML**: OpenAI GPT-4, Anthropic Claude, ChromaDB

### Frontend

- **Framework**: Next.js (React)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **UI Components**: shadcn/ui
- **State Management**: React Context + Hooks

### Infrastructure

- **Containerization**: Docker & Docker Compose
- **Web Server**: Uvicorn (dev), Gunicorn (prod)
- **Reverse Proxy**: Nginx (production)
- **Monitoring**: Prometheus + Grafana

[[index]]