# Requirements Document

## Introduction

The Career Co-Pilot is an intelligent, proactive system designed to transform the job search process from a passive, manual activity into a guided, goal-oriented workflow. The system aggregates job opportunities, actively assists users in applying for them, tracks progress, identifies skill gaps, and discovers long-term career insights. This requirements document covers the complete MVP implementation across all four phases of the blueprint.

## Glossary

- **Career Co-Pilot System**: The complete intelligent job tracking and recommendation platform
- **User Profile**: A collection of user preferences including skills, preferred locations, and experience level
- **Job Entity**: A job opportunity with associated metadata (company, title, location, tech stack, etc.)
- **Application Entity**: A record tracking a user's application to a specific job
- **Recommendation Engine**: The algorithmic component that matches jobs to user profiles
- **Skill Gap Analyzer**: The component that identifies missing skills by comparing user skills to market demands
- **Job Scraper Service**: The automated service that ingests job opportunities from external sources
- **Notification Service**: The email-based communication system for briefings and summaries
- **Scheduler**: The time-based task execution system for automated workflows
- **Tech Stack**: An array of technologies and skills required for a job
- **Match Score**: A numerical value (0-100) representing how well a job matches a user's profile
- **Morning Briefing**: A daily email containing personalized job recommendations
- **Evening Summary**: A daily email containing progress statistics
- **Backend API**: The FastAPI-based REST API server
- **Frontend Dashboard**: The Streamlit-based user interface
- **Database**: The SQLite/PostgreSQL persistent storage system

## Requirements

### Requirement 1: User Profile Management

**User Story:** As a job seeker, I want to manage my profile with skills, preferred locations, and experience level, so that the system can provide personalized recommendations.

#### Acceptance Criteria

1. WHEN a user registers, THE Career Co-Pilot System SHALL create a User Profile with empty skills, preferred_locations, and experience_level fields
2. WHEN a user requests their profile, THE Backend API SHALL return the user's current skills, preferred_locations, and experience_level
3. WHEN a user updates their profile with new skills, THE Career Co-Pilot System SHALL persist the updated skills array to the Database
4. WHEN a user updates their preferred locations, THE Career Co-Pilot System SHALL persist the updated preferred_locations array to the Database
5. WHERE a user specifies an experience level, THE Career Co-Pilot System SHALL validate the level is one of: "junior", "mid", or "senior"

### Requirement 2: Job Management

**User Story:** As a job seeker, I want to add, view, update, and delete job opportunities, so that I can maintain a centralized list of positions I'm interested in.

#### Acceptance Criteria

1. WHEN a user creates a Job Entity, THE Career Co-Pilot System SHALL require company and title fields
2. WHEN a user creates a Job Entity with tech_stack, THE Career Co-Pilot System SHALL store the tech_stack as a JSON array
3. WHEN a user requests their jobs, THE Backend API SHALL return all Job Entities associated with that user
4. WHEN a user updates a Job Entity, THE Career Co-Pilot System SHALL persist the changes and update the updated_at timestamp
5. WHEN a user deletes a Job Entity, THE Career Co-Pilot System SHALL remove the job and all associated Application Entities

### Requirement 3: Job Recommendation Engine

**User Story:** As a job seeker, I want to receive personalized job recommendations based on my skills and preferences, so that I can focus on the most relevant opportunities.

#### Acceptance Criteria

1. WHEN a user requests recommendations, THE Recommendation Engine SHALL calculate a Match Score for each unapplied Job Entity
2. WHEN calculating Match Score, THE Recommendation Engine SHALL weight tech stack alignment at 50 percent
3. WHEN calculating Match Score, THE Recommendation Engine SHALL weight location preferences at 30 percent
4. WHEN calculating Match Score, THE Recommendation Engine SHALL weight experience level match at 20 percent
5. WHEN returning recommendations, THE Backend API SHALL sort jobs by Match Score in descending order and return the top N results

### Requirement 4: Skill Gap Analysis

**User Story:** As a job seeker, I want to understand which skills I'm missing compared to market demands, so that I can prioritize my learning and development.

#### Acceptance Criteria

1. WHEN a user requests skill gap analysis, THE Skill Gap Analyzer SHALL aggregate all tech_stack requirements from the user's Job Entities
2. WHEN analyzing skills, THE Skill Gap Analyzer SHALL identify skills present in job requirements but absent from the User Profile
3. WHEN calculating coverage, THE Skill Gap Analyzer SHALL compute the percentage of skill mentions the user possesses
4. WHEN generating recommendations, THE Skill Gap Analyzer SHALL prioritize the top 5 most frequently mentioned missing skills
5. WHEN returning analysis, THE Backend API SHALL include user_skills, missing_skills, top_market_skills, skill_coverage_percentage, and learning recommendations

### Requirement 5: Automated Job Ingestion

**User Story:** As a job seeker, I want the system to automatically find and add relevant job opportunities, so that I don't have to manually search multiple job boards.

#### Acceptance Criteria

1. WHEN the Scheduler triggers the nightly ingestion task, THE Job Scraper Service SHALL query external job APIs using user skills and preferred locations
2. WHEN new jobs are retrieved, THE Job Scraper Service SHALL check for duplicates by comparing company and title combinations
3. WHEN a unique job is identified, THE Career Co-Pilot System SHALL create a new Job Entity with source set to "scraped"
4. WHEN ingestion completes, THE Career Co-Pilot System SHALL log the number of jobs added for each user
5. WHERE job scraping is disabled via configuration, THE Scheduler SHALL skip the ingestion task

### Requirement 6: Morning Job Briefing

**User Story:** As a job seeker, I want to receive a daily email with my top job recommendations, so that I can start my day with clear action items.

#### Acceptance Criteria

1. WHEN the Scheduler triggers the morning briefing task, THE Notification Service SHALL generate recommendations for each user
2. WHEN generating the briefing, THE Recommendation Engine SHALL select the top 5 jobs by Match Score
3. WHEN composing the email, THE Notification Service SHALL include job title, company, location, tech stack, Match Score, and link for each recommendation
4. WHEN sending the briefing, THE Notification Service SHALL use the configured SMTP settings
5. WHERE SMTP is not configured, THE Notification Service SHALL log the briefing content without sending

### Requirement 7: Evening Progress Summary

**User Story:** As a job seeker, I want to receive a daily summary of my application progress, so that I can track my job search momentum.

#### Acceptance Criteria

1. WHEN the Scheduler triggers the evening summary task, THE Notification Service SHALL calculate daily statistics for each user
2. WHEN calculating statistics, THE Career Co-Pilot System SHALL count applications submitted today, total active applications, and total jobs saved
3. WHEN composing the summary, THE Notification Service SHALL include applications_today, total_applications, and jobs_saved metrics
4. WHEN sending the summary, THE Notification Service SHALL use the configured SMTP settings
5. WHERE SMTP is not configured, THE Notification Service SHALL log the summary content without sending

### Requirement 8: Application Tracking

**User Story:** As a job seeker, I want to track my job applications and their status, so that I can manage my job search pipeline effectively.

#### Acceptance Criteria

1. WHEN a user creates an Application Entity, THE Career Co-Pilot System SHALL require a valid job_id
2. WHEN an application is created, THE Career Co-Pilot System SHALL set the initial status to "interested"
3. WHEN a user updates application status, THE Career Co-Pilot System SHALL accept one of: "interested", "applied", "interview", "offer", "rejected", "accepted", "declined"
4. WHEN a user marks a job as applied, THE Career Co-Pilot System SHALL update the Job Entity date_applied timestamp
5. WHEN a user requests applications, THE Backend API SHALL return all Application Entities with associated Job Entity details

### Requirement 9: Analytics Dashboard

**User Story:** As a job seeker, I want to view analytics about my job search, so that I can understand my progress and identify areas for improvement.

#### Acceptance Criteria

1. WHEN a user requests analytics summary, THE Backend API SHALL calculate total_jobs, total_applications, interviews, and offers
2. WHEN calculating interviews, THE Career Co-Pilot System SHALL count Application Entities with status "interview"
3. WHEN calculating offers, THE Career Co-Pilot System SHALL count Application Entities with status "offer" or "accepted"
4. WHEN displaying analytics, THE Frontend Dashboard SHALL show metrics in a clear, visual format
5. WHEN displaying recent activity, THE Frontend Dashboard SHALL show the 5 most recent Application Entities

### Requirement 10: Task Scheduling

**User Story:** As a system administrator, I want automated tasks to run on schedule, so that the system operates proactively without manual intervention.

#### Acceptance Criteria

1. WHEN the Backend API starts, THE Scheduler SHALL initialize with configured task schedules
2. WHEN the schedule reaches 4:00 AM, THE Scheduler SHALL trigger the ingest_jobs task
3. WHEN the schedule reaches 8:00 AM, THE Scheduler SHALL trigger the send_morning_briefing task
4. WHEN the schedule reaches 8:00 PM, THE Scheduler SHALL trigger the send_evening_summary task
5. WHERE ENABLE_SCHEDULER is set to false, THE Career Co-Pilot System SHALL not start the Scheduler

### Requirement 11: Authentication and Security

**User Story:** As a job seeker, I want my account and data to be secure, so that my job search information remains private.

#### Acceptance Criteria

1. WHEN a user registers, THE Career Co-Pilot System SHALL hash the password before storing in the Database
2. WHEN a user logs in with valid credentials, THE Backend API SHALL return a JWT access token
3. WHEN a user makes an authenticated request, THE Backend API SHALL validate the JWT token
4. WHEN a JWT token is invalid or expired, THE Backend API SHALL return a 401 Unauthorized response
5. WHEN accessing protected endpoints, THE Career Co-Pilot System SHALL ensure users can only access their own data

### Requirement 12: Frontend User Interface

**User Story:** As a job seeker, I want an intuitive web interface to interact with the system, so that I can easily manage my job search.

#### Acceptance Criteria

1. WHEN a user accesses the Frontend Dashboard, THE Career Co-Pilot System SHALL display a login form if not authenticated
2. WHEN a user logs in successfully, THE Frontend Dashboard SHALL display the main dashboard with navigation
3. WHEN viewing the dashboard, THE Frontend Dashboard SHALL display key metrics and recent activity
4. WHEN managing jobs, THE Frontend Dashboard SHALL provide forms to add, edit, and delete Job Entities
5. WHEN managing applications, THE Frontend Dashboard SHALL provide interfaces to create and update Application Entities

### Requirement 13: Configuration Management

**User Story:** As a system administrator, I want to configure the system through environment variables, so that I can adapt the system to different environments without code changes.

#### Acceptance Criteria

1. WHEN the Backend API starts, THE Career Co-Pilot System SHALL load configuration from environment variables
2. WHEN DATABASE_URL is provided, THE Career Co-Pilot System SHALL use the specified database connection
3. WHEN SMTP settings are provided, THE Notification Service SHALL use them for email delivery
4. WHEN JOB_API_KEY is provided, THE Job Scraper Service SHALL use it for external API calls
5. WHERE required configuration is missing, THE Career Co-Pilot System SHALL use sensible defaults or disable optional features

### Requirement 14: Data Persistence

**User Story:** As a job seeker, I want my data to be reliably stored and retrievable, so that I don't lose my job search progress.

#### Acceptance Criteria

1. WHEN the Backend API starts, THE Database SHALL initialize all required tables if they don't exist
2. WHEN a user creates or updates data, THE Career Co-Pilot System SHALL commit changes to the Database
3. WHEN a database operation fails, THE Career Co-Pilot System SHALL rollback the transaction and return an error
4. WHEN querying data, THE Backend API SHALL use indexed fields for efficient retrieval
5. WHEN relationships exist between entities, THE Database SHALL enforce foreign key constraints

### Requirement 15: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error handling and logging, so that I can troubleshoot issues and monitor system health.

#### Acceptance Criteria

1. WHEN an error occurs in the Backend API, THE Career Co-Pilot System SHALL return a structured error response with appropriate HTTP status code
2. WHEN an exception is raised, THE Career Co-Pilot System SHALL log the error with timestamp, context, and stack trace
3. WHEN scheduled tasks execute, THE Scheduler SHALL log start time, completion time, and results
4. WHEN external services fail, THE Career Co-Pilot System SHALL log the failure and continue operation where possible
5. WHEN the system starts, THE Career Co-Pilot System SHALL log initialization status and configuration summary
