# Database Schema Documentation

## Overview

Career Copilot uses PostgreSQL with SQLAlchemy ORM. The database follows a normalized relational design with JSON fields for flexible data storage.

## Core Tables

### Users Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Relationships:**
- One-to-Many: `jobs`, `applications`, `saved_searches`
- One-to-One: `user_profile`

**Indexes:**
- `email` (unique)
- `created_at`

### Jobs Table

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    requirements TEXT,
    tech_stack JSONB,  -- Array of technologies
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(3) DEFAULT 'EUR',
    job_type VARCHAR(50),  -- full-time, part-time, contract
    remote_option VARCHAR(50),  -- remote, hybrid, onsite
    source VARCHAR(100),  -- linkedin, indeed, etc.
    source_id VARCHAR(255),  -- External ID from source
    url VARCHAR(1000) UNIQUE,
    posted_date DATE,
    application_deadline DATE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Relationships:**
- Many-to-One: `user`
- One-to-Many: `applications`, `job_views`

**Indexes:**
- `user_id`
- `source`, `source_id` (composite)
- `scraped_at`
- `tech_stack` (GIN index for JSONB)
- Full-text search index on `title`, `company`, `description`

### Applications Table

```sql
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,  -- saved, applied, interviewing, etc.
    applied_date DATE,
    notes TEXT,
    cover_letter TEXT,
    resume_version VARCHAR(100),
    application_url VARCHAR(1000),
    response_date DATE,
    interview_date DATETIME,
    offer_amount INTEGER,
    offer_currency VARCHAR(3) DEFAULT 'EUR',
    rejection_reason TEXT,
    interview_feedback JSONB,  -- Array of feedback objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_id, user_id)  -- One application per job per user
);
```

**Relationships:**
- Many-to-One: `job`, `user`
- One-to-Many: `interview_stages`

### User Profiles Table

```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    years_experience INTEGER,
    desired_title VARCHAR(255),
    desired_locations JSONB,  -- Array of preferred locations
    tech_stack JSONB,  -- Array of skills
    salary_expectation_min INTEGER,
    salary_expectation_max INTEGER,
    salary_currency VARCHAR(3) DEFAULT 'EUR',
    remote_preference VARCHAR(50),  -- remote, hybrid, onsite
    job_types JSONB,  -- Array of preferred job types
    visa_sponsorship_needed BOOLEAN DEFAULT false,
    preferred_companies JSONB,  -- Array of target companies
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Supporting Tables

### Saved Searches Table

```sql
CREATE TABLE saved_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    query VARCHAR(1000),
    filters JSONB,  -- Search filters
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Notifications Table

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,  -- job_match, application_update, etc.
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB,  -- Additional notification data
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Interview Stages Table

```sql
CREATE TABLE interview_stages (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE,
    stage_name VARCHAR(255) NOT NULL,  -- phone_screen, technical, onsite, etc.
    scheduled_date DATETIME,
    completed_date DATETIME,
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, completed, cancelled
    notes TEXT,
    feedback TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Database Relationships

```
users (1) ──── (∞) jobs
   │
   ├── (1) user_profiles
   │
   ├── (∞) applications ──── (∞) interview_stages
   │
   ├── (∞) saved_searches
   │
   └── (∞) notifications

jobs (1) ──── (∞) applications
```

## Key Design Patterns

### JSONB Fields for Flexibility
- `tech_stack`: Array of technologies
- `interview_feedback`: Structured feedback data
- `filters`: Search filter configurations

### Soft Deletes
- `is_active` boolean fields instead of hard deletes
- Preserves data integrity and audit trails

### Composite Unique Constraints
- `(job_id, user_id)` on applications table
- Prevents duplicate applications

### Indexing Strategy
- Foreign key indexes on all relationships
- GIN indexes on JSONB fields for efficient querying
- Full-text search indexes for job content
- Composite indexes for common query patterns

## Migration Strategy

Database changes are managed through Alembic migrations:

- **Location**: [[../../backend/alembic/versions/|backend/alembic/versions/]]
- **Naming**: `001_initial_schema.py`, `002_add_notifications.py`, etc.
- **Process**: `alembic revision --autogenerate -m "description"` then `alembic upgrade head`

## Performance Optimizations

### Query Optimization
- Use `selectinload` for eager loading relationships
- Implement pagination for large result sets
- Cache frequently accessed data in Redis

### Indexing
- Foreign key constraints automatically indexed
- Additional indexes on commonly filtered columns
- Partial indexes for active records only

### Connection Pooling
- SQLAlchemy connection pooling configured
- Async connections for high concurrency
- Connection health monitoring

## Data Validation

All data validation is handled at the application layer using Pydantic schemas:

- **Location**: [[../../backend/app/schemas/|backend/app/schemas/]]
- **Validation**: Automatic request/response validation
- **Type Safety**: Full type hints throughout the application

## Backup and Recovery

- **Automated Backups**: Daily PostgreSQL dumps
- **Point-in-Time Recovery**: WAL archiving enabled
- **Backup Storage**: Cloud storage with encryption
- **Testing**: Regular backup restoration tests

---

*See also: [[../architecture/ARCHITECTURE.md#database-schema|Architecture Database Section]], [[../../backend/app/models/|Database Models]]*"