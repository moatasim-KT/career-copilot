# Design Document

## Overview

The Career Co-Pilot is a full-stack web application that provides intelligent job tracking and career guidance. The system follows a three-tier architecture with a FastAPI backend, Streamlit frontend, and SQLite/PostgreSQL database. The design emphasizes modularity, scalability, and cost-efficiency while delivering proactive, AI-powered career assistance.

### Key Design Principles

1. **Separation of Concerns**: Clear boundaries between API, business logic, and data layers
2. **Modularity**: Independent services that can be developed and tested separately
3. **Extensibility**: Plugin architecture for adding new job sources and notification channels
4. **Cost Efficiency**: Designed to operate within free-tier limits where possible
5. **User Privacy**: User data isolation and secure authentication
6. **Graceful Degradation**: Optional features degrade gracefully when dependencies are unavailable

## Architecture

### High-Level Architecture

Theyers:

**Frontend Layer (Streamlit Dashboard)**
- Authentication UI
- Job Management Interface
- Application Tracking
- Analytics Visualization
- Profile Management

**Backend Layer (FastAPI Application)**
- API Endpoints for all operations
- Business Logic Services (Recommendation Engine, Skill Gap Anae)
- Scheduled Tasks (APSchedule)

**Data Layer (Database)**
- SQLite for development
- PostgreSQL for production
- Three main tables: users, jobs, applications

**External Services**
- Job APIs (Adzuna, Indeed, etc.) - optional
- SMTP Email Service (Gmail, SendGrid, etc.)

### Technology Stack

**Backend:**
- FastAPI 0.104+ (REST API framework)
- SQLAlchemy 2.0+ (ORM)
- Pydantic 2.0+ (data validation)
- APScheduler 3.10+ (task scheduling)
- Python 3.9+

**Frontend:**
- Streamlit 1.28+ (web UI framework)
- Plotly (data visualization)
- Requests (HTTP client)

**Database:**
- SQLite (development)
- PostgreSQL (production)

## Components and Interfaces

### 1. Data Models

#### User Model
- id: int (primary key)
- username: str (unique, indexed)
- email: str (unique, indexed)
- hashed_password: str
- skills: JSON array
- preferred_locations: JSON array
- experience_level: str (junior, mid, senior)
- created_at, updated_at: datetime
- Relationships: jobs (one-to-many), applications (one-to-many

**Design Rationale:** JSON columns provide flexibility for skis.

l
- id: int (primary key)
- user_id: int (foreign key)
- company, title: str (indexed)
- location, description, requirements: str
- salary_range, job_type, remote_option: str
- ty
r
- source: str (manua)

- date_appli
- created_at, updated_at: datetime
- Relationships: user ()

**Design Rationale:** Indexed companyics.

odel
- id: int (pr)
- user_id, job_id: int (foreign keys)
- status: str (interested, ap
- applied_date, intervie
ext
- created_at,e
- Relationships: user 

t.

### 2. API Layer




- Request: usernamssword
l
- Creates new ussword

**POST /api
- Request: usernd
- Response: JWT access_token and usct
- Returns token for subsequent ats

#### Profile Endpoints

**GET /api/v1/profile**
- Headers: Authorization
- Response: user profilevel

**PUT /api/v1/profi
- Headers: Authoriz
- Request: skills, preferred_locatinal)
- R profile

#### Job Endpoints

**GET /api/v1/jobs**
- Query params: skip, limit
er's jobs

**POST /a**
- Request:fields
- Response: creaobject

**PUT /api/v1/jobs/{job_id
- Request: any job fieldte
- Response: updatject

**DELETE /api/v1/jobs/ob_id}**
- Response: success m

#### Application Endpoints

**GET /api/v1/applications
- Query param limit
- Response: array of user's applications wits

**POST /api/v1/**
- Request: job_id, status, notes
- Response: created application object

**PU*
- Request: status, tes
- Response: up

###

**GET /api/v1/recommes**
- Query params: limit (default 5)
- Response: array of jobs with match_score, s
- Only returns unapplied jobs

dpoints

**GET /ap
- Response: user_s

#### Analytics Endpoints

**GET /api/v1/analytics/summary**
- Response: total_jobs, tofers

### 3. Business Logic Services

#### RecommendationEngin

**Pu

**Algorithm:**
1. Tech Stacills
2. tion
le
4. Return score cappe00

**Methods:**
- calculate_match_score(job, user) t


bility.



**P

*thm:**
1. Aggregate all tech jobs
2. Count frequencyll
3. Identify skills ns
4percentage


*ds:**
- analyze_skt
- _generate_recommend

**Design Rationale:** Fric.

###

**Purpose:** Ingest jobs frplicate.

**Method:**
-
- deduplicate_jobs(ex

*sitively.

**Design bloat.

#### NotificationService

**Purpose:*es.

**Methods:**
- send_morning_bries)
- sts)
-dy)



**Design Rationale:** SMTP-based for flexgured.

### 4. Scheduled Tasks

**Implementation:** APTrigger

**Tasks:**
1. ly
   - Scrapes jobs for each user based 
s
   - Addsed"

2. send_mornily
   - Generates top 5 
   - Sends email wores

3. send_evening_summary - Runs at  daily
   - Calculates daily statisd)
 ary

ag.

###nents



*

**Features:**
- Token management (set, clear)
-tion

- Session reuse for con

e

age:**
- Metrics cards (job)
- Rns)
- Quick navigation

*
- Job list withs
- A
ions
- Apply button (creattion)

**Applications Page:**
r
- Statusropdown
-
- Date tracking

**Profile Page:**
- Skill
- Locations input
- Experience level dropdown
- Save button

**Analytics Page:**
- Status breakdown visualization
- Application 

- Top missing skills

**Design Rationale:** Single-page app s.

## Data Models

### Database Schema

**users table:**
- Prid
- Unique indexes: mail

- Cascade delete to jobs ications

**jobs table:**
- Primary key: id
- Foreign key:

- JSON column: tectack

**applications table:**
- Primary key: id
- Foreign keys: )
us

### Data Relation

- User (1) to Jobs (N)
N)
)



## Error Handling

### Error Categories


2. **Authentication Errors (401)** - Inv
3. **Authorization Errors (4a
4. **Not Found Errors (404)** - Resource doesn't exist
5. **Server Errors (5s

### Error Respt

All errors return JSON with: detamp

### Error Handling Strategy

codes

**Service Layer:** Try-catch around eging

**Frontend:** User-friendly messages, retry mechan

tegy

### Uni

**Coverage Targe*
- Models: 90%+ )

e)

**Key Test Case
- Recommendatiouts
- SkillGapAn
- JobSion
low

### Integratioests

s:**
1. End-to-end user registra
2. Create Apply
3. Update es
4. Scheduled tas
5. Email notificatiMTP)

### Performance Testing

**Metrics:**
- API response tim)
- Recom100 jobs
- Skill gap analys500 jobs

## Security Consider

###n
- Bcrypt passwor2)
- JWT tokens with 24-hour on
- Secure token storage

### Authorization
- User ID from JWT token
- All queries filtered by user_id
- Ness

on
- Pydantic 
- SQL injection prevented b ORM
- XSS prevention 

### Data Privacy
- User data isolated by user_id
- Earily
- API keys in environment 

## Deployment Architecture

### Development Environment
- SQLite database
- Backend: uvicorn --reload
- Frontend: streamun
d
- Email: disabled (console logs)

### Productiment
- PostgreSQL database
orkers
- Frontend: streamlit (containerized)
- Scheduler: enabled
- Email: SMTP configured
- Reverse proxy: nginx
t

### Configuration Management

Environment varir:
- DATABASE_U
- JWT_SECRET_KEY
- ENABLE_SCHEDULER
- ENABLE_JOB_SCRAPING
- JOB_API_KEY
rd)
- API_PORT, FRONTEND_PT

## Performance Optimization

### Database Optimization
- Indexes on frequently queried columns
- Connectioing

- Pagination forlt sets

### Caching Strategy
- User profile cached in JWT token
- Recommendations cachedr
- Skill gap analysis cacheours
- Cache invalidatio

### API Optimization
- Async endpoints where possible
- Batch operations ates
- Compression 


- Session state
inputs
- Lazy loading for large lists
- Optimistic UI updates

## Monitoring and Observability

### Logging
gs
- Log levels: D

- Scheduled task execution logs

### Metrics
- API request count and latency
- Database query performan
ate
- User activity metrics

### Health Checks
- GET /andpoint
- Databa
- Scheduler status check
ility



### Phase 5: Advanced Features (Post-MVP)
- Real-time job alerts via Wet
- Resume par
tions
- Salary negotiation insights
- Career path visualization
- Integration with LinkedIn
- Mobile app
- Multi-lort

### Scalability Considerations
- Microservices architecture
- Message queueis)
s)
- Read replicas for database

- Hcer
