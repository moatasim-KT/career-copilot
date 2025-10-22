# Implementation Plan

## Overview

This implementation plan covers the complete Career Co-Pilot MVP across all four phases of the blueprint. Tasks are organized to build incrementally from core infrastructure through intelligent features and automation.

## Tasks

- [x] 1. Verify and enhance core database models

  - Review existing User, Job, and Application models against design specifications
  - Ensure all required fields are present
  - Verify JSON column types are properly configured
  - Add any missing indexes for performance optimization
  - _Requirements: 1.1, 2.1, 2.2, 8.1, 14.1, 14.5_

- [x] 2. Implement database migration for blueprint features

  - Create migration script to add new columns to existing tables if needed
  - Add skills, preferred_locations, experience_level to users table
  - Add tech_stack, responsibilities, source, date_applied to jobs table
  - Test migration on development database
  - Verify data integrity after migration
  - _Requirements: 1.1, 2.2, 14.1_

- [x] 3. Enhance authentication and user management
- [x] 3.1 Verify JWT token generation and validation

  - Review existing auth endpoints
  - Ensure password hashing uses bcrypt
  - Verify JWT token includes user_id and expiration
  - Test token validation middleware
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 3.2 Implement user profile endpoints

  - Create GET /api/v1/profile endpoint
  - Create PUT /api/v1/profile endpoint
  - Add Pydantic schemas for ProfileUpdate and ProfileResponse
  - Ensure proper authorization
  - _Requirements: 1.2, 1.3, 1.4, 1.5_

- [x] 4. Implement job management enhancements
- [x] 4.1 Enhance job creation endpoint

  - Update POST /api/v1/jobs to accept tech_stack, responsibilities, source fields
  - Add validation for required fields
  - Set default values
  - Test with various input combinations
  - _Requirements: 2.1, 2.2_

- [x] 4.2 Enhance job update endpoint

  - Update PUT /api/v1/jobs/{job_id} to handle all job fields
  - Update date_applied when status changes to applied
  - Ensure updated_at timestamp is automatically updated
  - Test authorization
  - _Requirements: 2.4, 8.4_

- [x] 4.3 Verify job listing and deletion endpoints

  - Test GET /api/v1/jobs with pagination
  - Test DELETE /api/v1/jobs/{job_id} with cascade
  - Verify proper error handling
  - _Requirements: 2.3, 2.5_

- [x] 5. Implement recommendation engine
- [x] 5.1 Create RecommendationEngine service class

  - Implement calculate_match_score method with weighted algorithm
  - Tech stack match 50 percent weight
  - Location match 30 percent weight
  - Experience level match 20 percent weight
  - Cap score at 100
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5.2 Create recommendations API endpoint

  - Implement GET /api/v1/recommendations endpoint
  - Query only jobs with status not_applied
  - Calculate match score for each job
  - Sort by score descending and return top N
  - Return job details with match_score
  - _Requirements: 3.5_

- [ ]\* 5.3 Write unit tests for recommendation engine

  - Test calculate_match_score with various skill combinations
  - Test with missing user skills or job tech_stack
  - Test location matching with different formats
  - Test experience level matching
  - Verify score capping at 100
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [-] 6. Implement skill gap analyzer
- [x] 6.1 Create SkillGapAnalyzer service class

  - Implement analyze_skill_gaps method
  - Aggregate all tech_stack arrays from user jobs
  - Count frequency of each skill using Counter
  - Identify skills not in user skills
  - Calculate skill coverage percentage
  - Generate top 5 learning recommendations
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 6.2 Create skill gap analysis API endpoint

  - Implement GET /api/v1/skill-gap endpoint
  - Call SkillGapAnalyzer analyze_skill_gaps
  - Return user_skills, missing_skills, top_market_skills, skill_coverage_percentage, recommendations
  - Handle edge cases
  - _Requirements: 4.5_

- [ ]\* 6.3 Write unit tests for skill gap analyzer

  - Test with various job and skill combinations
  - Test coverage calculation accuracy
  - Test recommendation generation
  - Test edge cases
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Implement application tracking
- [x] 7.1 Create application endpoints

  - Implement POST /api/v1/applications to create application
  - Implement GET /api/v1/applications to list user applications
  - Implement PUT /api/v1/applications/{id} to update status
  - Add Pydantic schemas
  - _Requirements: 8.1, 8.2, 8.5_

- [x] 7.2 Implement status validation and job updates

  - Validate status is one of allowed values
  - When application status changes to applied update job date_applied
  - When application status changes to applied update job status
  - Test status transitions
  - _Requirements: 8.3, 8.4_

- [x] 8. Implement analytics dashboard backend
- [x] 8.1 Create analytics service

  - Implement method to calculate total_jobs for user
  - Implement method to calculate total_applications for user
  - Count applications with status interview for interviews metric
  - Count applications with status offer or accepted for offers metric
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 8.2 Create analytics API endpoint

  - Implement GET /api/v1/analytics/summary endpoint
  - Return all calculated metrics in structured format
  - Add caching for performance
  - _Requirements: 9.1_

- [ ] 9. Implement job scraper service
- [x] 9.1 Create JobScraperService class

  - Implement scrape_jobs method with API integration placeholder
  - Add support for configurable job API
  - Implement deduplicate_jobs method using company title comparison
  - Make case-insensitive comparison for deduplication
  - _Requirements: 5.1, 5.2_

- [x] 9.2 Implement job ingestion logic

  - Create ingest_jobs function in scheduled_tasks
  - Query all users with skills and preferred_locations
  - For each user call scraper scrape_jobs with their preferences
  - Deduplicate against existing jobs
  - Create Job entities with source scraped
  - Log number of jobs added per user
  - _Requirements: 5.3, 5.4_

- [ ]\* 9.3 Write integration tests for job scraping

  - Test deduplication logic with various inputs
  - Test job creation from scraped data
  - Mock external API calls
  - _Requirements: 5.2, 5.3_

- [x] 10. Implement notification service
- [x] 10.1 Create NotificationService class

  - Implement send_morning_briefing method
  - Implement send_evening_summary method
  - Implement \_send_email helper with SMTP
  - Create HTML email templates for briefing and summary
  - Add graceful degradation when SMTP not configured
  - _Requirements: 6.3, 6.4, 7.3, 7.4_

- [x] 10.2 Implement morning briefing logic

  - Create send_morning_briefing function in scheduled_tasks
  - Query all users
  - For each user get top 5 recommendations
  - Format email with job details and match scores
  - Send email via NotificationService
  - Log success or failure
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 10.3 Implement evening summary logic

  - Create send_evening_summary function in scheduled_tasks
  - Query all users
  - Calculate daily statistics
  - Format email with statistics
  - Send email via NotificationService
  - Log success or failure
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 11. Implement task scheduler
- [x] 11.1 Set up APScheduler

  - Create scheduler module
  - Initialize APScheduler with BackgroundScheduler
  - Configure timezone and job stores
  - Add startup and shutdown handlers
  - _Requirements: 10.1_

- [x] 11.2 Register scheduled tasks

  - Register ingest_jobs task with cron trigger 0 4 \* \* \*
  - Register send_morning_briefing task with cron trigger 0 8 \* \* \*
  - Register send_evening_summary task with cron trigger 0 20 \* \* \*
  - Add ENABLE_SCHEDULER configuration check
  - Test scheduler starts with application
  - _Requirements: 10.2, 10.3, 10.4, 10.5_

- [ ]\* 11.3 Write tests for scheduled tasks

  - Mock time to test task execution
  - Test each task function independently
  - Verify database operations
  - Test error handling in tasks
  - _Requirements: 10.2, 10.3, 10.4_

- [x] 12. Enhance frontend dashboard
- [x] 12.1 Implement profile management UI

  - Create profile page in Streamlit
  - Add multi-select for skills
  - Add multi-select for preferred locations
  - Add dropdown for experience level
  - Implement save functionality calling PUT /api/v1/profile
  - _Requirements: 12.3, 1.3, 1.4_

- [x] 12.2 Implement recommendations UI

  - Add recommendations section to dashboard
  - Call GET /api/v1/recommendations
  - Display jobs with match scores
  - Show tech stack location and other details
  - Add Apply button to create application
  - _Requirements: 12.3, 3.5_

- [x] 12.3 Implement skill gap analysis UI

  - Create skill gap page in Streamlit
  - Call GET /api/v1/skill-gap
  - Display user skills vs missing skills
  - Show skill coverage percentage with gauge chart
  - Display learning recommendations
  - _Requirements: 12.3, 4.5_

- [x] 12.4 Enhance analytics dashboard UI

  - Update dashboard to call GET /api/v1/analytics/summary
  - Display metrics in cards
  - Add status breakdown pie chart
  - Show recent activity
  - _Requirements: 9.4, 9.5, 12.3_

- [x] 12.5 Enhance job management UI

  - Update job form to include tech_stack field
  - Add responsibilities field
  - Display source badge
  - Show match score if available
  - _Requirements: 12.4, 2.1, 2.2_

- [x] 13. Implement configuration management
- [x] 13.1 Create environment configuration

  - Define all required environment variables in env example
  - Add DATABASE_URL JWT_SECRET_KEY JWT_ALGORITHM JWT_EXPIRATION_HOURS
  - Add ENABLE_SCHEDULER ENABLE_JOB_SCRAPING JOB_API_KEY
  - Add SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD
  - Document each variable with comments
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 13.2 Implement configuration loading

  - Create config module to load environment variables
  - Add validation for required variables
  - Set sensible defaults for optional variables
  - Add configuration summary logging on startup
  - _Requirements: 13.5_

- [x] 14. Implement error handling and logging
- [x] 14.1 Set up structured logging

  - Configure logging with appropriate levels
  - Add request response logging middleware
  - Log all scheduled task executions
  - Add error logging with stack traces
  - _Requirements: 15.2, 15.3_

- [x] 14.2 Implement error handlers

  - Create FastAPI exception handlers for common errors
  - Return structured error responses with detail error_code timestamp
  - Handle validation errors 400
  - Handle authentication errors 401
  - Handle not found errors 404
  - Handle server errors 500
  - _Requirements: 15.1_

- [x] 14.3 Add graceful degradation

  - Handle SMTP failures without crashing
  - Handle job API failures without crashing
  - Log failures and continue operation
  - _Requirements: 15.4_

- [x] 15. Implement health check endpoint

  - Create GET /api/v1/health endpoint
  - Check database connectivity
  - Check scheduler status
  - Return status and component health
  - _Requirements: 15.5_

- [x] 16. Create database initialization scripts
- [x] 16.1 Create init_database script

  - Initialize all tables using SQLAlchemy models
  - Add indexes
  - Verify foreign key constraints
  - _Requirements: 14.1, 14.5_

- [x] 16.2 Create seed_data script

  - Create test user with sample profile
  - Create sample jobs with tech_stack
  - Create sample applications
  - Useful for development and testing
  - _Requirements: 14.2_

- [ ] 17. Integration and end-to-end testing
- [ ]\* 17.1 Write API integration tests

  - Test complete user registration and login flow
  - Test job creation and recommendation flow
  - Test profile update and skill gap analysis flow
  - Test application creation and tracking flow
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]\* 17.2 Write end-to-end workflow tests

  - Test Register Add jobs Update profile Get recommendations Apply
  - Test Add jobs Analyze skill gaps Update skills Verify coverage change
  - Test Create applications View analytics Verify metrics
  - _Requirements: All requirements_

- [ ] 18. Documentation and deployment preparation
- [ ] 18.1 Update README with new features

  - Document all new API endpoints
  - Add configuration instructions
  - Add usage examples for recommendations and skill gap
  - Update architecture diagram
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [ ] 18.2 Create deployment guide

  - Document production environment setup
  - Add PostgreSQL migration instructions
  - Add SMTP configuration examples
  - Add security checklist
  - _Requirements: 13.5_

- [ ] 18.3 Create startup scripts

  - Create start script for production
  - Create start_dev script for development with test data
  - Add validation script to check configuration
  - _Requirements: 13.1, 13.5_

- [ ] 19. Performance optimization
- [ ] 19.1 Add database indexes

  - Verify indexes on users username email
  - Verify indexes on jobs user_id company title created_at
  - Verify indexes on applications user_id job_id status
  - Test query performance with EXPLAIN
  - _Requirements: 14.4_

- [ ] 19.2 Implement caching for recommendations

  - Add simple in-memory cache for recommendations 1 hour TTL
  - Invalidate cache when user profile changes
  - Invalidate cache when new jobs are added
  - _Requirements: 3.5_

- [ ] 20. Final validation and testing
- [ ] 20.1 Run complete system validation

  - Start backend and frontend
  - Test all user workflows manually
  - Verify scheduled tasks execute
  - Check email notifications if SMTP configured
  - Review logs for errors
  - _Requirements: All requirements_

- [ ] 20.2 Performance testing

  - Test API response times with realistic data volumes
  - Test recommendation generation with 100 plus jobs
  - Test skill gap analysis with 500 plus jobs
  - Verify database query performance
  - _Requirements: 14.4_

- [ ] 20.3 Security review
  - Verify password hashing is working
  - Test JWT token expiration
  - Test authorization users cannot access other users data
  - Review environment variable handling
  - Check for SQL injection vulnerabilities
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
