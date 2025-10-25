# Codebase Consolidation - Detailed TODO List

## Week 1: Foundation
*   **Core Configuration Consolidation** [backend] [config]
    *   Consolidate `config.py`, `config_loader.py`, `config_manager.py`, `config_validator.py`, `config_validation.py`, `config_init.py`, `config_integration.py`, `config_templates.py` into `config.py` (core configuration + loading + validation) and `config_advanced.py` (hot reload + templates + integrations).
    *   Update all import paths referencing the old configuration files.
    *   Run unit and integration tests for configuration management.
*   **Services Analytics Consolidation** [backend] [services]
    *   Consolidate `analytics.py`, `analytics_service.py`, `analytics_data_collection_service.py`, `advanced_user_analytics_service.py`, `application_analytics_service.py`, `email_analytics_service.py`, `job_analytics_service.py`, `slack_analytics_service.py` into `analytics_service.py` (core analytics + data collection) and `analytics_specialized.py` (domain-specific analytics).
    *   Update all import paths referencing the old analytics service files.
    *   Run unit and integration tests for analytics services.
*   **E2E Tests Cleanup** [test]
    *   Identify and remove all `demo_*.py` files from `tests/e2e/`.
    *   Consolidate remaining E2E test frameworks and simple/standalone tests where appropriate.
    *   Ensure existing E2E test coverage is maintained.

## Weeks 2-3: Core Services
*   **Services Job Management** [backend] [services]
    *   Consolidate `job_service.py`, `unified_job_service.py`, `job_scraper_service.py`, `job_scraper.py`, `job_ingestion_service.py`, `job_ingestion.py`, `job_api_service.py`, `job_matching_service.py`, `job_recommendation_feedback_service.py`, `job_source_manager.py`, `job_data_normalizer.py`, `job_description_parser_service.py` into `job_service.py` (core job management), `job_scraping_service.py` (scraping + ingestion), and `job_recommendation_service.py` (matching + recommendations).
    *   Update all import paths.
    *   Run unit and integration tests.
*   **Services Authentication** [backend] [services]
    *   Consolidate `auth_service.py`, `authentication_service.py`, `authorization_service.py`, `firebase_auth_service.py`, `oauth_service.py`, `jwt_token_manager.py` into `auth_service.py` (core auth + JWT) and `oauth_service.py` (OAuth + Firebase + external auth).
    *   Update all import paths.
    *   Run unit and integration tests.
*   **Core Database Management** [backend] [core] [database]
    *   Consolidate `database.py`, `database_init.py`, `database_simple.py`, `optimized_database.py`, `database_backup.py`, `database_migrations.py`, `database_optimization.py`, `database_performance.py` into `database.py` (core database + initialization) and `database_optimization.py` (performance + backup + migrations).
    *   Update all import paths.
    *   Run unit and integration tests.

## Weeks 4-5: Supporting Services
*   **Email Services Consolidation** [backend] [services]
    *   Consolidate `email_service.py`, `email_template_service.py`, `email_template_manager.py`, `email_analytics_service.py`, `email_notification_optimizer.py`, `gmail_service.py`, `smtp_service.py`, `sendgrid_service.py` into `email_service.py` (core email functionality) and `email_template_manager.py` (template management).
    *   Update all import paths.
    *   Run unit and integration tests.
*   **Cache Services Consolidation** [backend] [services]
    *   Consolidate `cache_service.py`, `intelligent_cache_service.py`, `cache_invalidation_service.py`, `cache_monitoring_service.py`, `session_cache_service.py`, `recommendation_cache_service.py` into `cache_service.py` (core caching) and `intelligent_cache_service.py` (advanced caching strategies).
    *   Update all import paths.
    *   Run unit and integration tests.
*   **LLM/AI Services Consolidation** [backend] [services]
    *   Consolidate `llm_manager.py`, `llm_service_plugin.py`, `llm_config_manager.py`, `llm_cache_manager.py`, `llm_benchmarking.py`, `llm_error_handler.py`, `ai_service_manager.py`, `unified_ai_service.py` into `llm_service.py` (core LLM/AI functionality) and `llm_config_manager.py` (configuration and benchmarking).
    *   Update all import paths.
    *   Run unit and integration tests.

## Weeks 6-7: Infrastructure
*   **Middleware Consolidation** [backend] [middleware]
    *   Consolidate `auth_middleware.py`, `jwt_auth_middleware.py`, `api_key_middleware.py`, `security_middleware.py`, `ai_security_middleware.py`, `error_handling.py`, `global_error_handler.py` into `auth_middleware.py`, `security_middleware.py`, `error_handling.py`, and 3 specialized middlewares.
    *   Update all import paths.
    *   Run unit and integration tests.
*   **Tasks Consolidation** [backend] [tasks]
    *   Consolidate `analytics_tasks.py`, `analytics_collection_tasks.py`, `scheduled_tasks.py`, `scheduler.py` and other task files into `analytics_tasks.py`, `scheduled_tasks.py`, and 4 specialized tasks.
    *   Update all import paths.
    *   Run unit and integration tests.
*   **Core Monitoring Consolidation** [backend] [core] [monitoring]
    *   Consolidate `monitoring.py`, `monitoring_backup.py`, `comprehensive_monitoring.py`, `production_monitoring.py`, `performance_metrics.py`, `performance_monitor.py`, `performance_optimizer.py` into `monitoring.py`, `performance_metrics.py`, and 2 specialized monitoring files.
    *   Update all import paths.
    *   Run unit and integration tests.

## Week 8: Cleanup and Documentation
*   **Configuration Files Cleanup** [config] [backend] [frontend]
    *   Consolidate `.env` files (e.g., `.env`, `.env.development`, `.env.production`, `.env.testing`, `.env.example`) into a single, well-managed `.env` file with clear environment-specific overrides.
    *   Streamline `config/` directory YAML files (`backend.yaml`, `frontend.yaml`, `deployment.yaml`, `base.yaml`) into a more unified structure.
    *   Consolidate monitoring configuration files.
*   **Email Templates Consolidation** [backend] [templates]
    *   Consolidate templates from `backend/app/email_templates/` and `backend/app/templates/email/` into a single, organized location (e.g., `backend/app/templates/email/`).
    *   Update all references to email templates.
*   **Documentation Updates** [docs]
    *   Update `README.md` to reflect the new architecture and consolidated file structure.
    *   Review and update any other relevant documentation (e.g., `DOCSTRING_GUIDE.md`, `guides/`) to align with the changes.
    *   Create a migration guide for developers detailing import path changes and new module structures.

## General Tasks (Ongoing throughout the project)
*   **Version Control:** Create a new feature branch for this consolidation effort. [devops]
*   **Backup:** Ensure regular backups are performed before and after major consolidation steps. [devops]
*   **Communication:** Maintain open communication channels with the development team regarding changes and progress. [management]
*   **Testing:** Continuously run unit, integration, and E2E tests to ensure no functionality is lost. [test]
*   **Import Mapping:** Develop and maintain an import compatibility layer if necessary to manage breaking changes. [backend]
*   **Code Review:** Conduct thorough code reviews for all consolidated modules. [devops]
