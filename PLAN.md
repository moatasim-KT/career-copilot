# Plan for Backend-Frontend Integration

This plan outlines the steps to complete the remaining tasks for backend-frontend integration in the Career Copilot application, based on the research findings in `RESEARCH.md`.

## Phase 1: Dependency Consolidation (Critical)

1.  **Audit `get_current_user` imports**:
    *   Search the entire backend codebase for all occurrences of `get_current_user`.
    *   Identify files importing from `app/dependencies.py` and `app/core/dependencies.py`.
2.  **Standardize imports**:
    *   Modify all imports to exclusively use `app.dependencies.get_current_user`.
3.  **Remove duplicate implementation**:
    *   Delete or deprecate `app.core.dependencies.get_current_user`.
4.  **Add integration tests**:
    *   Create new tests or extend existing ones to verify that `get_current_user` consistently returns the same mock user across various endpoints when authentication is disabled.

## Phase 2: Endpoint Testing Framework Enhancements

1.  **Create test report generator**:
    *   Develop a module to generate HTML test reports.
    *   Ensure reports include pass/fail status, response times, and detailed error messages.
    *   Implement functionality to categorize results by endpoint type.
    *   Add options to export reports to JSON and CSV formats.

## Phase 3: Missing Backend Implementations

### 3.1 Data Export Functionality

1.  **Implement JSON export**:
    *   Develop a JSON formatter for jobs and applications.
    *   Integrate filtering and field selection capabilities.
    *   Add pagination support for large datasets.
2.  **Implement CSV export**:
    *   Develop a CSV formatter for jobs and applications.
    *   Handle nested data structures (e.g., `tech_stack`, `interview_feedback`).
    *   Ensure proper escaping and encoding.
3.  **Implement PDF export**:
    *   Integrate a PDF generation library (e.g., ReportLab).
    *   Design professional PDF templates for jobs and applications.
    *   Include charts and visualizations if applicable.
4.  **Implement full backup export**:
    *   Create an endpoint to export all user data (jobs, applications, profile, settings).
    *   Generate a compressed archive (e.g., ZIP) containing all data.

### 3.2 Data Import Functionality

1.  **Implement job import**:
    *   Develop logic to parse CSV files containing job data.
    *   Implement validation for required fields and data types.
    *   Handle parsing of `tech_stack` arrays.
    *   Implement bulk insertion of validated jobs using database transactions.
    *   Return an import summary with success/failure counts and error details.
2.  **Implement application import**:
    *   Develop logic to parse CSV files containing application data.
    *   Implement validation for status values and dates.
    *   Implement linking applications to existing jobs.
    *   Implement bulk insertion of validated applications using database transactions.
    *   Return an import summary with success/failure counts and error details.

### 3.3 Bulk Operations

1.  **Implement bulk create operations**:
    *   Create endpoints for bulk job creation.
    *   Create endpoints for bulk application creation.
    *   Ensure database transactions for atomicity.
    *   Return detailed results including created IDs.
2.  **Implement bulk update operations**:
    *   Create endpoints for bulk job updates.
    *   Create endpoints for bulk application updates.
    *   Implement validation for all updates before applying.
    *   Return updated IDs and error details.
3.  **Implement bulk delete operations**:
    *   Create endpoints for bulk job deletion.
    *   Create endpoints for bulk application deletion.
    *   Implement a soft delete option.
    *   Return deleted IDs and error details.

### 3.4 Enhanced Search and Filtering

1.  **Optimize search performance**:
    *   Add database indexes for frequently searched fields.
    *   Implement query result caching (e.g., using Redis).
    *   Implement pagination with cursor-based navigation.
    *   Ensure sub-second response times for search queries.

### 3.5 Notification Management System

1.  **Create notification data models**:
    *   Define SQLAlchemy models for `Notification` and `NotificationPreferences`.
    *   Create Pydantic schemas for request and response bodies.
    *   Generate a database migration for new notification tables.
2.  **Implement notification CRUD endpoints**:
    *   Create an endpoint to retrieve notifications with filtering options.
    *   Implement endpoints to mark notifications as read/unread.
    *   Implement an endpoint to mark all notifications as read.
    *   Create an endpoint to delete individual notifications.
    *   Implement an endpoint for bulk deletion of notifications.
3.  **Implement notification preferences**:
    *   Create an endpoint to retrieve user notification preferences.
    *   Create an endpoint to update user notification preferences (e.g., email, push, in-app settings, per-event-type configuration).
4.  **Create notification generation system**:
    *   Implement logic to generate notifications on job status changes.
    *   Implement logic for application updates.
    *   Implement logic for interview reminders.
    *   Implement logic for new job matches.

### 3.6 WebSocket Real-time Updates

1.  **Set up WebSocket infrastructure**:
    *   Configure WebSocket support within FastAPI.
    *   Develop a connection manager to handle active WebSocket connections.
    *   Implement user authentication for WebSocket connections.
2.  **Implement notification WebSocket endpoint**:
    *   Create a `/ws/notifications` WebSocket endpoint.
    *   Handle the full connection lifecycle (connect, disconnect, reconnect).
    *   Implement heartbeat/ping-pong mechanisms for connection health.
3.  **Integrate WebSocket with notification system**:
    *   Send real-time notifications through the WebSocket connection.
    *   Implement notification broadcasting to relevant users.
    *   Handle offline users by queuing notifications for later delivery.

### 3.7 Analytics Enhancements

1.  **Implement comprehensive analytics summary**:
    *   Calculate application counts by status.
    *   Compute interview and offer rates, and acceptance rate.
    *   Analyze daily/weekly/monthly application trends.
    *   Identify top skills in jobs and top companies applied to.
2.  **Implement trend analysis**:
    *   Calculate trend direction (up, down, neutral) and percentage changes.
    *   Support custom time ranges for trend analysis.
3.  **Implement skill gap analysis**:
    *   Compare user skills with market demand.
    *   Identify missing skills and calculate skill coverage percentage.
    *   Generate skill recommendations.
4.  **Optimize analytics performance**:
    *   Implement result caching with a 5-minute TTL.
    *   Add database indexes for analytics queries.
    *   Utilize aggregation queries for efficiency.
    *   Ensure sub-3-second response times for analytics queries.

## Phase 4: Comprehensive Error Handling

1.  **Create error response models**:
    *   Define a standardized `ErrorResponse` Pydantic model including `request_id`, `timestamp`, and `field_errors`.
2.  **Add global exception handlers**:
    *   Implement handlers for validation errors (400, 422).
    *   Implement handlers for not found errors (404).
    *   Implement handlers for database errors (500).
    *   Implement a catch-all handler for unexpected exceptions.
3.  **Enhance error logging**:
    *   Ensure all errors are logged with full context, including `request_id`, user, and endpoint information.
    *   Implement structured logging.
4.  **Improve error messages**:
    *   Provide clear, actionable error messages to the frontend.
    *   Include field names in validation errors.
    *   Avoid exposing sensitive information in production.
    *   Add error codes for programmatic handling.

## Phase 5: Performance Optimizations

1.  **Add database indexes**:
    *   Create indexes on frequently queried fields.
    *   Add composite indexes for common filter combinations.
    *   Index foreign keys for join performance.
2.  **Implement caching layer**:
    *   Set up Redis for distributed caching.
    *   Cache analytics results (5-minute TTL), user profiles (1-hour TTL), and job listings (15-minute TTL).
    *   Implement cache invalidation on updates.
3.  **Optimize database queries**:
    *   Use `select_related` for eager loading to reduce N+1 queries.
    *   Implement query result pagination.
    *   Add query performance logging.
4.  **Implement connection pooling**:
    *   Configure the database connection pool with appropriate size limits.
    *   Monitor connection pool usage.

## Phase 6: Comprehensive Testing

1.  **Write unit tests for new endpoints**:
    *   Cover all new export, import, bulk operation, search, and notification CRUD functionalities.
2.  **Write integration tests**:
    *   Test complete export-import workflows.
    *   Test WebSocket connections and real-time messaging.
    *   Test notification generation and delivery.
    *   Test analytics calculation accuracy.
3.  **Write end-to-end tests**:
    *   Cover complete user workflows involving new features (e.g., job creation -> application -> export; import -> search -> filter -> apply; notification flow).
4.  **Implement performance tests**:
    *   Conduct tests for 100 concurrent requests.
    *   Test large dataset queries (10,000+ records).
    *   Test bulk operations with 1,000+ records.
    *   Test WebSocket with 100+ connections.
    *   Verify all response time requirements are met.

## Phase 7: Documentation and Deployment

1.  **Update API documentation**:
    *   Document all new endpoints with examples.
    *   Update the OpenAPI schema.
    *   Add usage examples for export/import.
    *   Document the WebSocket protocol.
2.  **Create deployment guide**:
    *   Document environment variables.
    *   Add database migration instructions.
    *   Document Redis setup for caching.
    *   Add monitoring setup instructions.
3.  **Update frontend documentation**:
    *   Document new API client methods.
    *   Add examples for new features.
    *   Update the integration guide.