
# Deployment Guide

This guide provides instructions for deploying the Career Copilot application to a production environment.

## Prerequisites

- A server with Docker and Docker Compose installed.
- A domain name pointing to your server's IP address.

## 1. Configuration

### Environment Variables

Create a `.env` file in the root of the project and fill in the following environment variables:

```
# backend/.env
DATABASE_URL=postgresql://user:password@db:5432/career_copilot
JWT_SECRET_KEY=your-super-secret-jwt-key

# frontend/.env
NEXT_PUBLIC_API_URL=http://your-domain.com/api
```

### Nginx

Update the `nginx/nginx.conf` file with your domain name.

## 2. Build and Run with Docker Compose

```bash
docker-compose up -d --build
```

This will build the Docker images and start the backend, frontend, and database containers.

## 3. Database Migrations

Run the following command to apply database migrations:

```bash
docker-compose exec backend alembic upgrade head
```
