# Project Roadmap: Gaps, Unimplemented Code, and Placeholders

This document outlines the identified gaps, unimplemented code, and placeholders within the Career Copilot project, synthesized from code comments, `TODO.md`, and other documentation.

## 📚 Knowledge Base Integration

This roadmap has been integrated into the Foam knowledge base for better organization and navigation:

- **Main Roadmap**: `docs/roadmap/index.md`
- **Backend Gaps**: `docs/roadmap/backend-gaps.md`
- **Frontend Gaps**: `docs/roadmap/frontend-gaps.md`
- **Code TODOs**: `docs/roadmap/code-todos.md`
- **Documentation**: `docs/roadmap/documentation-todos.md`
- **Prioritization**: `docs/roadmap/prioritization.md`

Use the knowledge base for detailed implementation plans and cross-references.

## I. Major Unimplemented Features/Gaps (from `TODO.md` and code comments)

These are high-level features and functionalities that are planned but not yet fully implemented.

*   **Data Export Functionality (Backend):**
    *   JSON, CSV, and PDF export for jobs and applications.
    *   Full backup export of all user data.
*   **Data Import Functionality (Backend):**
    *   Job and application import from CSV files.
*   **Bulk Operations (Backend):**
    *   Bulk create, update, and delete for jobs and applications.
*   **Enhanced Search and Filtering (Backend):**
    *   Optimization of search performance (indexing, caching, pagination).
*   **Notification Management System (Backend & Frontend):**
    *   Notification data models, CRUD endpoints, and preference management.
    *   Notification generation system for various events.
    *   Real-time updates for notifications via WebSockets.
*   **Analytics Enhancements (Backend):**
    *   Comprehensive analytics summary (application counts, rates, trends, top skills/companies).
    *   Trend analysis with custom time ranges.
    *   Skill gap analysis (comparing user skills with market demand).
    *   Optimization of analytics performance (caching, indexing, aggregation).
*   **Comprehensive Error Handling (Backend):**
    *   Standardized error response models.
    *   Global exception handlers.
    *   Enhanced error logging and improved error messages.
*   **Performance Optimizations (Backend):**
    *   Database indexing.
    *   Caching layer with Redis.
    *   Optimized database queries (eager loading, pagination, logging).
    *   Connection pooling.
*   **Comprehensive Testing:**
    *   Unit, integration, and end-to-end tests for new features.
    *   Performance tests.
*   **Documentation and Deployment:**
    *   Updating API and frontend documentation.
    *   Creating deployment guides.

## II. Specific Code-level TODOs and Placeholders

These are more granular items found directly in the codebase, indicating areas for future work or temporary implementations.

### Backend

*   **Security:** ✅ **COMPLETED**
    *   Real API keys found in `backend/.env` have been moved to secure `secrets/api_keys/` directory
    *   Environment file now contains placeholder values only
    *   Security audit passes with no exposed secrets
*   **Database/Models:**
    *   `# TODO: Convert to async queries` in `scripts/database/convert_to_async.py`.
    *   `# TODO: Create document model` and `# TODO: Create goal model` in `backend/app/services/profile_service.py` and `backend/app/services/backup_service.py`.
    *   `"""Contract analysis database model (placeholder for compatibility)."""` in `backend/app/models/database_models.py`.
*   **Services (Placeholder Implementations):**
    *   `backend/app/services/chroma_health_monitor.py`: Slack health alerts.
    *   `backend/app/services/analytics_service.py`: Risk trend analysis, contract comparison, compliance checking.
    *   `backend/app/services/llm_config_manager.py`: Evaluate accuracy (placeholder for more sophisticated checks).
    *   `backend/app/services/slack_service.py`: Placeholder for Slack message templates.
    *   `backend/app/services/integration_service.py`: Fallback with placeholder doc id.
    *   `backend/app/services/template_service.py`: Placeholder scores (ATS compatibility, readability).
    *   `backend/app/services/job_service.py`: Placeholder user object.
    *   `backend/app/services/scheduled_notification_service.py`: Placeholder for interview tracking, jobs viewed, profiles updated, responses.
    *   `backend/app/services/storage/cloud.py`: Cloud storage implementation.
    *   `backend/app/services/job_source_manager.py`: Build summary and simple trends.
    *   `backend/app/services/task_queue_manager.py`: Returns a placeholder.
    *   `backend/app/services/intelligent_cache_service.py`: Returns a placeholder or raises an error.
    *   `backend/app/services/analytics_processing_service.py`: Returns placeholder.
    *   `backend/app/services/recommendation_engine.py`: Placeholder scoring.
    *   `backend/app/services/briefing_service.py`: Integrate with recommendations.
    *   `backend/app/services/sharding_migration_strategy_service.py`: Returns a placeholder structure.
    *   `backend/app/services/task_handlers.py`: Registry placeholder.
    *   `backend/app/services/scraping/themuse_scraper.py`: Treat placeholder/comment values as not set.
    *   `backend/app/services/job_scraping_service.py`: Rate limiting and quota management.
*   **API Endpoints (Placeholder Implementations/TODOs):**
    *   `backend/app/api/v1/enhanced_recommendations.py`: ✅ **COMPLETED** - Implemented proper filtering logic for experience levels, company sizes, and industries.
    *   `backend/app/api/v1/skill_gap_analysis.py`: ✅ **COMPLETED** - Replaced placeholder with proper data freshness timestamp.
    *   `backend/app/api/v1/help_articles.py`: ✅ **COMPLETED** - Implemented relevance scoring based on keyword matching in title, excerpt, and content.
    *   `backend/app/api/v1/advanced_user_analytics.py`: Returns placeholder structure (appropriate fallback when service unavailable).
    *   `backend/app/api/v1/database_performance.py`: Returns placeholder data (appropriate fallback when service unavailable).
    *   `backend/app/api/v1/job_ingestion.py`: `# TODO: enforce admin permission check once RBAC is in place`.
    *   `backend/app/api/v1/feedback.py`: `# TODO: Fix FeedbackService to use async queries`.
    *   `backend/app/api/v1/resume.py`: `# TODO: Fix missing schemas` (ProfileService commented out but not used).
*   **Core/Utils:**
    *   `backend/app/utils/docstring_enhancer.py`: Basic placeholder using function name.
    *   `backend/app/core/alerting.py`: Evaluate all alert rules.
    *   `backend/app/core/optimized_database.py`: Simple normalization - replace parameters with placeholders.
    *   `backend/app/core/monitoring.py`: `log_entries_per_second=0`, `prometheus_metrics_placeholder`.

### Frontend

*   **API Integration:**
    *   `frontend/src/lib/api/api.ts`: `# TODO: Potentially trigger a global logout or re-authentication flow`.
    *   `frontend/src/hooks/useDeleteApplication.ts`, `useAddJob.ts`, `useDeleteJob.ts`, `useUpdateJob.ts`, `useAddApplication.ts`: `// Placeholder for API client`.
    *   `frontend/src/lib/export/dataBackup.ts`: `// Placeholder - would call API` for various backup/restore operations.
*   **Monitoring/Logging:**
    *   `frontend/src/lib/logger.ts`: `// TODO: Integrate with monitoring service`.
    *   `frontend/src/hooks/useGracefulDegradation.ts`: `// TODO: Send to Sentry or similar`.
*   **Real-time Updates:**
    *   `frontend/src/components/layout/Layout.tsx`: Numerous `// TODO:` comments for real-time updates (jobs list, application status, dashboard stats, notification badges, sound playback).
*   **Offline Sync:**
    *   `frontend/src/lib/utils/offlineSync.ts`: `// Placeholder for offline data synchronization strategy`.
*   **UI Components (Functional Placeholders):**
    *   `frontend/src/components/lazy/LazyRichTextEditor.tsx`: Placeholder for future rich text editor integration.
    *   `frontend/src/components/pages/ApplicationKanban.tsx`: `// TODO: Open add application modal`.
    *   `frontend/src/components/jobs/benchmark.ts`: Placeholder for job benchmarking.
*   **Testing:**
    *   `frontend/src/components/__tests__/Auth.test.tsx`: `// TODO: Fix MSW setup or migrate to a different mocking approach`.
*   **Image Optimization:**
    *   Extensive use of `placeholder="blur"` and `placeholder.svg` for loading states (intentional UX). However, `frontend/TASK_10.3_SUMMARY.md` mentions `// TODO: Add automatic blur placeholder generation`, indicating an area for improvement.
*   **Settings:**
    *   `frontend/TASK_21_SETTINGS_SYSTEM_SUMMARY.md`: "Two-factor authentication (coming soon placeholder)", "Custom shortcuts placeholder for future feature", "API integration ready (commented placeholders)".

## III. Documentation TODOs

*   `TODO.md` is actively used for task tracking and references many of the items above.
*   `config/templates/env.template`: Requires replacing placeholder values with actual credentials.

## Prioritization

The most critical areas for immediate focus are:

1.  **Security:** Replacing hardcoded placeholder tokens and passwords.
2.  **Core Backend Functionality:** Implementing data export/import, bulk operations, and the notification system.
3.  **API Integration (Frontend):** Connecting frontend hooks to the backend API.
4.  **Real-time Updates:** Implementing WebSocket functionality for a dynamic user experience.
5.  **Analytics Enhancements:** Providing meaningful insights to users.

This roadmap will serve as a guide for future development, ensuring that all identified gaps and unimplemented features are systematically addressed.
