# System Architecture: Career Copilot

This document outlines the system architecture for the Career Copilot application, following the provided design framework.

### 1. Requirements Clarification

#### Functional Requirements
- **User Management**: User registration, authentication, and profile management.
- **Resume Management**: Upload, parse, store, and manage multiple resume versions.
- **Job Application Tracking**: Manually add and track job applications, including status, company, role, and date.
- **AI-Powered Insights**: Provide AI-driven feedback on resumes and generate tailored cover letters.
- **Async Task Processing**: Handle long-running tasks like resume analysis and email notifications in the background.
- **Email Notifications**: Send users updates on application statuses or reminders.

#### Non-Functional Requirements
- **Performance**: API response times should be under 200ms for most endpoints. Page loads should be under 2 seconds.
- **Scalability**: The system should be able to scale horizontally to support a growing user base (estimated 1M+ DAU).
- **Availability**: Target uptime of 99.9% (less than 9 hours of downtime per year).
- **Reliability**: No data loss for user-critical information like resumes and application data.
- **Consistency**: Strong consistency for core user and application data.
- **Security**: Secure handling of Personally Identifiable Information (PII) in resumes and user profiles. All data encrypted in transit and at rest.
- **Maintainability**: The codebase should be modular, well-documented, and easy to deploy.

#### Constraints
- **Technology Stack**: The architecture must leverage the existing stack: Python/FastAPI for the backend, Next.js for the frontend, PostgreSQL for the database, Redis for caching/messaging, and Docker/Kubernetes for deployment.

### 2. Capacity Estimation

#### Traffic Estimates
- **Daily Active Users (DAU)**: 1,000,000
- **Requests per user per day**: 50
- **Total daily requests**: 50,000,000
- **Average Requests Per Second (RPS)**: `50,000,000 / 86400 ≈ 580 RPS`
- **Peak RPS (3x average)**: `580 * 3 ≈ 1740 RPS`

#### Storage Estimates
- **Average data per user** (profiles, applications): 500KB
- **Average resume size**: 500KB
- **Total users**: 10,000,000
- **Primary DB Storage**: `10,000,000 * 500KB = 5 TB`
- **Object Storage (resumes)**: `10,000,000 * 500KB = 5 TB`
- **5-year projection**: Assuming linear growth, storage needs will scale with the user base.

#### Bandwidth Estimates
- **Average request/response size**: 10KB
- **Total bandwidth**: `580 RPS * 10KB ≈ 5.8 MB/s`

#### Memory/Cache Estimates
- **Cache 20% of hot DB queries**: Requires a cache size relative to the hot dataset, estimated around 10-20GB.
- **Session/User data in cache**: `1M DAU * 1KB/user = 1GB`

### 3. High-Level Architecture

```
                    ┌──────────────────┐
                    │      Client      │
                    │ (Next.js Web App)│
                    └────────┬─────────┘
                             │
                      ┌──────▼──────┐
                      │     CDN     │
                      │(Cloudflare) │
                      └──────┬──────┘
                             │
                    ┌────────▼────────┐
                    │  K8s Ingress    │
                    │ (Load Balancer) │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │ FastAPI Pod │    │ FastAPI Pod │    │ FastAPI Pod │
      │ (Web Server)│    │ (Web Server)│    │ (Web Server)│
      └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │   Cache   │    │Message Queue│  │  Object   │
      │  (Redis)  │    │(Celery/Redis)│  │  Storage  │
      └───────────┘    └─────┬─────┘    │   (S3/GCS)  │
                             │            └───────────┘
            ┌────────────────┼────────────────┐
            │                │                │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │  Primary  │    │  Read     │    │  Celery   │
      │ DB (Postgres)│    │  Replica  │    │  Worker Pod │
      └───────────┘    └───────────┘    └───────────┘
```

### 4. Component Design

- **Load Balancer**: A Kubernetes Ingress Controller (like Nginx or Traefik) manages external access to the services within the cluster, providing load balancing, SSL termination, and name-based virtual hosting.
- **Web/Application Servers**: The FastAPI backend runs in stateless Docker containers, orchestrated by Kubernetes. Auto-scaling is configured based on CPU and memory usage to handle traffic spikes.
- **Caching Layer**: Redis is used for caching frequently accessed data (e.g., user profiles, job listings) and for session management, reducing database load. The cache-aside pattern is the primary strategy.
- **Database**: A PostgreSQL database with a primary-replica setup. All write operations go to the primary instance, while read operations are distributed across one or more read replicas to improve performance. Alembic is used for schema migrations.
- **Message Queue**: Celery, using Redis as the message broker, manages asynchronous tasks. This decouples long-running operations (like resume parsing or AI analysis) from the main request-response cycle, improving API responsiveness.
- **Object Storage**: A service like AWS S3 or Google Cloud Storage is used to store large files, primarily user-uploaded resumes and other documents. This keeps the main database lean and leverages scalable, cost-effective storage.

### 5. Data Flow

#### Read Flow (Get Job Applications)
1. Client (Next.js app) sends a request to the API endpoint.
2. The request hits the K8s Ingress, which routes it to an available FastAPI pod.
3. The FastAPI server checks the Redis cache for the user's application list.
4. **Cache Hit**: The data is returned directly from Redis to the client.
5. **Cache Miss**: The server queries the PostgreSQL read replica for the data.
6. The server stores the result in Redis with a defined TTL (Time-To-Live).
7. The data is returned to the client.

#### Write Flow (Upload Resume)
1. Client sends the resume file to a dedicated upload endpoint.
2. Ingress routes the request to a FastAPI pod.
3. The server authenticates the user (via JWT) and validates the request.
4. The server uploads the file directly to Object Storage (S3/GCS).
5. Upon successful upload, the server writes the file's metadata (URL, user ID, etc.) to the primary PostgreSQL database.
6. The server publishes a `resume_uploaded` event to the Celery/Redis message queue.
7. A background Celery worker consumes the event and starts the asynchronous resume parsing and analysis task.
8. The server immediately returns a success response to the client, without waiting for the analysis to complete.

### 6. Scalability Strategies

- **Horizontal Scaling**: The use of Kubernetes allows for the horizontal scaling of stateless FastAPI pods and Celery worker pods based on demand.
- **Database Scaling**:
  - **Read Scaling**: Achieved by adding more PostgreSQL read replicas.
  - **Write Scaling**: If necessary in the future, the database can be sharded by `user_id` to distribute the write load across multiple database instances.
- **Microservices**: The current backend structure (e.g., `services`, `repositories`) is modular. If complexity grows, it can be broken down into microservices (e.g., `UserService`, `ResumeService`, `ApplicationService`) that can be scaled independently.

### 7. Availability & Reliability

- **Redundancy**: Kubernetes manages pod replication, ensuring that if one pod fails, another takes its place. The database uses a primary-replica setup for redundancy.
- **Fault Tolerance**: The system is designed to be fault-tolerant. If a background task fails, Celery can be configured to retry it. If a downstream service is unavailable, the impact is isolated.
- **Monitoring**: The existing monitoring stack (Prometheus, Grafana, Loki) is used to track system health, application metrics, and logs. Alerts are configured to notify the team of anomalies (e.g., high error rates, high latency).
- **Disaster Recovery**: Regular automated backups of the PostgreSQL database and object storage are stored in a separate geographic region to allow for recovery in case of a regional outage.

### 8. Security Architecture

- **Network Security**: The application is deployed within a Virtual Private Cloud (VPC). Kubernetes Network Policies and Security Groups restrict traffic between pods and services to only what is necessary.
- **Application Security**:
  - **Authentication**: JWTs are used for stateless authentication.
  - **Authorization**: Role-based access control (RBAC) is implemented in the API to ensure users can only access their own data.
  - **Transport Security**: All traffic is encrypted using HTTPS/TLS.
  - **Input Validation**: Pydantic models in FastAPI enforce strict input validation to prevent injection attacks.
- **Data Security**:
  - **Encryption**: All data is encrypted at rest (in the database and object storage) and in transit.
  - **Secrets Management**: Secrets (API keys, DB passwords) are managed using a secure secret store (like HashiCorp Vault or AWS/GCP Secrets Manager) and injected into the environment at runtime.

### 9. API Gateway Pattern

While currently managed by a K8s Ingress, a dedicated API Gateway (like Kong, Tyk, or AWS API Gateway) could be introduced as the system scales. This would centralize concerns like advanced rate-limiting, authentication, and request transformation, especially in a microservices architecture.

### 10. Caching Strategies

- **CDN Caching**: The Next.js frontend's static assets (JS, CSS, images) are cached at the edge by a CDN for fast global delivery.
- **Application Caching**: Redis is used to cache database query results, user session information, and the results of expensive computations.
- **Browser Caching**: Proper `Cache-Control` headers and ETags are used to leverage browser caching for frontend assets and API responses where appropriate.

### 11. Async Processing Pattern

Celery is used for all long-running and background tasks:
- **Resume Parsing/Analysis**: After a resume is uploaded, a task is queued to parse its content and run AI-based analysis.
- **Email Sending**: Sending welcome emails, notifications, and reminders is handled by background workers to avoid blocking API responses.
- **Data Aggregation**: Periodic tasks can be scheduled to aggregate data for analytics dashboards.

### 12. Data Consistency

- **Strong Consistency**: The primary PostgreSQL database ensures ACID compliance for all core user data, job applications, and resume metadata, guaranteeing strong consistency.
- **Eventual Consistency**: Data derived from background processing (e.g., resume analysis results) is eventually consistent. The UI may show a "processing" state until the background task is complete and the data is available.

### 13. Rate Limiting

Rate limiting is implemented as middleware in FastAPI to prevent abuse. Limits are applied per user/IP for sensitive or expensive endpoints (e.g., AI-powered generation).

### 14. Technology Stack

- **Frontend**: Next.js (React), Tailwind CSS
- **Backend**: Python, FastAPI, Celery
- **Database**: PostgreSQL (Primary DB), Redis (Cache, Message Broker)
- **Infrastructure**: Docker, Kubernetes, Nginx (as Ingress)
- **Cloud Provider**: Agnostic, but designed for AWS, GCP, or Azure.
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana, Loki

### 15. Deployment Strategy

- **CI/CD**: GitHub Actions are used to automate testing, building Docker images, and deploying to a Kubernetes cluster.
- **Environments**: Separate environments for development, testing, and production are maintained.
- **Deployment**: Blue-green or canary deployment strategies are used to release new versions with zero downtime. Database migrations (Alembic) are applied as part of the deployment pipeline before the new application version is rolled out.
