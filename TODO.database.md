
# Career Copilot Production Database Schema & Integrity Rules

## Overview
This document summarizes the final, production-ready database schema for Career Copilot as of November 2025. It covers all tables, relationships, constraints, and integrity rules enforced at the database level.

---

## Core Tables

### users
- **id** (PK, serial)
- username (unique, not null)
- email (unique, not null)
- hashed_password (nullable)
- skills (JSON)
- preferred_locations (JSON)
- experience_level (string)
- daily_application_goal (int, default=10)
- is_admin (bool, default=False)
- prefer_remote_jobs (bool, default=False)
- oauth_provider, oauth_id, profile_picture_url (nullable)
- created_at, updated_at (timestamps)

**Constraints:**
- Unique: username, email
- Relationships: jobs, applications, resume_uploads, content_generations, job_recommendation_feedback, feedback, resource_bookmarks, resource_feedback, resource_views, learning_path_enrollments

---

### jobs
- **id** (PK, serial)
- user_id (FK users.id, not null)
- company, title (not null)
- location, description, requirements, salary_range, salary_min, salary_max, job_type, remote_option, tech_stack (JSON), responsibilities, documents_required (JSON), application_url, source_url, source, status, notes, date_applied, created_at, updated_at, currency
- job_fingerprint (string, index)

**Constraints:**
- FK: user_id → users.id
- Indexes: company, title, status, user_id, job_fingerprint
- Relationships: applications, content_generations, recommendation_feedback

---

### applications
- **id** (PK, serial)
- user_id (FK users.id, not null)
- job_id (FK jobs.id, not null)
- status (string, default="interested")
- applied_date, response_date, interview_date, offer_date, notes, interview_feedback (JSON), follow_up_date, created_at, updated_at

**Constraints:**
- FK: user_id → users.id, job_id → jobs.id
- Indexes: user_id, job_id, status

---

### analytics
- **id** (PK, serial)
- user_id (nullable, FK users.id)
- type (string, not null)
- data (JSON, not null)
- generated_at (timestamp, not null)

---

### feedback, feedback_votes, job_recommendation_feedback
- feedback: id (PK), user_id (FK), type (enum), priority (enum), status (enum), title, description, ...
- feedback_votes: id (PK), feedback_id (FK), user_id (FK), vote (int)
- job_recommendation_feedback: id (PK), user_id (FK), job_id (FK), is_helpful (bool), ...

---

### interview_sessions, interview_questions
- interview_sessions: id (PK), user_id (FK), job_id (FK), interview_type (enum), status (enum), ...
- interview_questions: id (PK), session_id (FK), question_text, ...

---

### resume_uploads
- id (PK), user_id (FK), filename, file_path, file_size, file_type, parsing_status, parsed_data (JSON), ...

---

### user_job_preferences
- id (PK), user_id (FK), preferred_sources (JSON), disabled_sources (JSON), ...

---

### content_generations, content_versions
- content_generations: id (PK), user_id (FK), job_id (FK), content_type, generated_content, ...
- content_versions: id (PK), content_generation_id (FK), version_number, content, ...

---

### career_resources, resource_bookmarks, resource_feedback, resource_views, learning_paths, learning_path_enrollments
- career_resources: id (PK), title, description, type, provider, url, skills (ARRAY), ...
- resource_bookmarks: id (PK), user_id (FK), resource_id (FK), ...
- resource_feedback: id (PK), user_id (FK), resource_id (FK), ...
- resource_views: id (PK), user_id (FK), resource_id (FK), ...
- learning_paths: id (PK), name, description, ...
- learning_path_enrollments: id (PK), user_id (FK), learning_path_id (FK), ...

---

## Integrity Rules
- All FKs use `ON DELETE CASCADE` or `SET NULL` as appropriate for orphan cleanup.
- All unique and composite indexes are enforced as per model definitions.
- Enum types are used for status, type, and priority fields for data consistency.
- All timestamps use UTC and are set by the database or application.
- JSON/ARRAY fields are used for flexible, semi-structured data (skills, preferences, etc.).
- All relationships are bi-directional and use SQLAlchemy `relationship` for ORM integrity.

---

## Notes
- See Alembic migration scripts for full DDL details.
- All schema changes are tracked and versioned via Alembic.
- This schema is production-ready and matches the current SQLAlchemy models and migrations as of November 2025.
