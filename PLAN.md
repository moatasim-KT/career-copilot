## Revised Plan for Career Co-Pilot Implementation

**Note on Architecture:**

The provided System Design Blueprint outlined a serverless architecture primarily using Google Cloud Functions and Firestore with a vanilla HTML/JS frontend. However, a review of the existing codebase reveals a different architecture is already in place:

*   **Backend:** A comprehensive FastAPI application (Python) handling API endpoints, services, and an internal scheduler.
*   **Database:** A relational database (PostgreSQL/SQLite) managed via SQLAlchemy, not Firestore.
*   **Frontend:** A Next.js application (Node.js/React) with established routing and UI components.

This revised plan adapts the goals of the blueprint to the existing FastAPI/Next.js/Relational Database architecture, focusing on completing the features within this established framework.

---

## Phase 1: Core Application & Job Management (Already Largely Implemented)

**Objective:** Leverage existing FastAPI and Next.js components to finalize core job management functionality.

### Tasks:

1.  **Database Setup & ORM Integration:**
    *   **Status:** Implemented (PostgreSQL/SQLite with SQLAlchemy).
    *   **Action:** Verify database connection and ORM models are correctly configured for all necessary entities (Users, Jobs, Applications, etc.). Ensure `alembic` migrations are up-to-date.

2.  **Frontend Job Management UI:**
    *   **Status:** Next.js frontend with `jobs` and `dashboard` routes exists.
    *   **Action:** Complete the UI for displaying, adding, updating, and deleting job entries within the Next.js frontend. Connect these UI actions to the existing FastAPI job management API endpoints (`/api/v1/jobs`).

3.  **User Authentication & Profile:**
    *   **Status:** FastAPI backend has `auth.router` and `profile.router`. Next.js frontend has `login` and `register` routes.
    *   **Action:** Finalize frontend UI for user login, registration, and profile management. Ensure secure communication and token handling between frontend and backend.

---

## Phase 2: Automation & Intelligence

**Objective:** Implement job ingestion and integrate the recommendation engine within the existing FastAPI backend and scheduler.

### Tasks:

1.  **Job Ingestion/Scraping Implementation:**
    *   **Status:** Backend has `enable_job_scraping` setting and `job_sources.router`.
    *   **Action:** Implement the actual job scraping logic within the FastAPI backend. This involves integrating with external job APIs (e.g., Adzuna) using the configured API keys. Ensure duplicate job checking before saving to the relational database.

2.  **Scheduler Configuration for Job Ingestion:**
    *   **Status:** Internal scheduler is integrated (`enable_scheduler: True`, `app.scheduler.py`).
    *   **Action:** Configure the existing internal scheduler to periodically trigger the job ingestion task (e.g., daily at 4 AM).

3.  **Recommendation Engine Integration:**
    *   **Status:** `RecommendationEngine` service is implemented in `backend/app/services/recommendation_engine.py`. `recommendations.router` exists.
    *   **Action:** Verify the recommendation API endpoint is fully functional. Integrate the display of personalized job recommendations into the Next.js frontend (e.g., on the dashboard or a dedicated recommendations page).

---

## Phase 3: Proactive Engagement

**Objective:** Implement email notifications for daily briefings using the existing backend and scheduler.

### Tasks:

1.  **Email Notification Service Implementation:**
    *   **Status:** `smtp_enabled` and `sendgrid_api_key` settings exist.
    *   **Action:** Implement the email sending logic within the FastAPI backend, utilizing SendGrid or direct SMTP. Create templates for morning briefings.

2.  **Scheduler Configuration for Notifications:**
    *   **Status:** Internal scheduler is present.
    *   **Action:** Configure the internal scheduler to trigger the `send_morning_briefing` task daily (e.g., 8 AM) to send personalized job recommendations via email.

3.  **Evening Summary (Optional):**
    *   **Status:** Planned for future expansion.
    *   **Action:** (Future) Implement logic for generating and sending evening summaries via the scheduler.

---

## Phase 4: Advanced Analytics & Insights

**Objective:** Integrate skill-gap analysis and long-term analytics into the existing backend and frontend.

### Tasks:

1.  **Skill-Gap Analysis Integration:**
    *   **Status:** `SkillGapAnalyzer` service is implemented in `backend/app/services/skill_gap_analyzer.py`. `skill_gap.router` exists.
    *   **Action:** Verify the skill-gap analysis API endpoint is functional. Integrate the display of skill-gap analysis and learning recommendations into the Next.js frontend.

2.  **Long-Term Analytics Implementation:**
    *   **Status:** `analytics.router` and `advanced_user_analytics.router` exist in the backend. `frontend/src/app/analytics` exists.
    *   **Action:** Implement the backend logic for aggregating and serving various long-term analytics data (e.g., application success rates, conversion funnels, market trends). Develop corresponding UI components in the Next.js frontend to display these insights.