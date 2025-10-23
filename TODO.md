## TODO List for Career Co-Pilot Implementation

This list details the actionable steps to implement the Career Co-Pilot features, adapted to the existing FastAPI/Next.js/Relational Database architecture.

---

### Phase 1: Core Application & Job Management

**Parallelism:** Tasks within this phase can be worked on in parallel where frontend and backend work is independent.

*   **Database Setup & ORM Integration:**
    *   [database] [backend] Verify database connection and ORM models are correctly configured for all necessary entities (Users, Jobs, Applications, etc.).
    *   [database] [backend] Ensure `alembic` migrations are up-to-date.
    *   [test] Write unit/integration tests for database models and ORM operations.

*   **Frontend Job Management UI:**
    *   [frontend] Complete the UI for displaying job entries within the Next.js frontend.
    *   [frontend] Complete the UI for adding new job entries within the Next.js frontend.
    *   [frontend] Complete the UI for updating job entries within the Next.js frontend.
    *   [frontend] Complete the UI for deleting job entries within the Next.js frontend.
    *   [frontend] Connect all job management UI actions to the existing FastAPI job management API endpoints (`/api/v1/jobs`).
    *   [test] Write frontend unit tests for job management components.
    *   [test] Write end-to-end tests for the job management workflow.

*   **User Authentication & Profile:**
    *   [frontend] Finalize frontend UI for user login.
    *   [frontend] Finalize frontend UI for user registration.
    *   [frontend] Finalize frontend UI for profile management.
    *   [frontend] Ensure secure communication and JWT token handling between frontend and backend.
    *   [test] Write frontend unit tests for authentication and profile components.
    *   [test] Write end-to-end tests for user authentication and profile management workflows.

---

### Phase 2: Automation & Intelligence

**Parallelism:** Job scraping implementation and recommendation engine integration can proceed in parallel with frontend integration.

*   **Job Ingestion/Scraping Implementation:**
    *   [backend] Implement the actual job scraping logic within the FastAPI backend (e.g., integrating with Adzuna API).
    *   [backend] Ensure duplicate job checking is performed before saving new jobs to the database.
    *   [test] Write unit/integration tests for the job scraping logic.

*   **Scheduler Configuration for Job Ingestion:**
    *   [backend] Configure the existing internal scheduler (`app.scheduler.py`) to periodically trigger the job ingestion task (e.g., daily at 4 AM).
    *   [test] Write integration tests to verify the scheduler triggers job ingestion correctly.

*   **Recommendation Engine Integration:**
    *   [backend] Verify the recommendation API endpoint (`/api/v1/recommendations`) is fully functional and returns personalized job recommendations.
    *   [frontend] Integrate the display of personalized job recommendations into the Next.js frontend (e.g., on the dashboard or a dedicated recommendations page).
    *   [test] Write unit/integration tests for the recommendation engine logic.
    *   [test] Write end-to-end tests for the recommendation display in the frontend.

---

### Phase 3: Proactive Engagement

**Parallelism:** Email notification implementation can proceed in parallel with other backend tasks.

*   **Email Notification Service Implementation:**
    *   [backend] Implement the email sending logic within the FastAPI backend, utilizing SendGrid or direct SMTP.
    *   [backend] Create email templates for morning briefings.
    *   [test] Write unit/integration tests for the email notification service.

*   **Scheduler Configuration for Notifications:**
    *   [backend] Configure the internal scheduler to trigger the `send_morning_briefing` task daily (e.g., 8 AM) to send personalized job recommendations via email.
    *   [test] Write integration tests to verify the scheduler triggers email notifications correctly.

*   **Evening Summary (Optional):**
    *   [backend] (Future) Implement logic for generating evening summaries.
    *   [backend] (Future) Implement sending evening summaries via the scheduler.

---

### Phase 4: Advanced Analytics & Insights

**Parallelism:** Skill-gap analysis and long-term analytics can be developed in parallel.

*   **Skill-Gap Analysis Integration:**
    *   [backend] Verify the skill-gap analysis API endpoint (`/api/v1/skill-gap`) is fully functional.
    *   [frontend] Integrate the display of skill-gap analysis and learning recommendations into the Next.js frontend.
    *   [test] Write unit/integration tests for the skill-gap analysis logic.
    *   [test] Write end-to-end tests for the skill-gap analysis display in the frontend.

*   **Long-Term Analytics Implementation:**
    *   [backend] Implement the backend logic for aggregating and serving various long-term analytics data (e.g., application success rates, conversion funnels, market trends).
    *   [frontend] Develop corresponding UI components in the Next.js frontend to display these insights.
    *   [test] Write unit/integration tests for the long-term analytics aggregation logic.
    *   [test] Write end-to-end tests for the long-term analytics display in the frontend.
