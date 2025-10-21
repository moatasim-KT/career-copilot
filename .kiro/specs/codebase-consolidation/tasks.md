# Implementation Plan: Codebase Consolidation

## Overview

This implementation plan breaks down the codebase consolidation into discrete, manageable tasks. Each task builds on previous work to systematically transform the codebase into a clean, maintainable job tracking system.

---

## Phase 1: Cleanup and Project Identity

- [ ] 1. Establish clear project identity and remove contract analysis code
  - Remove all contract analysis related files from backend/app/api/v1/
  - Remove contract analysis components from frontend
  - Update README.md to focus exclusively on job tracking
  - Update docker-compose.yml to reflect Career Copilot identity
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Remove redundant main application files
  - Delete backend/app/main_simple.py
  - Delete backend/app/main_streamlined.py
  - Delete backend/app/main_job_tracker.py
  - Keep only backend/app/main.py as single entry point
  - _Requirements: 2.1, 4.1_

- [ ] 3. Clean up configuration system
  - Remove complex YAML configuration files from config/
  - Keep only config/base.yaml for reference
  - Simplify config/config_loader.py or remove if not needed
  - Create simple backend/app/core/config.py using pydantic-settings
  - _Requirements: 2.4, 7.1, 7.3, 7.4_

- [ ] 4. Remove unused middleware and over-engineered components
  - Audit all middleware in backend/app/middleware/
  - Keep only: CORS, Authentication, Logging, Error Handler
  - Remove: comprehensive_security, resource_middleware, rate_limiting, CSP, enhanced_*, firebase_auth, input_validation, request_validation
  - Update main.py to use only essential middleware
  - _Requirements: 2.2, 4.3_

- [ ] 5. Clean up frontend application
  - Remove all contract analysis UI components from frontend/components/
  - Remove production optimization files if over-engineered
  - Keep only: job tracking components, analytics, API client
  - Simplify frontend/app.py to focus on job tracking
  - _Requirements: 6.3, 6.4_

---

## Phase 2: Fix Dependencies and Imports

- [ ] 6. Create minimal requirements.txt for backend
  - Start with essential packages: fastapi, uvicorn, sqlalchemy, pydantic, python-jose, passlib
  - Add only necessary dependencies
  - Remove all unused AI/ML packages if not needed for job tracking
  - Test that all imports work
  - _Requirements: 3.3, 4.3_

- [ ] 7. Fix broken imports in backend/app/main.py
  - Remove imports for deleted contract analysis routers
  - Remove imports for deleted middleware
  - Remove imports for non-existent services
  - Keep only imports for: health, jobs, applications, users, analytics, auth
  - Test application startup
  - _Requirements: 3.1, 3.2_

- [ ] 8. Create minimal requirements.txt for frontend
  - Include: streamlit, requests, pandas, plotly
  - Remove unnecessary dependencies
  - Test frontend startup
  - _Requirements: 3.3_

- [ ] 9. Fix frontend imports and API client
  - Update frontend/app.py imports to reference existing components
  - Simplify API client in frontend/utils/api_client.py
  - Remove references to non-existent production features
  - Test frontend-backend communication
  - _Requirements: 3.1, 3.2, 6.4_

---

## Phase 3: Implement Core Backend Structure

- [ ] 10. Set up simplified database configuration
  - Create backend/app/core/database.py with SQLAlchemy setup
  - Configure SQLite database connection
  - Add database initialization function
  - Create Alembic migration setup
  - _Requirements: 2.3, 10.4_

- [ ] 11. Create database models for job tracking
  - [ ] 11.1 Create backend/app/models/user.py with User model
    - Define User table with id, username, email, password_hash, timestamps
    - Add relationships to jobs and applications
    - _Requirements: 2.3_
  
  - [ ] 11.2 Create backend/app/models/job.py with Job model
    - Define Job table with all fields from design
    - Add relationship to user and applications
    - _Requirements: 2.3, 8.1_
  
  - [ ] 11.3 Create backend/app/models/application.py with Application model
    - Define Application table with status tracking
    - Add relationships to user and job
    - _Requirements: 2.3, 8.2_

- [ ] 12. Create Pydantic schemas for validation
  - [ ] 12.1 Create backend/app/schemas/user.py
    - UserCreate, UserLogin, UserResponse schemas
    - _Requirements: 5.2_
  
  - [ ] 12.2 Create backend/app/schemas/job.py
    - JobCreate, JobUpdate, JobResponse schemas
    - _Requirements: 5.2, 8.1_
  
  - [ ] 12.3 Create backend/app/schemas/application.py
    - ApplicationCreate, ApplicationUpdate, ApplicationResponse schemas
    - _Requirements: 5.2, 8.2_

- [ ] 13. Implement authentication and security
  - Create backend/app/core/security.py with JWT functions
  - Implement password hashing with bcrypt
  - Create authentication dependency for protected routes
  - Add simple authentication middleware
  - _Requirements: 2.5, 5.5_

- [ ] 14. Create service layer for business logic
  - [ ] 14.1 Create backend/app/services/job_service.py
    - Implement CRUD operations for jobs
    - Add search and filter functionality
    - _Requirements: 2.3, 8.1, 8.4_
  
  - [ ] 14.2 Create backend/app/services/application_service.py
    - Implement CRUD operations for applications
    - Add status update functionality
    - _Requirements: 2.3, 8.2_
  
  - [ ] 14.3 Create backend/app/services/analytics_service.py
    - Implement statistics calculation
    - Add timeline and status breakdown
    - _Requirements: 2.3, 8.3_

---

## Phase 4: Implement Core API Endpoints

- [ ] 15. Create health and monitoring endpoints
  - Create backend/app/api/v1/health.py
  - Implement GET /api/v1/health endpoint
  - Add database connectivity check
  - _Requirements: 5.4, 10.3_

- [ ] 16. Create authentication endpoints
  - Create backend/app/api/v1/auth.py
  - Implement POST /api/v1/auth/register endpoint
  - Implement POST /api/v1/auth/login endpoint
  - Add proper error handling
  - _Requirements: 5.3, 5.5_

- [ ] 17. Create job management endpoints
  - [ ] 17.1 Create backend/app/api/v1/jobs.py
    - Implement GET /api/v1/jobs (list with pagination)
    - Implement POST /api/v1/jobs (create)
    - Implement GET /api/v1/jobs/{id} (get details)
    - Implement PUT /api/v1/jobs/{id} (update)
    - Implement DELETE /api/v1/jobs/{id} (delete)
    - Add authentication requirement
    - _Requirements: 5.1, 5.2, 5.3, 8.1, 8.4_

- [ ] 18. Create application management endpoints
  - [ ] 18.1 Create backend/app/api/v1/applications.py
    - Implement GET /api/v1/applications (list with filters)
    - Implement POST /api/v1/applications (create)
    - Implement GET /api/v1/applications/{id} (get details)
    - Implement PUT /api/v1/applications/{id} (update status)
    - Implement DELETE /api/v1/applications/{id} (delete)
    - Add authentication requirement
    - _Requirements: 5.1, 5.2, 5.3, 8.2, 8.4_

- [ ] 19. Create analytics endpoints
  - [ ] 19.1 Create backend/app/api/v1/analytics.py
    - Implement GET /api/v1/analytics/summary (statistics)
    - Implement GET /api/v1/analytics/timeline (application timeline)
    - Implement GET /api/v1/analytics/status (status breakdown)
    - Add authentication requirement
    - _Requirements: 5.1, 5.2, 8.3_

- [ ] 20. Update main.py with clean router registration
  - Remove all contract analysis router imports
  - Register only: health, auth, jobs, applications, analytics
  - Configure minimal middleware stack
  - Add startup and shutdown events
  - Test all endpoints
  - _Requirements: 2.1, 2.2, 5.1, 10.1_

---

## Phase 5: Implement Frontend Components

- [ ] 21. Create simplified frontend API client
  - Update frontend/utils/api_client.py
  - Implement methods for all backend endpoints
  - Add authentication token management
  - Add error handling
  - _Requirements: 6.4_

- [ ] 22. Create job listing component
  - Create frontend/components/job_list.py
  - Display jobs in table/card format
  - Add search and filter functionality
  - Add pagination
  - _Requirements: 6.1, 6.2, 8.4_

- [ ] 23. Create job form component
  - Create frontend/components/job_form.py
  - Build form for adding new jobs
  - Build form for editing existing jobs
  - Add validation
  - _Requirements: 6.1, 6.2, 8.1_

- [ ] 24. Create application management component
  - Create frontend/components/application_manager.py
  - Display applications with status
  - Add status update functionality
  - Add notes and date tracking
  - _Requirements: 6.1, 6.2, 8.2_

- [ ] 25. Create analytics dashboard component
  - Create frontend/components/analytics_dashboard.py
  - Display application statistics
  - Show timeline visualization
  - Show status breakdown charts
  - _Requirements: 6.1, 6.2, 8.3_

- [ ] 26. Update main frontend app.py
  - Remove all contract analysis code
  - Create clean page navigation
  - Implement: Dashboard, Jobs, Applications, Analytics pages
  - Add authentication flow
  - Add error handling with user-friendly messages
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

---

## Phase 6: Database Migrations and Data

- [ ] 27. Create initial database migration
  - Create Alembic migration for users table
  - Create Alembic migration for jobs table
  - Create Alembic migration for applications table
  - Add indexes for performance
  - Test migration up and down
  - _Requirements: 10.4_

- [ ] 28. Create database initialization script
  - Create script to set up database
  - Add sample data for testing (optional)
  - Add database reset functionality
  - _Requirements: 10.1_

---

## Phase 7: Configuration and Environment

- [ ] 29. Create comprehensive .env.example file
  - Document all required environment variables
  - Provide sensible defaults
  - Add comments explaining each variable
  - _Requirements: 7.1, 7.2, 7.4_

- [ ] 30. Implement configuration validation
  - Add startup validation for required config
  - Provide clear error messages for missing config
  - Log configuration status on startup
  - _Requirements: 7.5, 10.1_

- [ ] 31. Update startup scripts
  - Update start.sh for simplified architecture
  - Create start_dev.sh for development
  - Create start_prod.sh for production
  - Test all startup scripts
  - _Requirements: 3.4, 10.1_

---

## Phase 8: Testing

- [ ] 32. Write unit tests for services
  - [ ]* 32.1 Create tests/unit/test_job_service.py
    - Test CRUD operations
    - Test search and filter
    - _Requirements: 8.1, 8.4_
  
  - [ ]* 32.2 Create tests/unit/test_application_service.py
    - Test CRUD operations
    - Test status updates
    - _Requirements: 8.2_
  
  - [ ]* 32.3 Create tests/unit/test_analytics_service.py
    - Test statistics calculation
    - Test timeline generation
    - _Requirements: 8.3_

- [ ] 33. Write integration tests for API endpoints
  - [ ]* 33.1 Create tests/integration/test_auth_api.py
    - Test registration and login flow
    - Test authentication errors
    - _Requirements: 5.5_
  
  - [ ]* 33.2 Create tests/integration/test_jobs_api.py
    - Test all job endpoints
    - Test authentication requirement
    - Test error handling
    - _Requirements: 5.1, 5.3, 8.1_
  
  - [ ]* 33.3 Create tests/integration/test_applications_api.py
    - Test all application endpoints
    - Test status updates
    - Test error handling
    - _Requirements: 5.1, 5.3, 8.2_

- [ ]* 34. Write end-to-end tests
  - Create tests/e2e/test_job_tracking_workflow.py
  - Test complete user journey: register → login → add job → apply → track
  - Test analytics generation
  - _Requirements: 8.1, 8.2, 8.3_

- [ ]* 35. Set up test configuration and fixtures
  - Create tests/conftest.py with test fixtures
  - Set up test database
  - Create test data factories
  - Configure pytest
  - _Requirements: 10.2_

---

## Phase 9: Documentation

- [ ] 36. Update README.md
  - Rewrite to focus on job tracking
  - Add clear project description
  - Update installation instructions
  - Add usage examples
  - Remove contract analysis references
  - _Requirements: 1.1, 1.3, 10.5_

- [ ]* 37. Create API documentation
  - Document all endpoints with examples
  - Add request/response schemas
  - Document authentication flow
  - Add error response examples
  - _Requirements: 5.1, 10.5_

- [ ]* 38. Create deployment documentation
  - Document environment setup
  - Add Docker deployment guide
  - Add cloud deployment guide
  - Document database setup
  - _Requirements: 10.5_

- [ ]* 39. Create developer documentation
  - Document project structure
  - Add contribution guidelines
  - Document testing approach
  - Add troubleshooting guide
  - _Requirements: 10.5_

---

## Phase 10: Final Cleanup and Validation

- [ ] 40. Remove all unused files and directories
  - Delete unused API route files
  - Delete unused middleware files
  - Delete unused service files
  - Delete unused configuration files
  - Clean up empty directories
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 41. Validate all imports and dependencies
  - Run application and verify no import errors
  - Check for unused dependencies in requirements.txt
  - Verify all tests pass
  - Check for any remaining contract analysis references
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 42. Performance and security audit
  - Test API response times
  - Verify authentication works correctly
  - Check for SQL injection vulnerabilities
  - Verify CORS configuration
  - Test error handling
  - _Requirements: 5.3, 5.5, 10.2_

- [ ] 43. Create deployment package
  - Build Docker images
  - Test Docker Compose setup
  - Create deployment checklist
  - Verify production configuration
  - _Requirements: 10.1, 10.2_

- [ ] 44. Final validation and handoff
  - Run full test suite
  - Verify all requirements met
  - Test complete user workflows
  - Update version numbers
  - Create release notes
  - _Requirements: All_

---

## Success Criteria

✅ Single main.py for backend, single app.py for frontend
✅ No import errors on startup
✅ All code focused on job tracking (no contract analysis)
✅ Minimal, necessary dependencies only
✅ Clear layered architecture
✅ All tests passing with >70% coverage
✅ Complete, accurate documentation
✅ Working deployment with clear instructions
✅ Clean, maintainable codebase