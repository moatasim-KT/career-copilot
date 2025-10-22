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
- Business Logic Services (Recommendation Engine, Skill Gap Analyzer, Content Generator, Interview Practice System)
- Real-time Services (WebSocket handlers, notification broadcasting)
- Scheduled Tasks (APScheduler)
- Authentication Services (JWT, OAuth providers)

**Data Layer (Database)**
- SQLite for development
- PostgreSQL for production
- Enhanced schema: users, jobs, applications, feedback, analytics, interview_sessions
- Redis for caching and real-time data

**External Services**
- Job APIs (Indeed, LinkedIn, Glassdoor, Adzuna) - enhanced integration
- LLM Services (OpenAI, Anthropic, local models) - for parsing and content generation
- SMTP Email Service (Gmail, SendGrid, etc.)
- OAuth Providers (Google, LinkedIn, GitHub)
- File Storage (local, S3, Google Drive) - for resume uploads

### Technology Stack

**Backend:**
- FastAPI 0.104+ (REST API framework)
- SQLAlchemy 2.0+ (ORM)
- Pydantic 2.0+ (data validation)
- APScheduler 3.10+ (task scheduling)
- WebSockets (real-time communication)
- Authlib 1.2+ (OAuth integration)
- OpenAI/Anthropic SDK (LLM integration)
- PyPDF2/pdfplumber (resume parsing)
- BeautifulSoup4 (web scraping)
- Redis 4.0+ (caching and sessions)
- Python 3.9+

**Frontend:**
- Streamlit 1.28+ (web UI framework)
- Plotly (data visualization)
- Requests (HTTP client)
- Streamlit-WebRTC (real-time features)
- File uploader components

**Database:**
- SQLite (development)
- PostgreSQL (production)
- Redis (caching, real-time data)

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
- oauth_provider: str (google, linkedin, github, null)
- oauth_id: str (external user ID)
- profile_picture_url: str
- created_at, updated_at: datetime
- Relationships: jobs (one-to-many), applications (one-to-many), feedback (one-to-many), interview_sessions (one-to-many)

**Design Rationale:** JSON columns provide flexibility for skills and locations. OAuth fields enable social authentication.

#### Job Model
- id: int (primary key)
- user_id: int (foreign key)
- company, title: str (indexed)
- location, description, requirements: str
- salary_range, job_type, remote_option: str
- tech_stack: JSON array
- responsibilities: text
- source: str (manual, scraped, linkedin, indeed, glassdoor)
- source_url: str
- date_applied: datetime
- match_score: float (calculated field)
- created_at, updated_at: datetime
- Relationships: user (many-to-one), applications (one-to-many)

**Design Rationale:** Indexed company/title for deduplication. Multiple source tracking for comprehensive job aggregation.

#### Application Model
- id: int (primary key)
- user_id, job_id: int (foreign keys)
- status: str (interested, applied, interview, offer, rejected, accepted, declined)
- applied_date, interview_date, offer_date: datetime
- notes: text
- cover_letter_id: int (foreign key to content_generation)
- created_at, updated_at: datetime
- Relationships: user (many-to-one), job (many-to-one), cover_letter (many-to-one)

**Design Rationale:** Status tracking enables pipeline management and analytics. Links to generated content.

#### User Feedback Model
- id: int (primary key)
- user_id: int (foreign key)
- feedback_type: str (recommendation, skill_gap, content_generation, interview_practice)
- target_id: int (job_id, skill_name, session_id, etc.)
- rating: int (1-5 or thumbs up/down)
- comments: text
- created_at: datetime
- Relationships: user (many-to-one)

**Design Rationale:** Enables machine learning feedback loop for improving AI recommendations.

#### Interview Session Model
- id: int (primary key)
- user_id: int (foreign key)
- job_id: int (foreign key, optional)
- session_type: str (general, job_specific, behavioral, technical)
- questions_asked: JSON array
- user_responses: JSON array
- ai_feedback: JSON object
- overall_score: float
- duration_minutes: int
- created_at: datetime
- Relationships: user (many-to-one), job (many-to-one, optional)

**Design Rationale:** Structured storage for interview practice data and progress tracking.

#### Resume Upload Model
- id: int (primary key)
- user_id: int (foreign key)
- filename: str
- file_path: str
- parsed_data: JSON object
- parsing_status: str (pending, completed, failed)
- extracted_skills: JSON array
- extracted_experience: str
- created_at: datetime
- Relationships: user (many-to-one)

**Design Rationale:** Supports resume parsing workflow with status tracking and extracted data storage.

#### Content Generation Model
- id: int (primary key)
- user_id: int (foreign key)
- job_id: int (foreign key, optional)
- content_type: str (cover_letter, resume_tailoring, email_template)
- generated_content: text
- user_modifications: text
- generation_prompt: text
- created_at: datetime
- Relationships: user (many-to-one), job (many-to-one, optional)

**Design Rationale:** Tracks AI-generated content with user modifications for learning and reuse.

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
- Response: total_jobs, total_applications, interviews, offers

**GET /api/v1/analytics/trends**
- Query params: timeframe (30d, 90d, 1y)
- Response: skill_trends, salary_trends, job_posting_frequency

#### Resume and Parsing Endpoints

**POST /api/v1/resume/upload**
- Request: multipart/form-data with resume file
- Response: upload_id, parsing_status

**GET /api/v1/resume/{upload_id}/status**
- Response: parsing_status, extracted_data, suggestions

**POST /api/v1/jobs/parse-description**
- Request: job_url or description_text
- Response: extracted_tech_stack, requirements, parsed_data

#### Content Generation Endpoints

**POST /api/v1/content/cover-letter**
- Request: job_id, tone (professional, casual, enthusiastic)
- Response: generated_content, content_id

**POST /api/v1/content/resume-tailor**
- Request: job_id, resume_sections
- Response: tailored_sections, suggestions

**GET /api/v1/content/{content_id}**
- Response: content details, user_modifications

**PUT /api/v1/content/{content_id}**
- Request: user_modifications
- Response: updated content

#### Interview Practice Endpoints

**POST /api/v1/interview/start-session**
- Request: job_id (optional), session_type
- Response: session_id, first_question

**POST /api/v1/interview/{session_id}/answer**
- Request: answer_text, question_id
- Response: feedback, next_question

**GET /api/v1/interview/{session_id}/summary**
- Response: overall_score, detailed_feedback, improvement_areas

#### Feedback Endpoints

**POST /api/v1/feedback**
- Request: feedback_type, target_id, rating, comments
- Response: feedback_id

**GET /api/v1/feedback/summary**
- Response: user's feedback history and impact on recommendations

#### Real-time WebSocket Endpoints

**WS /api/v1/ws/notifications**
- Real-time job matches, application updates, system notifications

**WS /api/v1/ws/interview**
- Real-time interview practice sessions with voice support

#### OAuth Authentication Endpoints

**GET /api/v1/auth/oauth/{provider}/login**
- Redirects to OAuth provider (Google, LinkedIn, GitHub)

**GET /api/v1/auth/oauth/{provider}/callback**
- Handles OAuth callback and creates/links user account

**POST /api/v1/auth/oauth/disconnect**
- Request: provider
- Response: success message

### 3. Business Logic Services

#### RecommendationEngine

**Purpose:** Calculate job-to-user match scores using weighted algorithms.

**Algorithm:**
1. Tech Stack Match: Compare user skills with job tech_stack (50% weight)
2. Location Match: Compare user preferred_locations with job location (30% weight)
3. Experience Level Match: Compare user experience_level with job requirements (20% weight)
4. Return score capped at 100

**Methods:**
- calculate_match_score(job, user) -> float
- get_recommendations(user, limit) -> List[JobWithScore]
- update_algorithm_weights(feedback_data) -> None

**Design Rationale:** Weighted scoring provides flexibility and personalization.

#### SkillGapAnalyzer

**Purpose:** Identify missing skills and generate learning recommendations.

**Algorithm:**
1. Aggregate all tech_stack arrays from user's jobs
2. Count frequency of each skill using Counter
3. Identify skills present in jobs but missing from user profile
4. Calculate skill coverage percentage

**Methods:**
- analyze_skill_gaps(user) -> SkillGapReport
- _generate_recommendations(missing_skills) -> List[str]
- calculate_market_demand(skills) -> Dict[str, float]

**Design Rationale:** Frequency-based analysis identifies high-impact skills.

#### JobScraperService

**Purpose:** Ingest jobs from external APIs and deduplicate.

**Methods:**
- scrape_jobs(skills, locations, sources) -> List[Job]
- deduplicate_jobs(existing_jobs, new_jobs) -> List[Job]
- normalize_job_data(raw_job, source) -> Job

**Design Rationale:** Multi-source aggregation prevents vendor lock-in and reduces data bloat.

#### NotificationService

**Purpose:** Handle email notifications and real-time updates.

**Methods:**
- send_morning_briefing(user) -> bool
- send_evening_summary(user) -> bool
- broadcast_real_time_update(user_id, message) -> None
- send_job_alert(user, job, match_score) -> bool

**Design Rationale:** SMTP-based for flexibility, WebSocket for real-time features.

#### ResumeParserService

**Purpose:** Extract structured data from resume documents using LLM integration.

**Methods:**
- parse_resume(file_path) -> ParsedResumeData
- extract_skills(resume_text) -> List[str]
- extract_experience_level(resume_text) -> str
- suggest_profile_updates(parsed_data, current_profile) -> ProfileSuggestions

**Design Rationale:** LLM-powered parsing provides high accuracy with fallback to rule-based extraction.

#### ContentGeneratorService

**Purpose:** Generate personalized cover letters and resume modifications.

**Methods:**
- generate_cover_letter(user, job, tone) -> str
- tailor_resume(user, job, resume_sections) -> Dict[str, str]
- generate_email_template(user, job, template_type) -> str
- improve_content(original_content, feedback) -> str

**Design Rationale:** Template-based generation with LLM enhancement for personalization.

#### InterviewPracticeService

**Purpose:** Conduct AI-powered mock interviews with feedback.

**Methods:**
- start_session(user, job_id, session_type) -> InterviewSession
- generate_question(session_context, previous_answers) -> str
- evaluate_answer(question, answer, job_context) -> AnswerFeedback
- generate_session_summary(session) -> SessionSummary

**Design Rationale:** Contextual question generation with structured feedback for skill improvement.

#### WebSocketService

**Purpose:** Handle real-time communication and notifications.

**Methods:**
- connect_user(user_id, websocket) -> None
- broadcast_to_user(user_id, message) -> None
- handle_job_match_alert(user_id, job, match_score) -> None
- handle_application_update(user_id, application) -> None

**Design Rationale:** Real-time updates improve user engagement and responsiveness.

#### OAuthService

**Purpose:** Handle social authentication with multiple providers.

**Methods:**
- initiate_oauth_flow(provider) -> str (redirect_url)
- handle_oauth_callback(provider, code) -> UserData
- link_oauth_account(user_id, provider, oauth_data) -> bool
- disconnect_oauth_account(user_id, provider) -> bool

**Design Rationale:** Multi-provider support reduces friction in user onboarding.

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
