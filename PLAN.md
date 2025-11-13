# Plan: Career Copilot Integrated Roadmap & Consolidation Implementation

This plan outlines the implementation strategy for the Career Copilot project, integrating critical codebase consolidation with new feature development based on the `RESEARCH.md`.

## IMPORTANT: Foundational Work First!
The following consolidation and build optimization phases (Phase 0 and 0.5) are foundational and must be completed before or in parallel with subsequent feature development phases. This approach ensures a stable, efficient, and maintainable platform for future work.

## Phase 0: Critical Consolidation (Weeks 1-2)
**Objective:** Reduce codebase complexity, improve maintainability, and establish single sources of truth.

### 0.1. Service Layer Consolidation
*   **Create service mapping document:** Document dependencies and responsibilities of existing services to guide consolidation.
*   **Consolidate analytics services:** Re-architect analytics services, aiming to keep `analytics_service.py` as the primary and use a facade pattern, removing or refactoring redundant implementations.
*   **Consolidate job management services:** Create a unified `JobManagementSystem` class or similar pattern to centralize job-related logic (scraping, ingestion, recommendations).
*   **Merge LLM services with plugin architecture:** Implement a single provider-agnostic LLM service with a plugin architecture to integrate different LLM providers (e.g., Groq, OpenAI, Ollama).
*   **Unify notification services:** Re-architect notification services into a single, unified service with clear channel abstraction (email, WebSocket, scheduled).
*   **Remove duplicate storage implementations:** Identify and remove redundant storage logic, standardizing on a single approach (e.g., cloud storage integration).
*   **Update import statements:** Refactor and update all import statements across the codebase to reflect the consolidated service structure.

### 0.2. API Route Cleanup
*   **Audit all API endpoints for duplication:** Identify overlapping or redundant API routes across `analytics.py`, `analytics_extended.py`, `advanced_user_analytics.py`, `notifications.py`, `notifications_new.py`, `notifications_v2.py`.
*   **Merge analytics routes:** Consolidate all analytics-related endpoints into a single, unified `analytics.py` file with all functionality.
*   **Consolidate notification routes:** Unify notification endpoints, ensuring proper versioning and removing redundant `notifications_new.py`/`notifications_v2.py` files.
*   **Remove deprecated route versions:** Delete any API route files or endpoints that have been identified as deprecated or superseded.
*   **Update OpenAPI documentation:** Ensure the OpenAPI schema correctly reflects the consolidated and updated API routes.

## Phase 0.5: Build Optimization (Week 3)
**Objective:** Significantly reduce frontend build times and bundle size, improving developer productivity and user experience.

### 0.5.1 Bundle Size Reduction
*   **Disable bundle analyzer in CI builds:** Configure `@next/bundle-analyzer` to run only when explicitly needed, not automatically in production CI builds.
*   **Optimize Sentry source map uploads:** Review Sentry configuration, particularly `widenClientFileUpload`, to reduce the size and frequency of source map uploads.
*   **Implement code splitting for large components:** Identify large frontend components and implement lazy loading/code splitting to reduce initial bundle size.
*   **Remove unused dependencies:** Audit `package.json` for unused npm packages and remove them.
*   **Configure proper tree-shaking:** Ensure Webpack/Next.js is effectively tree-shaking unused code branches and modules.

### 0.5.2 Webpack Configuration Cleanup
*   **Review and optimize webpack plugins:** Identify and remove redundant or inefficient Webpack plugins.
*   **Implement conditional bundle analysis:** Configure Webpack to allow for on-demand bundle analysis rather than always a full run.
*   **Configure proper caching strategies:** Optimize Webpack caching for faster incremental builds.
*   **Optimize CSS processing:** Review and optimize PostCSS/TailwindCSS configurations for efficient CSS generation.

## Phase 1: Critical Priority Tasks (Immediate - Next 1-2 weeks - *After Consolidation*)
**Objective:** Address high-priority security vulnerabilities and implement core backend functionalities.

### 1.1. Security & Credentials
*   **Replace hardcoded placeholder tokens/passwords:** Identify and remove all hardcoded tokens/passwords. Replace them with environment variables or a secure secrets management system.
*   **Update `.env.example`:** Ensure this file accurately reflects all necessary environment variables with clear descriptions for developers.
*   **Ensure secure loading of credentials:** Verify that the application correctly loads and uses credentials from environment variables securely.
*   **Update security scanning configurations:** Adjust security scanning tools (e.g., Bandit) to prevent flagging valid environment variable usage and ensure no real secrets are committed.

### 1.2. Core Backend Functionality
*   **Implement Data Export (JSON, CSV):** Develop the backend logic and API endpoints for exporting job and application data in JSON and CSV formats. This will likely involve using the *consolidated* services.
*   **Implement Data Import (CSV):** Develop the backend logic and API endpoints for importing job and application data from CSV files, including validation. This will likely involve using the *consolidated* services.
*   **Implement Bulk Operations (create, update, delete):** Develop backend logic and API endpoints for bulk creation, updating, and deletion of jobs and applications. This will likely involve using the *consolidated* services.
*   **Fix critical API placeholders:** Replace placeholder logic/data in specific API endpoints identified in `RESEARCH.md` (e.g., `advanced_user_analytics.py`, `database_performance.py`) with actual functionality.
*   **Implement admin permission check in `job_ingestion.py`:** Add the necessary role-based access control (RBAC) checks.
*   **Refactor `FeedbackService` to use async queries:** Convert synchronous database operations in this service to asynchronous.
*   **Define and add missing Pydantic schemas in `resume.py`:** Ensure API requests and responses for resume-related endpoints are properly typed and validated.

## Phase 2: High Priority Tasks (Next 2-4 weeks - *After Consolidation*)
**Objective:** Connect the frontend to the new backend features and implement real-time notifications.

### 2.1. Frontend-Backend Integration
*   **Update API client:** Modify `frontend/src/lib/api/api.ts` to include methods for interacting with the newly implemented (and consolidated) backend API endpoints for export, import, and bulk operations.
*   **Replace placeholder logic in frontend hooks:** Update specific frontend hooks (e.g., `useAddJob.ts`, `useDeleteApplication.ts`) to use the actual API client calls instead of placeholder logic.
*   **Implement global logout/re-authentication flow:** Develop the frontend logic to handle token expiration, invalid authentication, and prompt the user for re-authentication or logout.

### 2.2. Notification System
*   **Backend Implementation:**
    *   **Define SQLAlchemy models:** Create `Notification` and `NotificationPreferences` models in `backend/app/models/`.
    *   **Create CRUD service and REST API endpoints:** Implement `notification_service.py` with business logic and corresponding API endpoints in `backend/app/api/v1/notifications.py`.
    *   **Implement WebSocket manager and endpoint:** Set up a WebSocket server in `backend/app/websocket/` to handle real-time notification delivery.
*   **Frontend Implementation:**
    *   **Implement WebSocket client:** Develop a client in `frontend/src/lib/` to connect to the backend WebSocket endpoint.
    *   **Update `Layout.tsx` for real-time notifications:** Integrate the WebSocket client to display incoming notifications and update notification badges in the UI.

## Phase 3: Medium Priority Tasks (Next 1-2 months)
**Objective:** Enhance analytics, improve application performance, and strengthen error handling/monitoring.

### 3.1. Analytics and Performance
*   **Implement detailed analytics calculations:** Develop `backend/app/services/analytics_service.py` to calculate trends, skill gaps, application rates, etc.
*   **Add database indexes:** Identify performance-critical database queries and create appropriate indexes on relevant columns.
*   **Integrate Redis caching:** Configure and implement Redis for caching frequently accessed data, suchs as analytics results and user profiles.

### 3.2. Error Handling & Monitoring
*   **Implement global exception handlers:** Create centralized exception handlers in `backend/app/core/` to standardize error logging and responses across the application.
*   **Integrate a third-party monitoring service:** Set up integration with a service like Sentry for both backend (`logger.ts`) and frontend to capture, report, and monitor errors.

## Phase 4: Low Priority & Ongoing Tasks (Future Releases)
**Objective:** Implement advanced user features, ensure code quality through comprehensive testing, and maintain up-to-date documentation.

### 4.1. Advanced Features & Testing
*   **Integrate `LazyRichTextEditor` component:** Implement the full functionality of a rich text editor.
*   **Implement job benchmarking feature:** Develop the logic and corresponding UI for comparing job offers or market rates.
*   **Write unit and integration tests:** Create comprehensive test suites for all newly implemented features across both frontend and backend.
*   **Fix MSW setup in `Auth.test.tsx`:** Resolve issues with Mock Service Worker setup in frontend tests to ensure reliable authentication testing.

### 4.2. Documentation
*   **Update API documentation:** Ensure all new and consolidated API endpoints are thoroughly documented with examples.
*   **Update user and developer guides:** Reflect new features, consolidated architectures, and best practices.
*   **Document new environment variables and deployment steps:** Provide clear instructions for setting up and deploying the application in various environments.
